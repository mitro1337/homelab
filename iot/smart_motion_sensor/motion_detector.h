#ifndef MOTION_DETECTOR_H
#define MOTION_DETECTOR_H

#include <Arduino.h>

class MotionDetector {
public:
    MotionDetector(uint8_t pirPin, uint8_t radarPin, uint8_t ldrPin, uint8_t batteryPin, uint8_t tamperPin);

    void begin();
    bool update();

    bool isMotionDetected() const;
    bool isTampered() const;
    float getAmbientLux();
    float getBatteryVoltage();
    int getBatteryPercentage();
    unsigned long getLastMotionAgeSeconds() const;

private:
    uint8_t _pirPin;
    uint8_t _radarPin;
    uint8_t _ldrPin;
    uint8_t _batteryPin;
    uint8_t _tamperPin;

    bool _motionState;
    bool _tamperState;
    unsigned long _lastMotionTriggerTime;
    unsigned long _lastRawPulseTime;
    int _rawPulseCount;

    float _cachedLux;
    float _cachedBatteryVoltage;
    int _cachedBatteryPercent;
    unsigned long _lastAnalogSampleTime;

    void sampleAnalogSensors();
};

#endif // MOTION_DETECTOR_H
