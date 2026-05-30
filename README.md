# Smart video doorbell for Apple Home

In this repository you will find a firmware for a smart video doorbell for Apple Home. Should you have any questions please do not hesitate to contact me at gully.horror0w@icloud.com.  
 
**Required components**

- RF doorbell - 1 pcs.
- ESP32C3FN4 Super Mini - 1 pcs.
- 5V 1A power supply - 1 pcs.

**Required Arduino libraries**

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

## HomeBridge setup

In this chapter you will find a detailed instructions on how to setup your HomeBridge to work with this device.  

### Setting up the MQTT broker

Connect to your HomeBridge device using SSH and execute the following commands:  

`sudo apt-get update`  
`sudo apt-get upgrade`  
`sudo apt-get install mosquitto mosquitto-clients`  
`sudo systemctl enable mosquitto`  
`sudo nano /etc/mosquitto/mosquitto.conf`

The last command opens the MQTT broker configuration file. Remove (delete) all the lines from the file and insert the following line instead:  

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

Create new MQTT broker user. To do that execute the following command:  

`sudo mosquitto_passwd -c /etc/mosquitto/passwd mqtt_user_name`

Provide a user name you would like instead of **mqtt_user_name** (for example: mqttuser). When requested provide a new user's password.  

Start MQTT broker by executing the following command:  

`sudo systemctl restart mosquitto`

### Setting up the HomeBridge

Connect to your HomeBridge by Web interface. Select "Edit JSON". 

In the **CameraUI** section update the MQTT settings as below:

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

Replace **mqtt_user_name** and **mqtt_password** with just created user name and password.  

Scroll down to the **Cameras** and find the **mqtt** section. Change it as shown below. If there is no such section then add it right after **videoanalysis**.  

```
"mqtt": {
      "doorbellTopic": "doorcam/bell",
      "doorbellMessage": "RING",
},
```

Now add the following line right before **videoConfig**:

`"doorbell": true,`

**Do not forget to provide correct MQTT broker user name and password in the firmware**.

DONE.
## Support the author

If you like what I am doing you can support me using one of the link below:

**BuyMeACoffee**: https://buymeacoffee.com/dronetales  
**Boosty**: https://boosty.to/drone_tales/donate  
  
**BTC**: bitcoin:1A1WM3CJzdyEB1P9SzTbkzx38duJD6kau  
**BCH**: bitcoincash:qre7s8cnkwx24xpzvvfmqzx6ex0ysmq5vuah42q6yz  
**ETH**: 0xf780b3B7DbE2FC74b5F156cBBE51F67eDeAd8F9a  



