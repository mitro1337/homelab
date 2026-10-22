<div align="center">

# Hardware Pinouts, Wiring & Electrical Interfaces

</div>

**Platform Architect**: Moană Ștefănuț-Cornel ([@stefanutc1](https://github.com/stefanutc1))  
**Hardware Fleet**: Espressif ESP32-WROOM-32D (Dual-Core Xtensa LX6 @ 240 MHz, 520 KB SRAM, 4 MB Flash)  
**Operating Voltage**: 3.3V Logic (5V tolerant with level shifting / optocoupler isolation)  

---

<div align="center">

## 1. Master GPIO Assignment Matrix

</div>

To guarantee zero pin contention and prevent peripheral collisions during development and maintenance, all GPIO assignments are cataloged across the fleet:

| Node ID & Project | Peripheral / Function | GPIO Pin | Signal Type | Electrical Specification | Default State / Protection |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **ESP32-EDGE-01** (`footprint`) | Fingerprint UART2 RX | `GPIO 16` | Digital Input | 3.3V UART (RX2) from R307/R504 | Hardware Serial2 (57600 baud) |
| **ESP32-EDGE-01** (`footprint`) | Fingerprint UART2 TX | `GPIO 17` | Digital Output | 3.3V UART (TX2) to R307/R504 | Hardware Serial2 |
| **ESP32-EDGE-01** (`footprint`) | Ultrasonic Trigger | `GPIO 5` | Digital Output | 3.3V Pulse (10 µs) to HC-SR04 | Driven LOW |
| **ESP32-EDGE-01** (`footprint`) | Ultrasonic Echo | `GPIO 18` | Digital Input | Voltage Divider 5V -> 3.3V (1kΩ / 2kΩ) | Pulse width measurement |
| **ESP32-EDGE-01** (`footprint`) | PIR Presence Sensor | `GPIO 27` | Digital Input | 3.3V Logic from HC-SR501 | Pulled LOW (Internal) |
| **ESP32-EDGE-01** (`footprint`) | Solenoid Gate Relay | `GPIO 26` | Digital Output | Transistor Driver / Optocoupled Relay | Active HIGH (1,500 ms max pulse) |
| **ESP32-EDGE-01** (`footprint`) | OLED Display I2C SDA | `GPIO 21` | Digital Bidirectional | I2C Data (400 kHz) | 4.7 kΩ Pull-up to 3.3V |
| **ESP32-EDGE-01** (`footprint`) | OLED Display I2C SCL | `GPIO 22` | Digital Output | I2C Clock (400 kHz) | 4.7 kΩ Pull-up to 3.3V |
| **ESP32-EDGE-02** (`irrigation`) | Solenoid Valve Zone 1 | `GPIO 23` | Digital Output | Optocoupled Relay Driver (Lawn Front) | Active LOW (Failsafe: HIGH) |
| **ESP32-EDGE-02** (`irrigation`) | Solenoid Valve Zone 2 | `GPIO 22` | Digital Output | Optocoupled Relay Driver (Lawn Back) | Active LOW (Failsafe: HIGH) |
| **ESP32-EDGE-02** (`irrigation`) | Solenoid Valve Zone 3 | `GPIO 21` | Digital Output | Optocoupled Relay Driver (Garden Beds) | Active LOW (Failsafe: HIGH) |
| **ESP32-EDGE-02** (`irrigation`) | Solenoid Valve Zone 4 | `GPIO 19` | Digital Output | Optocoupled Relay Driver (Greenhouse) | Active LOW (Failsafe: HIGH) |
| **ESP32-EDGE-02** (`irrigation`) | Soil Moisture ADC 1 | `GPIO 34` | Analog Input | Capacitive Probe (0 – 3.0V DC) | ADC1 Channel 6 (`ADC_ATTEN_DB_11`) |
| **ESP32-EDGE-02** (`irrigation`) | Soil Moisture ADC 2 | `GPIO 35` | Analog Input | Capacitive Probe (0 – 3.0V DC) | ADC1 Channel 7 (`ADC_ATTEN_DB_11`) |
| **ESP32-EDGE-02** (`irrigation`) | Rain Sensor Digital | `GPIO 32` | Digital Input | Precipitation Comparator Module | Active LOW on rain |
| **ESP32-EDGE-02** (`irrigation`) | Flow Meter Pulse | `GPIO 33` | Digital Input | YF-S201 Hall Turbine (Interrupt) | `FALLING` Edge ISR Counter |
| **ESP32-EDGE-03** (`datacenter_env`) | BME280 I2C SDA | `GPIO 21` | Digital Bidirectional | I2C Bus Data | 4.7 kΩ Pull-up to 3.3V |
| **ESP32-EDGE-03** (`datacenter_env`) | BME280 I2C SCL | `GPIO 22` | Digital Output | I2C Bus Clock | 4.7 kΩ Pull-up to 3.3V |
| **ESP32-EDGE-03** (`datacenter_env`) | DS18B20 1-Wire Data | `GPIO 4` | Digital Bidirectional | Dallas 1-Wire Bus (Intake & Exhaust) | 4.7 kΩ Pull-up to 3.3V |
| **ESP32-EDGE-03** (`datacenter_env`) | Noctua Fan PWM Out | `GPIO 18` | Digital Output (PWM) | 25 kHz High-Frequency PWM (Timer 0) | Duty Cycle: 25% – 100% |
| **ESP32-EDGE-03** (`datacenter_env`) | Fan Tachometer RPM | `GPIO 19` | Digital Input | Open-Collector Tachometer | Pull-up to 3.3V · Interrupt Counter |
| **ESP32-EDGE-04** (`power_monitor`) | 230V AC Grid Cut | `GPIO 25` | Digital Input | PC817 Optocoupler Zero-Latency Int | `CHANGE` Edge ISR (<10ms trigger) |
| **ESP32-EDGE-04** (`power_monitor`) | 12V SLA Battery ADC | `GPIO 36` | Analog Input | Resistive Divider (100kΩ / 22kΩ) | ADC1 Channel 0 (0 – 15.0V range) |
| **ESP32-EDGE-04** (`power_monitor`) | INA219 I2C SDA | `GPIO 21` | Digital Bidirectional | DC Voltage & Current Monitor | 4.7 kΩ Pull-up to 3.3V |
| **ESP32-EDGE-04** (`power_monitor`) | INA219 I2C SCL | `GPIO 22` | Digital Output | DC Voltage & Current Monitor | 4.7 kΩ Pull-up to 3.3V |
| **ESP32-EDGE-04** (`power_monitor`) | Buzzer Alarm | `GPIO 18` | Digital Output | Active Piezo Buzzer Driver | High-Pitch Alert on Battery < 11.4V |
| **ESP32-EDGE-05** (`smart_thermostat`) | DHT22 Data Bus | `GPIO 4` | Digital Bidirectional | AM2302 Single-Wire Protocol | 10 kΩ Pull-up to 3.3V |
| **ESP32-EDGE-05** (`smart_thermostat`) | Heat Relay (W1) | `GPIO 25` | Digital Output | Optocoupled Relay Board | Active LOW (3 min anti-cycle) |
| **ESP32-EDGE-05** (`smart_thermostat`) | Cool Relay (Y1) | `GPIO 26` | Digital Output | Optocoupled Relay Board | Active LOW (3 min anti-cycle) |
| **ESP32-EDGE-05** (`smart_thermostat`) | Fan Relay (G) | `GPIO 27` | Digital Output | Optocoupled Relay Board | Active LOW |
| **ESP32-EDGE-05** (`smart_thermostat`) | Temp Up Button | `GPIO 32` | Digital Input | Tactile Pushbutton | Internal Pull-Up · Active LOW |
| **ESP32-EDGE-05** (`smart_thermostat`) | Temp Down Button | `GPIO 33` | Digital Input | Tactile Pushbutton | Internal Pull-Up · Active LOW |
| **ESP32-EDGE-06** (`smart_motion`) | PIR Sensor Digital | `GPIO 13` | Digital Input | HC-SR501 / AM312 Output | 3.3V Logic · Active HIGH |
| **ESP32-EDGE-06** (`smart_motion`) | Microwave Radar Out | `GPIO 27` | Digital Input | RCWL-0516 Doppler Sensor Output | 3.3V Logic · Active HIGH |
| **ESP32-EDGE-06** (`smart_motion`) | LDR Light ADC | `GPIO 34` | Analog Input | GL5528 Photoresistor + 10kΩ Divider | ADC1 Channel 6 (0 – 1000 Lux) |
| **ESP32-EDGE-06** (`smart_motion`) | 18650 Battery ADC | `GPIO 35` | Analog Input | 1:1 Divider (100kΩ / 100kΩ) | ADC1 Channel 7 (0 – 4.2V Range) |

---

<div align="center">

## 2. Voltage Scaling & ADC Calibration

</div>

The ESP32 integrated ADC exhibits non-linearity near the lower ($<0.15\text{V}$) and upper ($>3.1\text{V}$) boundaries. All analog telemetry channels use 11 dB attenuation (`ADC_ATTEN_DB_11`) and software calibration curves:

### 12V Lead-Acid Battery Voltage Divider (`power_monitor`)
$$\text{Ratio} = \frac{R_2}{R_1 + R_2} = \frac{22\text{k}\Omega}{100\text{k}\Omega + 22\text{k}\Omega} = \frac{22}{122} \approx 0.1803$$
$$V_{\text{battery}} = V_{\text{ADC}} \times \left(\frac{100\text{k}\Omega + 22\text{k}\Omega}{22\text{k}\Omega}\right) \times K_{\text{cal}} = V_{\text{ADC}} \times 5.545$$

- Safe Battery Voltage: $12.6\text{V} - 13.8\text{V}$ (Float)
- Low Battery Warning: $11.8\text{V}$ (Alert dispatched via MQTT)
- Critical Shutdown Trigger: $11.4\text{V}$ (Emergency Proxmox shutdown webhook triggered immediately)

### 18650 Li-ion Cell Voltage Divider (`smart_motion_sensor`)
$$\text{Ratio} = \frac{100\text{k}\Omega}{100\text{k}\Omega + 100\text{k}\Omega} = 0.500$$
$$V_{\text{battery}} = V_{\text{ADC}} \times 2.000$$

- Fully Charged: $4.20\text{V}$ ($100\%$)
- Nominal: $3.70\text{V}$ ($50\%$)
- Cut-off / Recharge: $3.20\text{V}$ ($0\%$)
