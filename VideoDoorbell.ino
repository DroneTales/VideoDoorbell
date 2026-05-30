// ESP32C3FN4 SuperMini Board
// =====================================================================================
// Arduino IDE settings:
//   - Board: ESP32C3 Dev Module
//   - ESP CDC On Boot: Enabled
//   - CPU Frequency: 80MHz (WiFi)
//   - Core Debug Level: None
//   - Erase All Flash Before Sketch Upload: Disabled
//   - Flash frequency: 80Mhz
//   - Flash Mode: QIO
//   - Flash Size: 4MB (32Mb)
//   - JTAG Adapter: Disabled
//   - Partition Scheme: Huge APP (3MB No OTA/1MB SPIFFS)
//   - Upload Speed: 921600
//   - Zigbee Mode: Disabled
//   - Programmer: Esptool
// =====================================================================================

#include <HomeSpan.h>
#include <PubSubClient.h>
#include <WiFi.h>


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


/**************************************************************************************/
/*                            Doorbell hardware  constants                            */

// The doorbell button signal duration in milliseconds.
constexpr uint32_t BELL_BUTTON_SIGNAL_DURATION = 500;
// The doorbell play signal duration in milliseconds.
constexpr uint32_t BELL_SIGNAL_DURATION = 250;

/**************************************************************************************/


/**************************************************************************************/
/*                                  Pins  definition                                  */

// HomeSpan status LED pin.
#define STATUS_LED_PIN      GPIO_NUM_8
// HomeSpan control button pin.
#define CONTROL_PIN         GPIO_NUM_9

// The doorbell button input pin (radio signal)
#define BELL_BUTTON_PIN     GPIO_NUM_3
// The doorbell signal pin (wired to the sound chip)
#define BELL_SIGNAL_PIN     GPIO_NUM_10

/**************************************************************************************/


/**************************************************************************************/
/*                                  Global variables                                  */

// The doorbell sound enabling flag. True if the doorbell sound is enabled. False if
// the doorbell sound is disabled.
bool SoundEnabled = true;

// The doorbell signal processing task handle.
TaskHandle_t DoorbellSignalTaskHandle = nullptr;

// The WiFi client instalce.
WiFiClient NetClient;

/**************************************************************************************/


/**************************************************************************************/
/*                             Virtual  Doorbell switches                             */

// Virtual doorbell switch used to control doorbell sound.
struct DoorbellSwitch : Service::Switch
{
    SpanCharacteristic* Switch;
    
    DoorbellSwitch() : Service::Switch()
    {
        // Default is false (bell is turned off) and we store current value in NVS.
        Switch = new Characteristic::On(false, true);
        // Get current states.
        SoundEnabled = Switch->getVal();
    }
    
    bool update()
    {
        // Get the current switch state and store it in the global flag.
        SoundEnabled = Switch->getNewVal();
        return true;
    }
};

/**************************************************************************************/


/**************************************************************************************/
/*                                 Doorbell functions                                 */

// Doorbell signal interrupt handler.
void IRAM_ATTR RingInterrupt()
{
    // The previous level state. True if the previous level was HIGH. False - if LOW.
    static bool WasHigh = false;
    // Last time when level changed from LOW to HIGH.
    static uint32_t LastMillis = 0;

    // Read the ring signal pin.
    bool NowHigh = (digitalRead(BELL_BUTTON_PIN) == HIGH);

    // If the current level is HIGH and the previous was LOW
    // (the level changed from LOW to HIGH)...
    if (NowHigh && !WasHigh)
    {
        // Set previous state to the current one (HIGH).
        WasHigh = true;
        // Remember time when level changed to high.
        LastMillis = millis();
        // Exit from ISR as we need to wait when it downs from HIGH to LOW.
        return;
    }

    // If the previous level was HIGH and the current is LOW
    // (the level changed from HIGH to LOW)...
    if (WasHigh && !NowHigh)
    {
        // Reset the previous state to the current one (LOW).
        WasHigh = false;
        // Now calculate the pulse duration and if it looks like bell signal
        // duration set the ringing flag.
        uint32_t CurrentMillis = millis(); // We need this to be able to use unsigned values.
        // If pulse duration is correct then notify (resume) ring processing task.
        if ((CurrentMillis - LastMillis) >= BELL_BUTTON_SIGNAL_DURATION)
            // It is guaranteed that the task handle is valid because we attached interrupts
            // after task created and started.
            xTaskNotify(DoorbellSignalTaskHandle, 0, eNoAction);
    }
}

// Doorbell signal processing task function.
void DoorbellSignalTask(void* pvParameters)
{
    // Configure MQTT client.
    PubSubClient MqttClient(NetClient);
    MqttClient.setServer(MQTT_SERVER, MQTT_PORT);

    while (true)
    {
        // Wait for doorbell signal notification.
        xTaskNotifyWait(0, 0, nullptr, portMAX_DELAY);

        // Ring detected. Try to send MQTT message to notify HomeSpan about ring.
        // Make sure we are connected to Wi-Fi network.
        if (WiFi.status() != WL_CONNECTED)
        {
            // Connect to MQTT broker.
            if (MqttClient.connect(MQTT_DOORBELL_CLIENT_ID, MQTT_USER_NAME, MQTT_PASSWORD))
            {
                // Check the MQTT connection status as it may not connect by any reason.
                if (MqttClient.connected())
                {
                    // Now we can send a MQTT message about doorbell ring.
                    MqttClient.publish(MQTT_DOORBELL_TOPIC, MQTT_DOORBELL_MESSAGE);
                    // And disconnect from MQTT broker as we do not need to keep
                    // connection active for so long time (I am sure, no one rings the
                    // bell every single minute).
                    MqttClient.disconnect();
                }
            }
        }

        // Once notification send and the doorbell sound is enabled we can
        // play the doorbell sound.
        if (SoundEnabled)
        {
            digitalWrite(BELL_SIGNAL_PIN, HIGH);
            delay(BELL_SIGNAL_DURATION);
            digitalWrite(BELL_SIGNAL_PIN, LOW);
        }
    }
}

/**************************************************************************************/


/**************************************************************************************/
/*                                 Arduino  functions                                 */

// Arduino initialization routine.
void setup()
{
    // Initialize debug UART.
    Serial.begin(115200);

    // Initialize pins door bell pins.
    pinMode(BELL_SIGNAL_PIN, OUTPUT);
    pinMode(BELL_BUTTON_PIN, INPUT_PULLDOWN);
    digitalWrite(BELL_SIGNAL_PIN, LOW);

    // Initialize HomeSpan pins
    pinMode(CONTROL_PIN, INPUT);
    pinMode(STATUS_LED_PIN, OUTPUT);
    digitalWrite(STATUS_LED_PIN, HIGH);

    // Initialize HomeSpan.
    homeSpan.setControlPin(CONTROL_PIN);
    homeSpan.setStatusPin(STATUS_LED_PIN);
    homeSpan.setPairingCode("83278456");
    homeSpan.begin(Category::Bridges, "DroneTales Video Doorbell Bridge");

    // Build device's serial number.
    char Sn[24];
    snprintf(Sn, 24, "DRONETALES-%llX", ESP.getEfuseMac());

    // Configure the Bridge accessory. We do not need to add name as it is taken
    // from the begin() method.
    new SpanAccessory();
	new Service::AccessoryInformation();
	new Characteristic::Identify();
    new Characteristic::Manufacturer("DroneTales");
    new Characteristic::SerialNumber(Sn);
    new Characteristic::Model("DroneTales Video Doorbell");
    new Characteristic::FirmwareRevision("1.0.3.0");

    // Configure doorbell switch.
    new SpanAccessory();
    new Service::AccessoryInformation();
    new Characteristic::Identify();
    new Characteristic::Manufacturer("DroneTales");
    new Characteristic::SerialNumber(Sn);
    new Characteristic::Model("DroneTales Video Doorbell");
    new Characteristic::FirmwareRevision("1.0.3.0");
    new Characteristic::Name("Video Doorbell Sound Switch");
    new DoorbellSwitch();

    // Create and start doorbell signal processing task.
    xTaskCreate(DoorbellSignalTask, "Doorbell Signal Task", 1024, nullptr,
        tskIDLE_PRIORITY, &DoorbellSignalTaskHandle);
    
    // Attached the interrupt to the ring signal pin.
    attachInterrupt(BELL_BUTTON_PIN, RingInterrupt, CHANGE);
}

// Arduino main loop.
void loop()
{
    // Process the HomeSpan messages.
    homeSpan.poll();
}

/**************************************************************************************/
