/*
 * ==============================================================================
 * ESP32 Smart Motion Sensor Retrofit Appliance
 * Author: Moană Ștefănuț-Cornel (@stefanutc1)
 * Platform: ESP32 (Arduino Core / Espressif IoT Development Framework)
 * Network: VLAN 50 (IoT & Physical Edge)
 *
 * Capabilities:
 * - Retrofits conventional dumb PIR sensors (HC-SR501 / AM312) into smart nodes
 * - Digital anti-chatter debounce and software occupancy hold timer (30s)
 * - Dual-tech sensing support (combining PIR with RCWL-0516 microwave radar)
 * - Ambient light measurement via LDR voltage divider (illuminance in lux)
 * - 18650 Li-ion battery fuel gauge monitoring via ADC voltage divider
 * - Physical enclosure tamper microswitch protection
 * - Hardware Watchdog Timer (esp_task_wdt) for continuous 24/7 reliability
 * - Instant zero-latency MQTT state publishing + Home Assistant MQTT discovery
 * ==============================================================================
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <esp_task_wdt.h>
#include "config.h"
#include "motion_detector.h"

// Networking & MQTT
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Motion Detector Core Instance
MotionDetector detector(PIR_INPUT_PIN, RADAR_INPUT_PIN, LDR_ADC_PIN, BATTERY_ADC_PIN, TAMPER_SWITCH_PIN);

// Operational Timing
unsigned long lastHeartbeatTime = 0;

// Function Prototypes
void connectWiFi();
void connectMQTT();
void publishHomeAssistantDiscovery();
void publishState(bool forceHeartbeat);
void mqttCallback(char* topic, byte* message, unsigned int length);

void setup() {
    Serial.begin(115200);
    delay(100);

    Serial.println(F("\n================================================"));
    Serial.println(F("ESP32 Smart Motion Sensor Retrofit Starting"));
    Serial.println(F("Author: Moană Ștefănuț-Cornel (@stefanutc1)"));
    Serial.println(F("Architecture: ESP32-WROOM-32 · VLAN 50 IoT Edge"));
    Serial.println(F("================================================"));

    // Status Indicator
    pinMode(STATUS_LED_PIN, OUTPUT);
    digitalWrite(STATUS_LED_PIN, LOW);

    // Initialize Motion Detector Core
    detector.begin();
    Serial.println(F("[SYSTEM] Conventional PIR and sensory inputs initialized."));

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
        publishState(true);
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

    // 1. Process sensor sampling and detect state changes
    bool stateChanged = detector.update();
    if (stateChanged) {
        Serial.printf("[EVENT] Motion State: %s | Tamper: %s | Lux: %.1f | Bat: %d%%\n",
                      detector.isMotionDetected() ? "OCCUPIED" : "CLEAR",
                      detector.isTampered() ? "TAMPERED" : "SECURE",
                      detector.getAmbientLux(),
                      detector.getBatteryPercentage());

        // Flash activity LED
        digitalWrite(STATUS_LED_PIN, detector.isMotionDetected() ? HIGH : LOW);

        // Immediate low-latency MQTT publish
        publishState(false);
    }

    // 2. Periodic Heartbeat / Telemetry Broadcast
    if (now - lastHeartbeatTime >= HEARTBEAT_INTERVAL_MS) {
        lastHeartbeatTime = now;
        publishState(true);
    }
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
        Serial.println(F("\n[WIFI] Connection failed. Running in autonomous local mode."));
    }
}

void connectMQTT() {
    if (mqttClient.connected() || WiFi.status() != WL_CONNECTED) return;

    Serial.print(F("[MQTT] Connecting to broker: "));
    Serial.println(MQTT_BROKER);

    if (mqttClient.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASS, TOPIC_MOTION_STATUS, 1, true, "offline")) {
        Serial.println(F("[MQTT] Connected to Mosquitto."));
        mqttClient.publish(TOPIC_MOTION_STATUS, "online", true);

        publishHomeAssistantDiscovery();
        publishState(true);
    } else {
        Serial.printf("[MQTT] Connection failed, rc=%d. Retrying in background.\n", mqttClient.state());
    }
}

void mqttCallback(char* topic, byte* message, unsigned int length) {
    // Read-only sensor node, callbacks reserved for remote sensitivity tuning
}

void publishState(bool forceHeartbeat) {
    if (!mqttClient.connected()) return;

    StaticJsonDocument<256> doc;
    doc["occupancy"] = detector.isMotionDetected() ? "ON" : "OFF";
    doc["tamper"] = detector.isTampered() ? "ON" : "OFF";
    doc["illuminance_lux"] = round(detector.getAmbientLux() * 10.0f) / 10.0f;
    doc["battery_voltage"] = round(detector.getBatteryVoltage() * 100.0f) / 100.0f;
    doc["battery_percent"] = detector.getBatteryPercentage();
    doc["uptime_sec"] = millis() / 1000;

    char buffer[256];
    serializeJson(doc, buffer);

    mqttClient.publish(TOPIC_MOTION_STATE, buffer, true);

    if (forceHeartbeat) {
        mqttClient.publish(TOPIC_MOTION_TELEMETRY, buffer);
    }
}

void publishHomeAssistantDiscovery() {
    if (!mqttClient.connected()) return;

    // 1. Binary Sensor: Motion Occupancy
    {
        const char* discTopic = "homeassistant/binary_sensor/smart_motion_sensor/occupancy/config";
        StaticJsonDocument<512> doc;
        doc["name"] = "Smart Motion Occupancy";
        doc["unique_id"] = "esp32_smart_motion_occupancy";
        doc["device_class"] = "motion";
        doc["state_topic"] = TOPIC_MOTION_STATE;
        doc["value_template"] = "{{ value_json.occupancy }}";
        doc["payload_on"] = "ON";
        doc["payload_off"] = "OFF";

        JsonObject dev = doc.createNestedObject("device");
        dev["identifiers"][0] = "esp32_smart_motion_sensor";
        dev["name"] = "ESP32 Smart Motion Sensor";
        dev["model"] = "ESP32-PIR-Retrofit";
        dev["manufacturer"] = "Homelab Physical Computing";

        char buffer[512];
        serializeJson(doc, buffer);
        mqttClient.publish(discTopic, buffer, true);
    }

    // 2. Binary Sensor: Enclosure Tamper
    {
        const char* discTopic = "homeassistant/binary_sensor/smart_motion_sensor/tamper/config";
        StaticJsonDocument<512> doc;
        doc["name"] = "Smart Motion Tamper";
        doc["unique_id"] = "esp32_smart_motion_tamper";
        doc["device_class"] = "problem";
        doc["state_topic"] = TOPIC_MOTION_STATE;
        doc["value_template"] = "{{ value_json.tamper }}";
        doc["payload_on"] = "ON";
        doc["payload_off"] = "OFF";

        JsonObject dev = doc.createNestedObject("device");
        dev["identifiers"][0] = "esp32_smart_motion_sensor";

        char buffer[512];
        serializeJson(doc, buffer);
        mqttClient.publish(discTopic, buffer, true);
    }

    // 3. Sensor: Illuminance (Lux)
    {
        const char* discTopic = "homeassistant/sensor/smart_motion_sensor/illuminance/config";
        StaticJsonDocument<512> doc;
        doc["name"] = "Smart Motion Illuminance";
        doc["unique_id"] = "esp32_smart_motion_lux";
        doc["device_class"] = "illuminance";
        doc["unit_of_measurement"] = "lx";
        doc["state_topic"] = TOPIC_MOTION_STATE;
        doc["value_template"] = "{{ value_json.illuminance_lux }}";

        JsonObject dev = doc.createNestedObject("device");
        dev["identifiers"][0] = "esp32_smart_motion_sensor";

        char buffer[512];
        serializeJson(doc, buffer);
        mqttClient.publish(discTopic, buffer, true);
    }

    // 4. Sensor: Battery Percent
    {
        const char* discTopic = "homeassistant/sensor/smart_motion_sensor/battery/config";
        StaticJsonDocument<512> doc;
        doc["name"] = "Smart Motion Battery";
        doc["unique_id"] = "esp32_smart_motion_battery";
        doc["device_class"] = "battery";
        doc["unit_of_measurement"] = "%";
        doc["state_topic"] = TOPIC_MOTION_STATE;
        doc["value_template"] = "{{ value_json.battery_percent }}";

        JsonObject dev = doc.createNestedObject("device");
        dev["identifiers"][0] = "esp32_smart_motion_sensor";

        char buffer[512];
        serializeJson(doc, buffer);
        mqttClient.publish(discTopic, buffer, true);
    }

    Serial.println(F("[MQTT] Home Assistant motion and sensory discovery payloads registered."));
}
