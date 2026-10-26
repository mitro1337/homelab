# x64 Infrastructure Inventory

This document records the current x64 Proxmox guest definitions tracked in [services/x64/](services/x64/). It does not infer runtime status, IP addresses, or resource allocations from guest names.

| ID | Display name | Proxmox type | Tracked configuration |
| ---: | --- | --- | --- |
| 100 | Home Assistant | LXC | homeassistant/100.conf, homeassistant/docker-compose.yml |
| 101 | Mosquitto | LXC | mosquitto/101.conf |
| 104 | Monitoring | LXC | monitoring/104.conf, monitoring/docker-compose.yml, monitoring/prometheus.yml |
| 105 | OWASP | LXC | owasp/105.conf, owasp/docker-compose.yml |
| 106 | Wazuh | LXC | wazuh/106.conf, wazuh/wazuh.conf |
| 107 | Nextcloud | LXC | nextcloud/107.conf |
| 108 | ESPHome | LXC | esphome/108.conf |
| 109 | Immich | LXC | immich/109.conf, immich/docker-compose.yml |
| 200 | OPNsense | QEMU VM | opnsense/200.conf |
| 300 | Parrot | QEMU VM | parrot/300.conf |
| 301 | Sandbox | QEMU VM | sandbox/301.conf |
| 400 | DC | QEMU VM | dc/400.conf |
| 401 | SV1 | QEMU VM | sv1/401.conf |
| 402 | SV2 | QEMU VM | sv2/402.conf |
| 403 | Active Directory client | QEMU VM | client/403.conf |
| 405 | RHEL | QEMU VM | rhel/405.conf |

Guest configuration files and service manifests are maintained under [services/x64/](services/x64/). Docker Compose is used only for application stacks; Proxmox VMs are represented by their QEMU configuration files.
