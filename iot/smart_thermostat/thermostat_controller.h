#ifndef THERMOSTAT_CONTROLLER_H
#define THERMOSTAT_CONTROLLER_H

#include <Arduino.h>

enum ThermostatMode {
    MODE_OFF,
    MODE_HEAT,
    MODE_COOL,
    MODE_AUTO
};

enum HvacAction {
    ACTION_OFF,
    ACTION_HEATING,
    ACTION_COOLING,
    ACTION_IDLE
};

class ThermostatController {
public:
    ThermostatController(uint8_t heatPin, uint8_t coolPin, uint8_t fanPin);

    void begin();
    void update(float currentTemp, float currentHumidity);

    void setTargetTemperature(float temp);
    float getTargetTemperature() const;

    void setHysteresis(float hysteresis);
    float getHysteresis() const;

    void setMode(ThermostatMode mode);
    ThermostatMode getMode() const;
    const char* getModeString() const;

    HvacAction getAction() const;
    const char* getActionString() const;

    float getCurrentTemperature() const;
    float getCurrentHumidity() const;
    bool isSensorFault() const;

    void emergencyShutdown();

private:
    uint8_t _heatPin;
    uint8_t _coolPin;
    uint8_t _fanPin;

    ThermostatMode _mode;
    HvacAction _action;

    float _targetTemp;
    float _hysteresis;
    float _currentTemp;
    float _currentHumidity;

    unsigned long _lastStateChangeTime;
    unsigned long _lastSensorReadTime;
    bool _sensorFault;

    void setRelayStates(bool heatOn, bool coolOn, bool fanOn);
    void evaluateHvacLogic();
};

#endif // THERMOSTAT_CONTROLLER_H
