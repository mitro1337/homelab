# x64 Proxmox guests

This directory documents the Proxmox guests on the x64 node. Guest IDs and names reflect the operator's inventory. Tracked files are configuration records; they do not by themselves confirm a guest or service is currently running.

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

## Tracked application configuration

- **Home Assistant (100):** Docker Compose manifest in `homeassistant/docker-compose.yml`.
- **Monitoring (104):** Compose stack and Prometheus scrape configuration.
- **OWASP (105):** Compose definition for OWASP Juice Shop, an intentionally vulnerable training application.
- **Wazuh (106):** `wazuh.conf`; application deployment is managed inside the guest.
- **Immich (109):** Compose stack and `.env.example`; see [the Immich notes](immich/README.md).
- **Vigolium (102):** Service notes are in [vigolium/README.md](vigolium/README.md). The Proxmox guest definition and application deployment manifest are not currently tracked in this repository.

The other LXC guest folders contain Proxmox definitions; application configuration for Mosquitto, Nextcloud, and ESPHome is managed inside those guests and is not represented by Compose manifests here. QEMU VM files are Proxmox definitions, not Docker Compose services.

## Applying configuration

Compose manifests are scoped to the guest directories that contain them. Run them on the system that hosts the corresponding application and review any environment requirements first. The repository does not contain a root-level aggregate Compose file.

For guest-level settings, consult the tracked `.conf` files where available. The Vigolium guest is included in the inventory based on the operator's current node view; its Proxmox definition is not checked into this repository. Do not infer guest addresses, ports, or runtime status from this inventory.
