# =============================================================================
# mqtt.py – MQTT communication layer for the DroneTales Camera Control service
# =============================================================================
# This module handles all MQTT interactions:
#   - Connection to the broker
#   - Automatic reconnection
#   - Publishing ON/OFF messages to camera motion topics
# It uses the paho‑mqtt library and reads broker configuration from settings.py.
# =============================================================================

import paho.mqtt.client as mqtt

# Import all configuration constants defined in settings.py.
import settings


# =============================================================================
# MQTT Client Instance
# =============================================================================
# A single paho MQTT client instance is created and configured with the broker
# credentials and automatic reconnection parameters.
# =============================================================================

# Create the MQTT client using the unique identifier from settings.py.
mqttClient = mqtt.Client(client_id = settings.MQTT_CLIENT_ID)

# Set username and password for broker authentication (if required).
mqttClient.username_pw_set(settings.MQTT_USER_NAME, settings.MQTT_PASSWORD)

# Enable automatic reconnection when the connection is lost.
# The client will wait between 1 and 30 seconds before retrying.
mqttClient.reconnect_delay_set(min_delay = 1, max_delay = 30)


# =============================================================================
# Public MQTT Interface
# =============================================================================
# The following functions are used by the main application to manage the
# MQTT connection and publish messages.
# =============================================================================

def connect_mqtt():
    """
    Establish a connection to the MQTT broker and start the background network loop.

    This function connects to the broker using the server, port, and keepalive
    interval defined in settings.py. After a successful connection, the loop_start()
    method runs a background thread that handles automatic reconnection and keeps
    the connection alive.

    If the initial connection attempt fails, the background thread will retry
    automatically if the broker becomes reachable later.
    """

    try:
        mqttClient.connect(settings.MQTT_SERVER, settings.MQTT_PORT, keepalive = 60)
        mqttClient.loop_start()
    except Exception:
        pass


def publish_message(topic, payload):
    """
    Publish a message to a given MQTT topic, but only if the client is connected.

    The message is sent with QoS 0 – delivery is not guaranteed, and no queueing
    is performed. If the broker is unreachable or the connection has been lost,
    the message is simply dropped and the function returns False.

    Args:
        topic (str):   The MQTT topic to publish to.
        payload (str): The message text to send.

    Returns:
        bool: True if the message was published, False otherwise.
    """

    if not mqttClient.is_connected():
        return False

    # QoS 0 → message is not queued, sent immediately or lost
    mqttClient.publish(topic, payload, qos=0)
    return True


def stop_mqtt():
    """
    Gracefully stop the MQTT client.

    This terminates the background network thread and disconnects from the broker.
    It should be called during a clean application shutdown (e.g., on KeyboardInterrupt).
    """
    
    mqttClient.loop_stop()
    mqttClient.disconnect()
