<div align="center">

# IoT & ESP32 Edge Systems & Physical Telemetry Suite

</div>

**Platform Architect**: Moană Ștefănuț-Cornel ([@stefanutc1](https://github.com/stefanutc1))  
**Academic Context**: Universitatea din Craiova · FEAA — Informatică Economică (2024 – 2027)  
**Network Segment**: VLAN 50 (`192.168.50.0/24` — Isolated IoT & Physical Edge)  

The homelab integrates an autonomous fleet of ESP32 microcontrollers deployed across six physical domains. All nodes operate on isolated VLAN 50, reporting telemetry over MQTT to Home Assistant (`CT 100`) and exposing native Prometheus scrape endpoints to Prometheus TSDB (`CT 104`).

---

<div align="center">

## 1. Automated Irrigation Controller (`iot/irrigation/`)

</div>

Microcontroller firmware for weather-aware, scheduled valve actuation with hardware fail-safes.

<div align="center">

### Source Files & Architecture

</div>

- `irrigation.ino` — Production Arduino sketch with WiFi auto-reconnect, MQTT telemetry, and safety timeout loops.
- `config.h` — Hardware pin mapping, safety duration caps (max 15m), and ADC calibration constants.
- `control.cpp` / `valve.cpp` — Solenoid valve actuation via optocoupled digital relay pins with fail-safe automatic shutoff.
- `ore.cpp` — Real-time clock (RTC) schedule engine synchronized via NTP (`pool.ntp.org`).
- `vreme.cpp` — Soil moisture and weather telemetry integration; automatically inhibits watering if precipitation is detected or rain inhibit is set.
- `logger.cpp` / `logger.h` — Serial and network syslog logging abstraction.

<div align="center">

### Hardware Mapping

</div>

```yaml
pins:
  relay_valve_zone1: 23  # Lawn Front (Active LOW)
  relay_valve_zone2: 22  # Lawn Back (Active LOW)
  relay_valve_zone3: 21  # Garden Beds (Active LOW)
  relay_valve_zone4: 19  # Greenhouse Drip (Active LOW)
  soil_moisture_adc1: 34 # Zone 1 Capacitive Probe
  soil_moisture_adc2: 35 # Zone 2 Capacitive Probe
  digital_rain_sensor: 32 # Active LOW on rain
  flow_meter_pulse: 33   # Hall-effect turbine pulse interrupt
```

---

<div align="center">

## 2. Footprint Biometric & Presence Sensor (`iot/footprint/`)

</div>

Presence and occupancy detection node paired with physical biometric gate access control.

<div align="center">

### Capabilities & Source Files

</div>

- `footprint.ino` — Master Arduino sketch executing concurrent presence tracking and biometric verification.
- `config.h` — Pin definitions for UART2 fingerprint scanner, ultrasonic sensor, PIR sensor, and relay.
- `sensor.cpp` — Dual PIR + Ultrasonic distance sensor sampling with noise filtering and debounce.
- `gate.cpp` — 12V Solenoid gate lock actuation with safety pulse duration (1,500ms).
- MQTT event dispatch to Home Assistant on topic `homelab/access/gate/event` and `homelab/sensors/footprint/presence`.

---

<div align="center">

## 3. Datacenter Rack Thermal Monitor (`iot/datacenter_environment/`)

</div>

Rack climate and thermal efficiency monitor managing cold/hot aisle delta-T and cooling fans.

<div align="center">

### Capabilities & Source Files

</div>

- `datacenter_environment.ino` — Autonomous temperature, humidity, and fan RPM regulation sketch.
- `config.h` — I2C BME280 addresses, 1-Wire DS18B20 digital probe buses, and 25 kHz PWM timer channels.
- **Embedded Prometheus Server**: Directly serves `/metrics` on port 80 for Prometheus scraping.
- **Dynamic Noctua PWM Control**: Automatically scales fan duty cycle from 25% (silent) to 100% based on exhaust heat.

---

<div align="center">

## 4. Datacenter Power & UPS Safety Appliance (`iot/power_monitor/`)

</div>

Grid failure detection and battery depletion monitor protecting bare-metal hypervisors from brownouts.

<div align="center">

### Capabilities & Source Files

</div>

- `power_monitor.ino` — Zero-latency mains monitoring and battery voltage tracking sketch.
- `config.h` — Optocoupler interrupt pins, battery voltage divider ratios, and threshold constants.
- **Zero-Latency Grid Loss Alert**: Detects AC power cuts in <10ms via hardware interrupt and dispatches urgent MQTT warning to Proxmox VE.
- **Automated Graceful Shutdown**: Initiates cluster shutdown if battery drops below 11.4V to prevent dirty disk unmounts.

---

<div align="center">

## 5. Smart HVAC Thermostat Controller (`iot/smart_thermostat/`)

</div>

Multi-stage heating and cooling climate regulator with hardware interlocks and compressor safety guards.

<div align="center">

### Capabilities & Source Files

</div>

- `smart_thermostat.ino` — FreeRTOS Arduino sketch running state machine, WiFi auto-reconnect, and MQTT discovery.
- `config.h` — Pinouts for DHT22 sensor, optocoupled HVAC relays (W1, Y1, G), tactile push buttons, and safety thresholds.
- `thermostat_controller.h` / `thermostat_controller.cpp` — Hysteresis control logic (0.5 C band) and 3-minute anti-cycle protection.
- **Fail-Safe Operation**: Immediate relay cutoff if sensor reports NaN or times out (>60s), preventing runaway heating.
- **Home Assistant Climate Entity**: Native MQTT climate discovery registering target setpoint and action status.

---

<div align="center">

## 6. Smart Motion Sensor Retrofit Appliance (`iot/smart_motion_sensor/`)

</div>

Hardware and software retrofit converting conventional analog PIR sensors into intelligent IoT occupancy nodes.

<div align="center">

### Capabilities & Source Files

</div>

- `smart_motion_sensor.ino` — Event-driven Arduino sketch with low-latency MQTT state publishing and auto-discovery.
- `config.h` — Digital input pins for PIR and microwave radar, ADC channels for LDR and battery divider.
- `motion_detector.h` / `motion_detector.cpp` — Anti-chatter debouncer, 30-second occupancy hold timer, lux and battery gauge calculations.
- **Dual-Tech Fusion**: Evaluates both passive infrared and microwave radar signals to eliminate false triggers.
- **Home Assistant Multi-Entity Registration**: Auto-registers motion binary sensor, tamper alert, illuminance sensor, and battery percentage.
