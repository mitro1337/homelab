#include "thermostat_controller.h"
#include "config.h"

ThermostatController::ThermostatController(uint8_t heatPin, uint8_t coolPin, uint8_t fanPin)
    : _heatPin(heatPin),
      _coolPin(coolPin),
      _fanPin(fanPin),
      _mode(MODE_HEAT),
      _action(ACTION_OFF),
      _targetTemp(DEFAULT_TARGET_TEMP_C),
      _hysteresis(DEFAULT_HYSTERESIS_C),
      _currentTemp(20.0f),
      _currentHumidity(50.0f),
      _lastStateChangeTime(0),
      _lastSensorReadTime(0),
      _sensorFault(false) {}

void ThermostatController::begin() {
    pinMode(_heatPin, OUTPUT);
    pinMode(_coolPin, OUTPUT);
    pinMode(_fanPin, OUTPUT);

    // Active LOW optocoupled relays: HIGH = OFF, LOW = ON
    setRelayStates(false, false, false);
    _lastStateChangeTime = millis();
}

void ThermostatController::setRelayStates(bool heatOn, bool coolOn, bool fanOn) {
    // Interlock: never allow heat and cool to run simultaneously
    if (heatOn && coolOn) {
        coolOn = false;
    }

    digitalWrite(_heatPin, heatOn ? LOW : HIGH);
    digitalWrite(_coolPin, coolOn ? LOW : HIGH);
    digitalWrite(_fanPin, (fanOn || heatOn || coolOn) ? LOW : HIGH);
}

void ThermostatController::emergencyShutdown() {
    _action = ACTION_OFF;
    setRelayStates(false, false, false);
}

void ThermostatController::update(float currentTemp, float currentHumidity) {
    unsigned long now = millis();

    // Check for sensor validity
    if (isnan(currentTemp) || currentTemp < -10.0f || currentTemp > 50.0f) {
        if (!_sensorFault && (now - _lastSensorReadTime > SENSOR_TIMEOUT_MS)) {
            _sensorFault = true;
            emergencyShutdown();
        }
        return;
    }

    _sensorFault = false;
    _currentTemp = currentTemp;
    _currentHumidity = currentHumidity;
    _lastSensorReadTime = now;

    evaluateHvacLogic();
}

void ThermostatController::evaluateHvacLogic() {
    unsigned long now = millis();
    bool canChangeState = (now - _lastStateChangeTime >= ANTI_CYCLE_DELAY_MS);

    if (_mode == MODE_OFF || _sensorFault) {
        if (_action != ACTION_OFF) {
            _action = ACTION_OFF;
            setRelayStates(false, false, false);
            _lastStateChangeTime = now;
        }
        return;
    }

    if (_mode == MODE_HEAT) {
        if (_currentTemp <= (_targetTemp - _hysteresis)) {
            if (_action != ACTION_HEATING && canChangeState) {
                _action = ACTION_HEATING;
                setRelayStates(true, false, true);
                _lastStateChangeTime = now;
            }
        } else if (_currentTemp >= _targetTemp) {
            if (_action == ACTION_HEATING && canChangeState) {
                _action = ACTION_IDLE;
                setRelayStates(false, false, false);
                _lastStateChangeTime = now;
            } else if (_action == ACTION_OFF) {
                _action = ACTION_IDLE;
            }
        }
    } else if (_mode == MODE_COOL) {
        if (_currentTemp >= (_targetTemp + _hysteresis)) {
            if (_action != ACTION_COOLING && canChangeState) {
                _action = ACTION_COOLING;
                setRelayStates(false, true, true);
                _lastStateChangeTime = now;
            }
        } else if (_currentTemp <= _targetTemp) {
            if (_action == ACTION_COOLING && canChangeState) {
                _action = ACTION_IDLE;
                setRelayStates(false, false, false);
                _lastStateChangeTime = now;
            } else if (_action == ACTION_OFF) {
                _action = ACTION_IDLE;
            }
        }
    } else if (_mode == MODE_AUTO) {
        // Auto mode maintains temperature within comfortable dual setpoint window
        if (_currentTemp <= (_targetTemp - _hysteresis)) {
            if (_action != ACTION_HEATING && canChangeState) {
                _action = ACTION_HEATING;
                setRelayStates(true, false, true);
                _lastStateChangeTime = now;
            }
        } else if (_currentTemp >= (_targetTemp + _hysteresis)) {
            if (_action != ACTION_COOLING && canChangeState) {
                _action = ACTION_COOLING;
                setRelayStates(false, true, true);
                _lastStateChangeTime = now;
            }
        } else {
            if ((_action == ACTION_HEATING || _action == ACTION_COOLING) && canChangeState) {
                _action = ACTION_IDLE;
                setRelayStates(false, false, false);
                _lastStateChangeTime = now;
            } else if (_action == ACTION_OFF) {
                _action = ACTION_IDLE;
            }
        }
    }
}

void ThermostatController::setTargetTemperature(float temp) {
    if (temp >= MIN_TARGET_TEMP_C && temp <= MAX_TARGET_TEMP_C) {
        _targetTemp = temp;
        evaluateHvacLogic();
    }
}

float ThermostatController::getTargetTemperature() const {
    return _targetTemp;
}

void ThermostatController::setHysteresis(float hysteresis) {
    if (hysteresis >= 0.1f && hysteresis <= 3.0f) {
        _hysteresis = hysteresis;
        evaluateHvacLogic();
    }
}

float ThermostatController::getHysteresis() const {
    return _hysteresis;
}

void ThermostatController::setMode(ThermostatMode mode) {
    _mode = mode;
    evaluateHvacLogic();
}

ThermostatMode ThermostatController::getMode() const {
    return _mode;
}

const char* ThermostatController::getModeString() const {
    switch (_mode) {
        case MODE_OFF:  return "off";
        case MODE_HEAT: return "heat";
        case MODE_COOL: return "cool";
        case MODE_AUTO: return "auto";
        default:        return "off";
    }
}

HvacAction ThermostatController::getAction() const {
    return _action;
}

const char* ThermostatController::getActionString() const {
    switch (_action) {
        case ACTION_OFF:     return "off";
        case ACTION_HEATING: return "heating";
        case ACTION_COOLING: return "cooling";
        case ACTION_IDLE:    return "idle";
        default:             return "off";
    }
}

float ThermostatController::getCurrentTemperature() const {
    return _currentTemp;
}

float ThermostatController::getCurrentHumidity() const {
    return _currentHumidity;
}

bool ThermostatController::isSensorFault() const {
    return _sensorFault;
}
