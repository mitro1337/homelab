<div align="center">

# Home Assistant & MQTT Integration Architecture

</div>

**Broker**: Eclipse Mosquitto (`192.168.20.100:1883`)  
**Network**: VLAN 50 (IoT Microcontrollers) -> VLAN 20 (Home Assistant & Mosquitto)  
**Discovery Prefix**: `homeassistant/`  
**Base Topic**: `homelab/`  

---

<div align="center">

## 1. MQTT Topic Taxonomy

</div>

All edge devices follow a standardized topic hierarchy with explicit availability (Last Will & Testament) channels:

```text
homelab/
├── access/
│   └── gate/
│       ├── event             # JSON: {"event": "biometric_grant", "finger_id": 1}
│       ├── command           # "OPEN"
│       └── status            # "online" / "offline" (LWT)
├── irrigation/
│   ├── zone1/state           # "ON" / "OFF"
│   ├── zone1/set             # Command: "ON" / "OFF"
│   ├── telemetry             # JSON: {"zone1_moisture": 42, "flow_lpm": 12.4}
│   └── status                # "online" / "offline" (LWT)
├── environment/
│   ├── telemetry             # JSON: {"temp": 24.2, "humidity": 45.1, "fan_rpm": 1420}
│   └── status                # "online" / "offline" (LWT)
├── power/
│   ├── grid_status           # "NORMAL" / "OUTAGE"
│   ├── telemetry             # JSON: {"battery_volts": 12.8, "current_amps": 1.4}
│   └── status                # "online" / "offline" (LWT)
├── climate/
│   └── thermostat/
│       ├── state             # JSON: {"temperature": 21.5, "target_temperature": 22.0, "mode": "heat", "action": "heating"}
│       ├── set               # JSON: {"target_temperature": 22.5, "mode": "heat"}
│       └── status            # "online" / "offline" (LWT)
└── sensors/
    └── motion/
        ├── state             # JSON: {"occupancy": true, "radar": true, "pir": true, "lux": 240, "battery": 92}
        ├── tamper            # "CLEAR" / "TRIGGERED"
        └── status            # "online" / "offline" (LWT)
```

---

<div align="center">

## 2. Home Assistant Auto-Discovery Payloads

</div>

When booting, each ESP32 broadcasts an MQTT discovery payload to `homeassistant/<component>/<node_id>/<object_id>/config` with `retain: true`. Home Assistant automatically creates and manages the corresponding entities:

### Smart HVAC Climate Discovery (`smart_thermostat`)
- **Topic**: `homeassistant/climate/esp32_thermostat/config`
- **Payload**:
```json
{
  "name": "Smart Thermostat",
  "unique_id": "esp32_smart_thermostat_05",
  "current_temperature_topic": "homelab/climate/thermostat/state",
  "current_temperature_template": "{{ value_json.temperature }}",
  "temperature_command_topic": "homelab/climate/thermostat/set/target_temp",
  "temperature_state_topic": "homelab/climate/thermostat/state",
  "temperature_state_template": "{{ value_json.target_temperature }}",
  "mode_command_topic": "homelab/climate/thermostat/set/mode",
  "mode_state_topic": "homelab/climate/thermostat/state",
  "mode_state_template": "{{ value_json.mode }}",
  "modes": ["off", "heat", "cool"],
  "action_topic": "homelab/climate/thermostat/state",
  "action_template": "{{ value_json.action }}",
  "min_temp": 15.0,
  "max_temp": 30.0,
  "temp_step": 0.5,
  "availability_topic": "homelab/climate/thermostat/status",
  "device": {
    "identifiers": ["esp32_smart_thermostat_05"],
    "name": "ESP32 HVAC Controller",
    "model": "ESP32-WROOM-32D",
    "manufacturer": "Moana Stefanut-Cornel"
  }
}
```

### Smart Motion Sensor Discovery (`smart_motion_sensor`)
- **Topic**: `homeassistant/binary_sensor/esp32_motion_sensor/config`
- **Payload**:
```json
{
  "name": "Room Occupancy",
  "unique_id": "esp32_motion_sensor_occupancy",
  "state_topic": "homelab/sensors/motion/state",
  "value_template": "{{ 'ON' if value_json.occupancy else 'OFF' }}",
  "device_class": "occupancy",
  "availability_topic": "homelab/sensors/motion/status",
  "device": {
    "identifiers": ["esp32_smart_motion_06"],
    "name": "ESP32 Smart Motion Retrofit",
    "model": "ESP32-WROOM-32D",
    "manufacturer": "Moana Stefanut-Cornel"
  }
}
```

---

<div align="center">

## 3. Prometheus HTTP Exporter Scraping

</div>

For high-resolution time-series monitoring, nodes `ESP32-EDGE-03` and `ESP32-EDGE-04` host lightweight embedded HTTP servers on port 80 outputting standard Prometheus text metrics:

```yaml
# Prometheus scrape configuration (CT 104)
scrape_configs:
  - job_name: "esp32_edge_telemetry"
    scrape_interval: 15s
    scrape_timeout: 5s
    static_configs:
      - targets:
          - "192.168.50.23:80"  # Rack Thermals (datacenter_environment)
          - "192.168.50.24:80"  # Mains & Battery Monitor (power_monitor)
        labels:
          vlan: "50"
          architecture: "esp32_bare_metal"
```
