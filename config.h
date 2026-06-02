#pragma once


/**************************************************************************************/
/*                                   MQTT constants                                   */

// MQTT server port.
constexpr uint16_t MQTT_PORT = 1883;
// MQTT server address.
const char* const MQTT_SERVER = "mqtt_server_ip";
// MQTT server user name.
const char* const MQTT_USER_NAME = "mqtt_user_name";
// MQTT server password.
const char* const MQTT_PASSWORD = "mqtt_password";

// MQTT client ID.
const char* const MQTT_DOORBELL_CLIENT_ID = "DroneTales Doorbell";

// Camera UI MQTT doorbell topic.
const char* const MQTT_DOORBELL_TOPIC = "doorcam/bell";
// Camera UI MQTT doorbell ring message.
const char* const MQTT_DOORBELL_MESSAGE = "RING";

/**************************************************************************************/
