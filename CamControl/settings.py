# =============================================================================
# settings.py – Central configuration for the DroneTales Camera Control service
# =============================================================================
# This file holds all configurable constants and the list of camera devices.
# The application reads these values at startup and uses them to establish
# TCP connections, detect motion events, and communicate via MQTT.
# =============================================================================


# =============================================================================
# Camera Communication Constants
# =============================================================================
# These constants define how the application talks to the IP cameras over TCP.

# Default TCP port used by all cameras.
# Each camera in the DEVICES list can override this with its own "port" field.
DEVICE_PORT = 3201

# The exact string that the camera sends to indicate a motion detection  event.
# The application scans every complete line (terminated by 0x0A) for this text.
EVENT_MOTION_DETECT = "EVENT: MOTION detect."
# The exact string that the camera sends to indicate a sound detection  event.
# The application scans every complete line (terminated by 0x0A) for this text.
EVENT_SOUND_DETECT = "EVENT: SOUND detect."

# =============================================================================
# MQTT Broker Configuration
# =============================================================================
# These constants configure the connection to the MQTT broker (Mosquitto, etc.).
# The MQTT client uses them when establishing and authenticating the connection.

# TCP port on which the MQTT broker is listening (default 1883 for unencrypted MQTT).
MQTT_PORT = 1883
# Hostname or IP address of the MQTT broker.
MQTT_SERVER = "mqtt_server_ip"
# Username for MQTT broker authentication (if required).
MQTT_USER_NAME = "mqtt_user_name"
# Password for MQTT broker authentication.
MQTT_PASSWORD = "mqtt_password"

# Unique client identifier sent to the broker.
# It should be unique on the network to avoid session conflicts.
MQTT_CLIENT_ID = "DroneTales Camera Control"


# =============================================================================
# MQTT Message Payloads
# =============================================================================
# These constants define the text payloads sent to the MQTT topics when
# motion is first detected and when the reset timer expires.

# Payload sent when a motion event is detected (motion ON).
MQTT_MOTION_ON_MESSAGE = "ON"

# Payload sent after the motion reset timeout has elapsed without a new event (motion OFF).
MQTT_MOTION_OFF_MESSAGE = "OFF"


# =============================================================================
# Device Connection Management
# =============================================================================
# Constants controlling how the application reconnects to cameras that have
# dropped their TCP connection or were never reachable at startup.

# Time in milliseconds that the application waits after a connection failure
# before attempting to reconnect to a camera.
RECONNECT_TIMEOUT = 5000   # 5 seconds


# =============================================================================
# Device List
# =============================================================================
# Each entry represents one IP camera that must be monitored.
# The application starts a dedicated thread for every device in this list.
#
# Device dictionary fields:
#   - "ip":             IP address of the camera (string, required)
#   - "port":           TCP port to connect to (int, optional; defaults to DEVICE_PORT)
#   - "mqtt_topic":     MQTT topic to publish ON/OFF messages to (string, required)
#   - "reset_timeout_ms": Time in milliseconds after the last motion event before
#                         an OFF message is sent (int, required)
#
# The application automatically reconnects to these devices using the
# RECONNECT_TIMEOUT interval if a connection is lost.
DEVICES = [
    {
        "ip": "192.168.1.100",
        "port": 3201,
        "mqtt_topic": "indoorcam/motion",
        "reset_timeout_ms": 20000,      # 20 seconds
        "max_reset_timeout_ms": 150000  # 150 seconds
    },
    {
        "ip": "192.168.1.101",
        "port": 3201,
        "mqtt_topic": "doorcam/motion",
        "reset_timeout_ms": 30000,      # 30 seconds
        "max_reset_timeout_ms": 150000  # 150 seconds
    }
]
