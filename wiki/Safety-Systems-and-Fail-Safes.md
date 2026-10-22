<div align="center">

# Safety Systems, Interlocks & Fail-Safe Architecture

</div>

**Platform Architect**: Moană Ștefănuț-Cornel ([@stefanutc1](https://github.com/stefanutc1))  
**Design Philosophy**: Autonomous Edge Survivability — zero dependency on central servers for basic safety.  

---

<div align="center">

## 1. Hardware Watchdog Timer (WDT)

</div>

To prevent edge node hangs due to memory fragmentation, network lockups, or peripheral bus stalls, every project initializes the hardware Task Watchdog Timer (`esp_task_wdt`):

```cpp
#include <esp_task_wdt.h>

#define WDT_TIMEOUT_SECONDS 8

void setup() {
    // Initialize Hardware WDT for 8 seconds
    esp_task_wdt_init(WDT_TIMEOUT_SECONDS, true);
    esp_task_wdt_add(NULL); // Subscribe current loop task
}

void loop() {
    // Core routine execution
    esp_task_wdt_reset(); // Feed watchdog
}
```

If the main event loop fails to feed the watchdog within 8 seconds, the SoC executes an immediate hardware reset, restoring operational state in $<800\text{ms}$.

---

<div align="center">

## 2. HVAC Compressor Anti-Cycle Protection (`smart_thermostat`)

</div>

Rapid cycling of air conditioning compressors causes excessive head pressure and motor burnout. The thermostat controller enforces a mandatory 3-minute (180s) minimum off-state lockout before re-engaging the cool relay:

- **Safety Guard**: `MIN_COMPRESSOR_OFF_TIME_MS = 180000`
- **State Verification**: Even if temperature rises above the cooling setpoint or the user overrides via Home Assistant, the relay remains locked open until the hardware timer expires.
- **Sensor NaN Cutoff**: If the DHT22 returns `NAN` for $>60\text{s}$, all relays (Heat, Cool, Fan) are forced to `OFF` immediately to prevent runaway heating or cooling.

---

<div align="center">

## 3. Irrigation Maximum Duration & Rain Interlock (`irrigation`)

</div>

To protect against valve driver failure, network disconnection during watering, or burst pipes, the irrigation controller implements a dual hardware fail-safe:

1. **Hardware Safety Timer**: No zone relay can remain active for more than **15 minutes (900 seconds)** under any circumstances. If an "OFF" MQTT command is dropped, the local firmware shuts off the zone automatically.
2. **Rain Interlock**: A dedicated hardware rain sensor pin acts as an electrical/logic gate. If active rain is detected, all solenoid valves are inhibited immediately regardless of schedule.

---

<div align="center">

## 4. Emergency Cluster Shutdown Trigger (`power_monitor`)

</div>

When mains power drops, battery depletion is non-linear. To prevent filesystem corruption across the Proxmox VE hypervisor and ZFS storage pools:

1. **AC Optocoupler Interrupt**: Detects 230V AC zero-crossing loss in $<10\text{ms}$.
2. **Voltage Tracking**: Samples SLA battery voltage every 500ms via calibrated ADC.
3. **Emergency Trigger (<11.4V)**:
   - Activates local high-decibel piezo buzzer alarm.
   - Dispatches authenticated REST call to Proxmox VE API: `POST /api2/json/nodes/pve/status` with `command=shutdown`.
   - Proxmox executes graceful shutdown sequence, flushing ZFS transaction groups and unmounting NFS before inverter shutoff.
