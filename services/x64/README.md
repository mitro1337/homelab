# x64 guests

Proxmox guest inventory and selected application configuration. Tracked configuration does not confirm runtime status.

## Guest inventory

| ID | Name | Type | Tracked directory |
| ---: | --- | --- | --- |
| 100 | Home Assistant | LXC | [homeassistant/](homeassistant/) |
| 101 | Mosquitto | LXC | [mosquitto/](mosquitto/) |
| 102 | Vigolium | LXC | [vigolium/](vigolium/) |
| 104 | Monitoring (Prometheus, Grafana and Loki) | LXC | [monitoring/](monitoring/) |
| 105 | OWASP | LXC | [owasp/](owasp/) |
| 106 | Wazuh | LXC | [wazuh/](wazuh/) |
| 107 | Nextcloud | LXC | [nextcloud/](nextcloud/) |
| 108 | ESPHome | LXC | [esphome/](esphome/) |
| 109 | Immich | LXC | [immich/](immich/) |
| 200 | OPNsense | QEMU VM | [opnsense/](opnsense/) |
| 300 | Parrot | QEMU VM | [parrot/](parrot/) |
| 301 | Sandboxed Windows 10 for Malware Analysis | QEMU VM | [sandbox/](sandbox/) |
| 400 | Domain Controller - Windows Server 2022 | QEMU VM | [dc/](dc/) |
| 401 | Server 1 - Windows Server 2016 | QEMU VM | [sv1/](sv1/) |
| 402 | Server 2 - Windows Server 2012 R2 | QEMU VM | [sv2/](sv2/) |
| 403 | Active Directory Client - Windows 10 LTSC IoT | QEMU VM | [client/](client/) |
| 405 | Red Hat Enterprise Linux | QEMU VM | [rhel/](rhel/) |

## Service notes

- Home Assistant (100), Monitoring (104), OWASP (105), and Immich (109) have tracked application files.
- Vigolium (102) has service notes, but no tracked guest definition or deployment manifest.
- QEMU VM files are Proxmox definitions, not Compose services. Other LXC application settings are managed inside the guests.
- [Immich notes](immich/README.md) and [Vigolium notes](vigolium/README.md).
