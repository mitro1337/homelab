# x64 Proxmox VE Inventory

This directory contains only the x64 Proxmox VE guests represented in the current node inventory.

| ID | Display name | Guest type | Directory | Application manifest |
| ---: | --- | --- | --- | --- |
| 100 | Home Assistant | LXC container | `homeassistant` | `homeassistant/docker-compose.yml` |
| 101 | Mosquitto | LXC container | `mosquitto` | Managed inside the guest |
| 104 | Monitoring | LXC container | `monitoring` | `monitoring/docker-compose.yml` |
| 105 | OWASP | LXC container | `owasp` | `owasp/docker-compose.yml` |
| 106 | Wazuh | LXC container | `wazuh` | Managed inside the guest |
| 107 | Nextcloud | LXC container | `nextcloud` | Managed inside the guest |
| 108 | ESPHome | LXC container | `esphome` | Managed inside the guest |
| 109 | Immich | LXC container | `immich` | `immich/docker-compose.yml` |
| 200 | OPNsense | QEMU virtual machine | `opnsense` | Not applicable |
| 300 | Parrot | QEMU virtual machine | `parrot` | Not applicable |
| 301 | Sandbox | QEMU virtual machine | `sandbox` | Not applicable |
| 400 | DC | QEMU virtual machine | `dc` | Not applicable |
| 401 | SV1 | QEMU virtual machine | `sv1` | Not applicable |
| 402 | SV2 | QEMU virtual machine | `sv2` | Not applicable |
| 403 | Active Directory client | QEMU virtual machine | `client` | Not applicable |
| 405 | RHEL | QEMU virtual machine | `rhel` | Not applicable |

## Configuration layout

The `.conf` files are Proxmox guest definitions. Docker Compose manifests are stored in the corresponding guest directories and describe applications running in those guests. Proxmox virtual machines are not Docker Compose services, so this directory does not have an aggregate `docker-compose.yml`.

Each guest directory contains an English README describing its role and tracked files.
