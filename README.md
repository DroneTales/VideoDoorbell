# Video Doorbell for Apple Home

Here you will find the firmware for a smart video doorbell compatible with Apple Home. If you have any questions, you can ask them in my [Telegram channel](t.me/drone_tales).

**Components used**

- Wireless doorbell - 1 pc.
- ESP32C3FN4 Super Mini - 1 pc.
- 5V 1A power supply - 1 pc.

**Arduino libraries used**

- esp32 by Espressif Systems (board)
- HomeSpan
- PubSubClient

**Arduino IDE settings**

- Board: ESP32C3 Dev BModule
- ESP CDC On Boot: Enabled
- CPU Frequency: 80MHz (WiFi)
- Core Debug Level: None
- Erase All Flash Before Sketch Upload: Disabled
- Flash frequency: 80Mhz
- Flash Mode: QIO
- Flash Size: 4MB (32Mb)
- JTAG Adapter: Disabled
- Partition Scheme: Huge APP (3MB No OTA/1MB SPIFFS)
- Upload Speed: 921600
- Zigbee Mode: Disabled
- Programmer: Esptool

## Configuring HomeBridge

In this part you will find detailed instructions for configuring HomeBridge to work with this device.

### Configuring the MQTT broker

Connect to your HomeBridge via SSH and run the following commands:

`sudo apt-get update`  
`sudo apt-get upgrade`  
`sudo apt-get install mosquitto mosquitto-clients`  
`sudo systemctl enable mosquitto`  
`sudo nano /etc/mosquitto/mosquitto.conf`

The last command will open the MQTT broker configuration file. Completely delete all contents of this file and insert the following lines:

```
per_listener_settings true

pid_file /run/mosquitto/mosquitto.pid

persistence true
persistence_location /var/lib/mosquitto/

log_dest file /var/log/mosquitto/mosquitto.log

include_dir /etc/mosquitto/conf.d

listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```

Now you need to create a new user for the MQTT broker. To do this, run the following command:

`sudo mosquitto_passwd -c /etc/mosquitto/passwd mqtt_user_name`

Instead of *mqtt_user_name*, specify a new username (for example: mqttuser). Enter a new password for the newly created user when prompted.

Restart the MQTT broker with the following command:

`sudo systemctl restart mosquitto`

### Configuring HomeBridge

Connect to your HomeBridge via the web interface. Select *Edit JSON*.

In the *CameraUI* section, update the MQTT settings as shown below:

```
"mqtt": {
    "active": true,
    "tls": false,
    "host": "127.0.0.1",
    "port": 1883,
    "username": "mqtt_user_name",
    "password": "mqtt_password"
},
```

Replace *mqtt_user_name* and *mqtt_password* with the username and password of the user you just created.

Scroll down to the *Camera* section and find the *mqtt* section. Modify it as shown below. If there is no such section, add it immediately after the *videoanalysis* section.

```
"mqtt": {
      "doorbellTopic": "doorcam/bell",
      "doorbellMessage": "RING",
},
```

Now add the following line immediately after the *videoConfig* line:

`"doorbell": true,`

**Do not forget to specify the MQTT username and password created earlier in the firmware.**

DONE.
