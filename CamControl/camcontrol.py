# =============================================================================
# camcontrol.py – Main application for DroneTales Camera Control service
# =============================================================================
# This module handles all TCP/IP communication with IP cameras using asyncio
# for truly event‑driven, non‑blocking I/O. It detects motion and sound events
# (exact string match) and coordinates MQTT ON/OFF messages via the mqtt.py
# module.
#
# Each camera is managed by a separate asyncio task. The connection stays open
# indefinitely; if it drops, the task reconnects after RECONNECT_TIMEOUT.
#
# State machine:
#   - Idle: no timers running, ON has not been sent.
#   - Active: ON has been sent, two timers run simultaneously:
#       1) Reset timer – restarted on every new event; when it expires, OFF is
#          sent and state returns to Idle.
#       2) Guard timer – started once when ON is first sent, never restarted.
#          If it expires, OFF is forced and state returns to Idle, regardless
#          of recent events.
# =============================================================================

import asyncio

import settings

from mqtt import connect_mqtt, publish_message, stop_mqtt


class CameraHandler:
    """
    Manages a single camera connection using asyncio.

    State machine:
      - Idle:     no timers running, ON has not been sent (or was followed by OFF).
      - Active:   ON has been sent, reset timer and guard timer are both running.
                  New events restart only the reset timer.
                  Expiry of either timer triggers OFF and a return to Idle.
    """

    def __init__(self, device_cfg):
        self.ip = device_cfg["ip"]
        self.port = device_cfg.get("port", settings.DEVICE_PORT)
        self.mqtt_topic = device_cfg["mqtt_topic"]
        self.reset_timeout_s = device_cfg["reset_timeout_ms"] / 1000.0
        self.max_reset_timeout_s = device_cfg["max_reset_timeout_ms"] / 1000.0

        # State
        self.motion_msg_sent = False          # True if ON was sent and timers are active
        self.reset_timer_task: asyncio.Task = None   # Task for the reset timer
        self.guard_timer_task: asyncio.Task = None   # Task for the guard timer


    # -------------------------------------------------------------------------
    # Timer management
    # -------------------------------------------------------------------------

    async def _start_reset_timer(self):
        """Cancel the existing reset timer (if any) and start a new one."""

        if self.reset_timer_task is not None:
            self.reset_timer_task.cancel()
        self.reset_timer_task = asyncio.create_task(self._reset_timer_expired())


    async def _reset_timer_expired(self):
        """
        Wait for the reset timeout, then send OFF and return to idle.

        This coroutine is cancelled when a new event arrives (timer restart),
        when the guard timer forces OFF, or when the connection is lost.
        """

        try:
            await asyncio.sleep(self.reset_timeout_s)
            if self.motion_msg_sent:
                await self._force_off()
        except asyncio.CancelledError:
            pass


    async def _start_guard_timer(self):
        """
        Start the guard timer that runs independently of event resets.

        The guard timer is created only once per active period and is never
        restarted. When it expires, OFF is forced.
        """

        if self.guard_timer_task is not None:
            self.guard_timer_task.cancel()
        self.guard_timer_task = asyncio.create_task(self._guard_timer_expired())


    async def _guard_timer_expired(self):
        """
        Wait for the maximum active duration, then force OFF.

        Unlike the reset timer, this is not cancelled by new events.
        It ensures the active period never exceeds max_reset_timeout_ms.
        """

        try:
            await asyncio.sleep(self.max_reset_timeout_s)
            if self.motion_msg_sent:
                await self._force_off()
        except asyncio.CancelledError:
            pass


    # -------------------------------------------------------------------------
    # Common OFF routine
    # -------------------------------------------------------------------------

    async def _force_off(self):
        """
        Send OFF, cancel both timers, and return to Idle.
        """

        publish_message(self.mqtt_topic, settings.MQTT_MOTION_OFF_MESSAGE)
        self.motion_msg_sent = False

        # Cancel both timers
        if self.reset_timer_task is not None:
            self.reset_timer_task.cancel()
            self.reset_timer_task = None
        
        if self.guard_timer_task is not None:
            self.guard_timer_task.cancel()
            self.guard_timer_task = None


    # -------------------------------------------------------------------------
    # Event handling
    # -------------------------------------------------------------------------

    async def _handle_event(self):
        """
        Process a detected motion or sound event.

        - If Idle: send ON, then start both timers.
        - If Active: restart the reset timer only; the guard timer continues.
        """

        if not self.motion_msg_sent:
            # Idle → try to become Active
            if publish_message(self.mqtt_topic, settings.MQTT_MOTION_ON_MESSAGE):
                self.motion_msg_sent = True
                await self._start_reset_timer()
                await self._start_guard_timer()
        else:
            # Active → only reset the main timer (guard keeps running)
            await self._start_reset_timer()


    # -------------------------------------------------------------------------
    # Connection cleanup
    # -------------------------------------------------------------------------

    async def _disconnect_cleanup(self):
        """
        Called when the TCP connection is lost.

        If ON was sent, send OFF immediately and cancel both timers.
        """

        if self.motion_msg_sent:
            await self._force_off()
        else:
            # Ensure timers are cleaned up even if not active
            if self.reset_timer_task is not None:
                self.reset_timer_task.cancel()
                self.reset_timer_task = None

            if self.guard_timer_task is not None:
                self.guard_timer_task.cancel()
                self.guard_timer_task = None


    # -------------------------------------------------------------------------
    # Persistent connection loop
    # -------------------------------------------------------------------------

    async def run(self):
        """
        Main loop for a single camera.

        Connects, reads lines indefinitely (no timeout), and reconnects
        after any failure.
        """

        reconnect_delay = settings.RECONNECT_TIMEOUT / 1000.0

        while True:
            try:
                reader, writer = await asyncio.open_connection(self.ip, self.port)

                # Read lines forever – asyncio.readline() blocks until a
                # newline arrives or the connection drops.
                while True:
                    try:
                        line_bytes = await reader.readline()
                    except Exception:
                        break

                    if not line_bytes:
                        break

                    # Decode the line (strip CR, LF)
                    line = line_bytes.decode(errors='replace').rstrip('\n\r')

                    # Only react to exact event strings
                    if line == settings.EVENT_MOTION_DETECT or line == settings.EVENT_SOUND_DETECT:
                        await self._handle_event()

                # Inner loop exited – connection lost
                await self._disconnect_cleanup()
                writer.close()
                await writer.wait_closed()

            except (OSError, asyncio.TimeoutError):
                await self._disconnect_cleanup()

            # Wait before trying again
            await asyncio.sleep(reconnect_delay)


# =============================================================================
# Application entry points
# =============================================================================

async def main_async():
    """
    Start MQTT, create and run camera tasks.
    """

    connect_mqtt()

    tasks = []
    for dev_cfg in settings.DEVICES:
        handler = CameraHandler(dev_cfg)
        tasks.append(asyncio.create_task(handler.run()))

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass

    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    stop_mqtt()


def main():
    """Synchronous wrapper to start the asyncio event loop."""
    
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
