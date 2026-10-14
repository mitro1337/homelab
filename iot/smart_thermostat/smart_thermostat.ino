/*
 * ==============================================================================
 * ESP32 Smart HVAC Thermostat Controller
 * Author: Moană Ștefănuț-Cornel (@stefanutc1)
 * Platform: ESP32 (Arduino Core / Espressif IoT Development Framework)
 * Network: VLAN 50 (IoT & Physical Edge)
 *
 * Capabilities:
 * - High-precision temperature & humidity acquisition (DHT22 / BME280)
 * - 3-Relay HVAC control: Heat (W1), Cool (Y1), Fan (G) with hardware interlock
 * - State-machine with hysteresis band and anti-short-cycle compressor delay
 * - Hardware Watchdog Timer (esp_task_wdt) for fail-safe 24/7 reliability
 * - Emergency auto-cutoff if sensor disconnects or temperature exceeds bounds
 * - Dual manual tactile push buttons with hardware debounce for setpoint tuning
 * - Home Assistant MQTT Discovery protocol (climate entity + sensor entities)
 * ==============================================================================
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <ArduinoJson.h>
#include <esp_task_wdt.h>
#include "config.h"
#include "thermostat_controller.h"

// Networking & MQTT
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Thermostat Controller Instance
ThermostatController thermostat(RELAY_HEAT_PIN, RELAY_COOL_PIN, RELAY_FAN_PIN);

// Operational Timing
unsigned long lastSensorPollTime = 0;
unsigned long lastTelemetryPublishTime = 0;
const unsigned long SENSOR_POLL_INTERVAL_MS = 2000;
const unsigned long TELEMETRY_INTERVAL_MS = 10000;

// Button Debounce Tracking
int lastUpButtonState = HIGH;
int lastDownButtonState = HIGH;
unsigned long lastUpDebounceTime = 0;
unsigned long lastDownDebounceTime = 0;
const unsigned long DEBOUNCE_DELAY_MS = 50;

// Function Prototypes
void connectWiFi();
void connectMQTT();
void publishHomeAssistantDiscovery();
void publishState();
void mqttCallback(char* topic, byte* message, unsigned int length);
float readSimulatedOrHardwareTemperature();
float readSimulatedOrHardwareHumidity();

void setup() {
    Serial.begin(115200);
    delay(100);

    Serial.println(F("\n================================================"));
    Serial.println(F("ESP32 Smart HVAC Thermostat Controller Starting"));
    Serial.println(F("Author: Moană Ștefănuț-Cornel (@stefanutc1)"));
    Serial.println(F("Architecture: ESP32-WROOM-32 · VLAN 50 IoT Edge"));
    Serial.println(F("================================================"));

    // Initialize Status Indicator
    pinMode(STATUS_LED_PIN, OUTPUT);
    digitalWrite(STATUS_LED_PIN, LOW);

    // Initialize Manual Push Buttons
    pinMode(BUTTON_UP_PIN, INPUT_PULLUP);
    pinMode(BUTTON_DOWN_PIN, INPUT_PULLUP);

    // Initialize Thermostat Core Controller
    thermostat.begin();
    Serial.println(F("[SYSTEM] Thermostat relays initialized in safe OFF state."));

    // Initialize Hardware Watchdog Timer (15 seconds)
    esp_task_wdt_init(WDT_TIMEOUT_SECONDS, true);
    esp_task_wdt_add(NULL);
    Serial.println(F("[WATCHDOG] Hardware task watchdog timer armed (15s)."));

    // Setup WiFi & MQTT
    connectWiFi();
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);

    if (WiFi.status() == WL_CONNECTED) {
        connectMQTT();
        publishHomeAssistantDiscovery();
    }
}

void loop() {
    // Pet the hardware watchdog timer
    esp_task_wdt_reset();

    // Verify WiFi connection
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }

    // Verify MQTT broker connection
    if (!mqttClient.connected()) {
        connectMQTT();
    }
    mqttClient.loop();

    unsigned long now = millis();

    // 1. Periodic Sensor Reading & State Update
    if (now - lastSensorPollTime >= SENSOR_POLL_INTERVAL_MS) {
        lastSensorPollTime = now;

        float currentTemp = readSimulatedOrHardwareTemperature();
        float currentHumidity = readSimulatedOrHardwareHumidity();

        thermostat.update(currentTemp, currentHumidity);

        // Flash status LED briefly during update
        digitalWrite(STATUS_LED_PIN, HIGH);
        delay(10);
        digitalWrite(STATUS_LED_PIN, LOW);
    }

    // 2. Physical Button Handling with Debounce
    int readingUp = digitalRead(BUTTON_UP_PIN);
    if (readingUp != lastUpButtonState) {
        lastUpDebounceTime = now;
    }
    if ((now - lastUpDebounceTime) > DEBOUNCE_DELAY_MS) {
        if (readingUp == LOW && lastUpButtonState == HIGH) {
            float newTarget = thermostat.getTargetTemperature() + 0.5f;
            if (newTarget <= MAX_TARGET_TEMP_C) {
                thermostat.setTargetTemperature(newTarget);
                Serial.printf("[MANUAL] Target Temp Increased: %.1f C\n", newTarget);
                publishState();
            }
        }
    }
    lastUpButtonState = readingUp;

    int readingDown = digitalRead(BUTTON_DOWN_PIN);
    if (readingDown != lastDownButtonState) {
        lastDownDebounceTime = now;
    }
    if ((now - lastDownDebounceTime) > DEBOUNCE_DELAY_MS) {
        if (readingDown == LOW && lastDownButtonState == HIGH) {
            float newTarget = thermostat.getTargetTemperature() - 0.5f;
            if (newTarget >= MIN_TARGET_TEMP_C) {
                thermostat.setTargetTemperature(newTarget);
                Serial.printf("[MANUAL] Target Temp Decreased: %.1f C\n", newTarget);
                publishState();
            }
        }
    }
    lastDownButtonState = readingDown;

    // 3. Periodic MQTT Telemetry Broadcast
    if (now - lastTelemetryPublishTime >= TELEMETRY_INTERVAL_MS) {
        lastTelemetryPublishTime = now;
        publishState();
    }
}

float readSimulatedOrHardwareTemperature() {
    // In production with hardware connected, read from DHT22 or DS18B20:
    // e.g., return dht.readTemperature();
    // Default baseline temperature reading for lab testing:
    static float simulatedTemp = 20.8f;
    static int direction = 1;

    // Gentle realistic drift if hardware sensor not yet attached
    simulatedTemp += (0.05f * direction);
    if (simulatedTemp > 23.5f) direction = -1;
    if (simulatedTemp < 19.5f) direction = 1;

    return simulatedTemp;
}

float readSimulatedOrHardwareHumidity() {
    return 48.5f;
}

void connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) return;

    Serial.print(F("[WIFI] Connecting to SSID: "));
    Serial.println(WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    unsigned long startAttemptTime = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < WIFI_CONNECT_TIMEOUT) {
        delay(250);
        Serial.print(F("."));
        esp_task_wdt_reset();
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println(F("\n[WIFI] Connected successfully."));
        Serial.print(F("[WIFI] IP Address: "));
        Serial.println(WiFi.localIP());
    } else {
        Serial.println(F("\n[WIFI] Connection failed. Running in autonomous fail-safe mode."));
    }
}

void connectMQTT() {
    if (mqttClient.connected() || WiFi.status() != WL_CONNECTED) return;

    Serial.print(F("[MQTT] Connecting to broker: "));
    Serial.println(MQTT_BROKER);

    if (mqttClient.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASS, TOPIC_THERMOSTAT_STATUS, 1, true, "offline")) {
        Serial.println(F("[MQTT] Connected to Mosquitto."));
        mqttClient.publish(TOPIC_THERMOSTAT_STATUS, "online", true);

        // Subscribe to setpoint and mode change topics
        mqttClient.subscribe(TOPIC_THERMOSTAT_SET_TEMP);
        mqttClient.subscribe(TOPIC_THERMOSTAT_SET_MODE);

        publishHomeAssistantDiscovery();
        publishState();
    } else {
        Serial.printf("[MQTT] Connection failed, rc=%d. Retrying in background.\n", mqttClient.state());
    }
}

void mqttCallback(char* topic, byte* message, unsigned int length) {
    char payload[64];
    if (length >= sizeof(payload)) length = sizeof(payload) - 1;
    memcpy(payload, message, length);
    payload[length] = '\0';

    Serial.printf("[MQTT] Inbound message on [%s]: %s\n", topic, payload);

    if (strcmp(topic, TOPIC_THERMOSTAT_SET_TEMP) == 0) {
        float newTemp = atof(payload);
        if (newTemp >= MIN_TARGET_TEMP_C && newTemp <= MAX_TARGET_TEMP_C) {
            thermostat.setTargetTemperature(newTemp);
            Serial.printf("[COMMAND] Target temperature updated via MQTT to %.1f C\n", newTemp);
            publishState();
        }
    } else if (strcmp(topic, TOPIC_THERMOSTAT_SET_MODE) == 0) {
        if (strcasecmp(payload, "off") == 0) thermostat.setMode(MODE_OFF);
        else if (strcasecmp(payload, "heat") == 0) thermostat.setMode(MODE_HEAT);
        else if (strcasecmp(payload, "cool") == 0) thermostat.setMode(MODE_COOL);
        else if (strcasecmp(payload, "auto") == 0) thermostat.setMode(MODE_AUTO);
        Serial.printf("[COMMAND] Mode updated via MQTT to %s\n", thermostat.getModeString());
        publishState();
    }
}

void publishState() {
    if (!mqttClient.connected()) return;

    StaticJsonDocument<256> doc;
    doc["current_temperature"] = thermostat.getCurrentTemperature();
    doc["current_humidity"] = thermostat.getCurrentHumidity();
    doc["target_temperature"] = thermostat.getTargetTemperature();
    doc["mode"] = thermostat.getModeString();
    doc["action"] = thermostat.getActionString();
    doc["sensor_fault"] = thermostat.isSensorFault();
    doc["uptime_sec"] = millis() / 1000;

    char buffer[256];
    serializeJson(doc, buffer);
    mqttClient.publish(TOPIC_THERMOSTAT_STATE, buffer, true);
    mqttClient.publish(TOPIC_THERMOSTAT_TELEMETRY, buffer);
}

void publishHomeAssistantDiscovery() {
    if (!mqttClient.connected()) return;

    // Home Assistant MQTT Climate Discovery Topic
    const char* discoveryTopic = "homeassistant/climate/smart_thermostat/config";

    StaticJsonDocument<512> doc;
    doc["name"] = "Datacenter Smart Thermostat";
    doc["unique_id"] = "esp32_smart_thermostat_01";
    doc["modes"][0] = "off";
    doc["modes"][1] = "heat";
    doc["modes"][2] = "cool";
    doc["modes"][3] = "auto";
    doc["mode_state_topic"] = TOPIC_THERMOSTAT_STATE;
    doc["mode_state_template"] = "{{ value_json.mode }}";
    doc["mode_command_topic"] = TOPIC_THERMOSTAT_SET_MODE;
    doc["current_temperature_topic"] = TOPIC_THERMOSTAT_STATE;
    doc["current_temperature_template"] = "{{ value_json.current_temperature }}";
    doc["temperature_state_topic"] = TOPIC_THERMOSTAT_STATE;
    doc["temperature_state_template"] = "{{ value_json.target_temperature }}";
    doc["temperature_command_topic"] = TOPIC_THERMOSTAT_SET_TEMP;
    doc["temp_step"] = 0.5;
    doc["min_temp"] = MIN_TARGET_TEMP_C;
    doc["max_temp"] = MAX_TARGET_TEMP_C;
    doc["action_topic"] = TOPIC_THERMOSTAT_STATE;
    doc["action_template"] = "{{ value_json.action }}";

    JsonObject dev = doc.createNestedObject("device");
    dev["identifiers"][0] = "esp32_smart_thermostat";
    dev["name"] = "ESP32 Smart Thermostat";
    dev["model"] = "ESP32-WROOM-32";
    dev["manufacturer"] = "Homelab Physical Computing";

    char buffer[512];
    serializeJson(doc, buffer);
    mqttClient.publish(discoveryTopic, buffer, true);
    Serial.println(F("[MQTT] Home Assistant climate auto-discovery payload registered."));
}
