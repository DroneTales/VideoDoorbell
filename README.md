# Видео дверной звонок для Apple Home

Здесь вы найдете прошивку для умного дверного видео звонка, совместимого с Apple Home. Если у вас возникнут какие либо вопросы, вы можете задать их в моем [телеграм канале](t.me/drone_tales).  
 
**Используемые компоненты**

- Беспроводно звонок - 1 шт.
- ESP32C3FN4 Super Mini - 1 шт.
- Блок питания на 5V 1A - 1 шт.

**Использумые библиотеки Arduino**

- esp32 by Espressif Systems (board)
- HomeSpan
- PubSubClient
 
**Настройки Arduino IDE**

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

## Найстройка HomeBridge

В этой части вы найдете детальные инструкции по настройке HomeBridge для работы с этим устройством.  

### Настройка MQTT брокера

Подключитесь к своему HomeBridge по SSH и выполните следующие команды:  

`sudo apt-get update`  
`sudo apt-get upgrade`  
`sudo apt-get install mosquitto mosquitto-clients`  
`sudo systemctl enable mosquitto`  
`sudo nano /etc/mosquitto/mosquitto.conf`

Последняя команда откроет файл конфигурации MQTT брокера. Полность/ удалите все содержимое этого файла и вставьте следующие строки:  

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

Тепепь необходимо сохдать нового пользователя для MQTT брокера. Для этого выполните следующую команду:  

`sudo mosquitto_passwd -c /etc/mosquitto/passwd mqtt_user_name`

Вместо *mqtt_user_name* укажите новое имя пользователя (на пример: mqttuser). Введите новый пароль для только что созданного пользователя, когда появится соответствующий запрос.  

Запустите MQTT брокер следующей командой:  

`sudo systemctl restart mosquitto`

### Настройка HomeBridge

Подключитесь к своему HomeBridge через web интерфейс. Выберите *Edit JSON*.  

В разделе *CameraUI*, обновите настройки MQTT как показано ниже:  

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

Замените *mqtt_user_name* и *mqtt_password* на имя и пароль только что созданного пользователя.  

Пролистайте до раздела *Camera* и найдите раздел *mqtt*. Измините его как показано ниже. Если такого раздела нет? то добавьте его сразу за разделом *videoanalysis*.  

```
"mqtt": {
      "doorbellTopic": "doorcam/bell",
      "doorbellMessage": "RING",
},
```

Теперь добавьте следующую строку сразу после строки *videoConfig*:  

`"doorbell": true,`

**Не забудьте указать имя и пароль MQTT пользователя, созданного ранее, в прошивке.**.  

ГОТОВО.  
