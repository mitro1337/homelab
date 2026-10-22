#ifndef SMART_THERMOSTAT_CONFIG_H
#define SMART_THERMOSTAT_CONFIG_H

// ==============================================================================
// Smart Thermostat Controller Configuration
// Author: Moană Ștefănuț-Cornel (@stefanutc1)
// Architecture: ESP32-WROOM-32 / NodeMCU-32S
// Network: VLAN 50 (IoT & Physical Edge)
// ==============================================================================

// WiFi Configuration
#define WIFI_SSID               "Datacenter-IoT"
#define WIFI_PASSWORD           "SecureIoTPassphrase"
#define WIFI_CONNECT_TIMEOUT    15000 // ms

// MQTT Broker Configuration
#define MQTT_BROKER             "192.168.20.10" // Home Assistant / Mosquitto on VLAN 20
#define MQTT_PORT               1883
#define MQTT_CLIENT_ID          "esp32-smart-thermostat"
#define MQTT_USER               "homelab_iot"
#define MQTT_PASS               "HomelabMqttPassword2026"

// MQTT Topics
#define TOPIC_THERMOSTAT_STATE      "homelab/climate/thermostat/state"
#define TOPIC_THERMOSTAT_SET_TEMP   "homelab/climate/thermostat/set_target"
#define TOPIC_THERMOSTAT_SET_MODE   "homelab/climate/thermostat/set_mode"
#define TOPIC_THERMOSTAT_TELEMETRY  "homelab/climate/thermostat/telemetry"
#define TOPIC_THERMOSTAT_STATUS     "homelab/devices/thermostat/status"

// Temperature & Humidity Sensor (DHT22 / AM2302)
#define DHT_PIN                 4

// HVAC Control Relays (Active LOW Optocoupler Relay Board)
#define RELAY_HEAT_PIN          25 // Call for Heat (W1)
#define RELAY_COOL_PIN          26 // Call for Cool (Y1)
#define RELAY_FAN_PIN           27 // Call for Fan (G)

// Physical Buttons for Local Manual Override
#define BUTTON_UP_PIN           32 // Temp Setpoint Increment (+0.5C)
#define BUTTON_DOWN_PIN         33 // Temp Setpoint Decrement (-0.5C)

// Status LED Indicator
#define STATUS_LED_PIN          2  // Onboard blue LED

// OLED Display (SSD1306 128x64 I2C)
#define OLED_SDA_PIN            21
#define OLED_SCL_PIN            22
#define OLED_I2C_ADDR           0x3C

// Thermostat Control Parameters
#define DEFAULT_TARGET_TEMP_C   21.5f
#define DEFAULT_HYSTERESIS_C    0.5f
#define MIN_TARGET_TEMP_C       15.0f
#define MAX_TARGET_TEMP_C       30.0f
#define ANTI_CYCLE_DELAY_MS     180000 // 3 minutes compressor protection delay
#define SENSOR_TIMEOUT_MS       60000  // Fail-safe shutdown if sensor stale >60s

// Watchdog Timer
#define WDT_TIMEOUT_SECONDS     15

#endif // SMART_THERMOSTAT_CONFIG_H
