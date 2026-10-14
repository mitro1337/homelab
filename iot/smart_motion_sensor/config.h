#ifndef SMART_MOTION_SENSOR_CONFIG_H
#define SMART_MOTION_SENSOR_CONFIG_H

// ==============================================================================
// Smart Motion Sensor Retrofit Configuration
// Author: Moană Ștefănuț-Cornel (@stefanutc1)
// Architecture: ESP32-WROOM-32 / NodeMCU-32S
// Network: VLAN 50 (IoT & Physical Edge)
// ==============================================================================

// WiFi Configuration
#define WIFI_SSID                   "Datacenter-IoT"
#define WIFI_PASSWORD               "SecureIoTPassphrase"
#define WIFI_CONNECT_TIMEOUT        15000 // ms

// MQTT Broker Configuration
#define MQTT_BROKER                 "192.168.20.10" // Home Assistant / Mosquitto on VLAN 20
#define MQTT_PORT                   1883
#define MQTT_CLIENT_ID              "esp32-smart-motion-sensor"
#define MQTT_USER                   "homelab_iot"
#define MQTT_PASS                   "HomelabMqttPassword2026"

// MQTT Topics
#define TOPIC_MOTION_STATE          "homelab/sensors/motion/state"
#define TOPIC_MOTION_TELEMETRY      "homelab/sensors/motion/telemetry"
#define TOPIC_MOTION_STATUS         "homelab/devices/motion/status"

// Conventional Sensor Signal Input Pins
#define PIR_INPUT_PIN               13 // Digital Out from Conventional PIR (HC-SR501 / AM312)
#define RADAR_INPUT_PIN             27 // Digital Out from Microwave Radar (RCWL-0516)

// Analog Sensory Inputs (ADC1 Channels Safe During WiFi)
#define LDR_ADC_PIN                 34 // Ambient Light Sensor (Photoresistor Divider)
#define BATTERY_ADC_PIN             35 // 18650 Battery Voltage Divider (100k / 100k)

// Security & Enclosure Inputs
#define TAMPER_SWITCH_PIN           14 // Case Tamper Detection Microswitch (Active LOW)

// Status LED Indicator
#define STATUS_LED_PIN              2  // Onboard Activity / Heartbeat LED

// Motion Detection and Filter Parameters
#define OCCUPANCY_HOLD_TIME_MS      30000 // Keep motion state ON for 30s after last pulse
#define DEBOUNCE_TIME_MS            150   // Noise rejection window
#define HEARTBEAT_INTERVAL_MS       60000 // Telemetry broadcast interval

// Battery ADC Calibration Parameters
#define BATTERY_ADC_R1              100000.0f // 100k Ohm
#define BATTERY_ADC_R2              100000.0f // 100k Ohm
#define BATTERY_VOLTAGE_MIN         3.20f     // 0% charge
#define BATTERY_VOLTAGE_MAX         4.20f     // 100% charge

// Watchdog Timer
#define WDT_TIMEOUT_SECONDS         15

#endif // SMART_MOTION_SENSOR_CONFIG_H
