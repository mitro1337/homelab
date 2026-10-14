#include "motion_detector.h"
#include "config.h"

MotionDetector::MotionDetector(uint8_t pirPin, uint8_t radarPin, uint8_t ldrPin, uint8_t batteryPin, uint8_t tamperPin)
    : _pirPin(pirPin),
      _radarPin(radarPin),
      _ldrPin(ldrPin),
      _batteryPin(batteryPin),
      _tamperPin(tamperPin),
      _motionState(false),
      _tamperState(false),
      _lastMotionTriggerTime(0),
      _lastRawPulseTime(0),
      _rawPulseCount(0),
      _cachedLux(0.0f),
      _cachedBatteryVoltage(4.0f),
      _cachedBatteryPercent(100),
      _lastAnalogSampleTime(0) {}

void MotionDetector::begin() {
    pinMode(_pirPin, INPUT);
    pinMode(_radarPin, INPUT);
    pinMode(_tamperPin, INPUT_PULLUP);

    // ADC pins on ESP32 configured with 11dB attenuation (0 - 3.3V range)
    analogSetAttenuation(ADC_11db);

    sampleAnalogSensors();
}

bool MotionDetector::update() {
    unsigned long now = millis();
    bool stateChanged = false;

    // Read digital inputs
    int pirValue = digitalRead(_pirPin);
    int radarValue = digitalRead(_radarPin);
    int tamperValue = digitalRead(_tamperPin);

    // Tamper detection: switch open (HIGH with PULLUP if depressed = LOW)
    bool currentTamper = (tamperValue == HIGH);
    if (currentTamper != _tamperState) {
        _tamperState = currentTamper;
        stateChanged = true;
    }

    // Motion detection: conventional sensor outputs HIGH when triggered
    bool rawTrigger = (pirValue == HIGH || radarValue == HIGH);

    if (rawTrigger) {
        if (now - _lastRawPulseTime > DEBOUNCE_TIME_MS) {
            _lastRawPulseTime = now;
            _rawPulseCount++;
            _lastMotionTriggerTime = now;

            if (!_motionState) {
                _motionState = true;
                stateChanged = true;
            }
        }
    } else {
        // Evaluate occupancy hold timer
        if (_motionState && (now - _lastMotionTriggerTime >= OCCUPANCY_HOLD_TIME_MS)) {
            _motionState = false;
            stateChanged = true;
        }
    }

    // Sample analog sensors every 5 seconds to reduce ADC noise and CPU load
    if (now - _lastAnalogSampleTime >= 5000) {
        sampleAnalogSensors();
        _lastAnalogSampleTime = now;
    }

    return stateChanged;
}

void MotionDetector::sampleAnalogSensors() {
    // 1. Ambient Light Sampling (LDR)
    int ldrRaw = analogRead(_ldrPin);
    // Approximate conversion to lux: 4095 (dark) down to 0 (bright) or vice versa depending on divider
    float normalizedLight = (4095.0f - (float)ldrRaw) / 4095.0f;
    if (normalizedLight < 0.0f) normalizedLight = 0.0f;
    _cachedLux = normalizedLight * 500.0f; // Scale up to 500 lux nominal indoor

    // 2. Battery Voltage Sampling
    int batRaw = analogRead(_batteryPin);
    // ESP32 ADC: 3.3V reference / 4095 steps
    float pinVoltage = ((float)batRaw / 4095.0f) * 3.3f * 1.05f; // Calibration factor
    float actualBatVoltage = pinVoltage * ((BATTERY_ADC_R1 + BATTERY_ADC_R2) / BATTERY_ADC_R2);

    _cachedBatteryVoltage = actualBatVoltage;

    // Calculate percentage
    float pct = ((actualBatVoltage - BATTERY_VOLTAGE_MIN) / (BATTERY_VOLTAGE_MAX - BATTERY_VOLTAGE_MIN)) * 100.0f;
    if (pct > 100.0f) pct = 100.0f;
    if (pct < 0.0f) pct = 0.0f;
    _cachedBatteryPercent = (int)pct;
}

bool MotionDetector::isMotionDetected() const {
    return _motionState;
}

bool MotionDetector::isTampered() const {
    return _tamperState;
}

float MotionDetector::getAmbientLux() {
    return _cachedLux;
}

float MotionDetector::getBatteryVoltage() {
    return _cachedBatteryVoltage;
}

int MotionDetector::getBatteryPercentage() {
    return _cachedBatteryPercent;
}

unsigned long MotionDetector::getLastMotionAgeSeconds() const {
    if (_lastMotionTriggerTime == 0) return 999999;
    return (millis() - _lastMotionTriggerTime) / 1000;
}
