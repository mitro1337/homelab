# Homelab

This repository contains configuration, automation, and operational material for a personal homelab. It includes Proxmox guest definitions, service manifests, Terraform and Ansible code, cloud and Kubernetes configuration, IoT firmware, and cybersecurity research.

The repository describes intended or tracked configuration. A file being present here does not confirm that a machine, container, or application is currently running. For the current x64 Proxmox guest list, use the [x64 inventory](services/x64/README.md) and the corresponding guest configuration files.

## Contents

| Path | What it contains |
| --- | --- |
| `services/x64/` | Proxmox LXC and QEMU guest definitions and selected application manifests for the x64 node. |
| `terraform/` | Proxmox infrastructure configuration and reusable modules for VMs, LXC guests, network segments, SDN, and firewalling. |
| `ansible/` | Inventories, playbooks, and roles for host setup, services, networking, storage, security, and maintenance. |
| `cloud/` | Terraform configurations for AWS, Azure, and Google Cloud. |
| `kubernetes/` | Kubernetes and GitOps configuration, applications, and supporting automation. |
| `hypervisors/` | Terraform configurations for Proxmox and other hypervisor platforms. |
| `cyber/` | Defensive tooling, threat intelligence, incident analysis, CTF material, and vulnerability research. |
| `hardware/`, `inventory/` | Hardware notes and host inventory data. |
| `scripts/` | Administration, backup, health-check, audit, and recovery utilities. |
| `.github/workflows/` | GitHub Actions workflows for CI, CD, and chaos-related jobs. |

## Physical hardware

The hardware notes in [`hardware/hardware.md`](hardware/hardware.md) describe three physical hosts. The summary below keeps the main specifications near the Proxmox guest inventory. These are hardware records; they do not imply that every configured workload is currently online.

| Host | Role | Processor | Memory | Graphics | Storage | Network |
| --- | --- | --- | --- | --- | --- | --- |
| `pve` | Proxmox VE hypervisor | Intel Core i3-10100F, 4 cores / 8 threads | 12 GB DDR4-2666 | NVIDIA GeForce GTX 1050 Ti, 4 GB | 512 GB PCIe 3.0 NVMe | Realtek RTL8111H Gigabit Ethernet |
| `openmediavault` | Storage host | Intel Celeron N2830, 2 cores / 2 threads | 2 GB DDR3L-1333 | Intel HD Graphics | 500 GB 2.5-inch SATA HDD; ZFS pool `omv_tank` | Realtek RTL8101E Ethernet |
| `kubernetes` | Kubernetes worker host | AMD Athlon II X2 220, 2 cores / 2 threads | 4 GB DDR3-1066 | NVIDIA GeForce GTS 250, 1 GB | 80 GB 3.5-inch SATA HDD | Realtek Gigabit Ethernet |

### Host notes

- `pve` is the x64 Proxmox VE host. The hardware record lists a custom ATX chassis and Proxmox VE 9.2. Its inventory is documented in the [x64 Proxmox section](#current-x64-proxmox-inventory).
- `openmediavault` is an ASUS X451MA laptop used as a storage host. The hardware record lists an external 19 V / 2.37 A adapter and an internal battery buffer.
- `kubernetes` is a legacy ATX micro-tower. Its hardware record lists a 450 W power supply.
- The hardware source records `pve` at `192.168.1.132`. Check the live host configuration before relying on addresses or network assignments.
- IoT board and peripheral details are maintained with the firmware projects under [`iot/`](iot/).
## Current x64 Proxmox inventory

The tracked x64 inventory contains 16 guests. The names below follow the current Proxmox node view.

| ID | Name | Type | Directory |
| ---: | --- | --- | --- |
| 100 | Home Assistant | LXC | `services/x64/homeassistant/` |
| 101 | Mosquitto | LXC | `services/x64/mosquitto/` |
| 104 | Monitoring (Prometheus, Grafana and Loki) | LXC | `services/x64/monitoring/` |
| 105 | OWASP | LXC | `services/x64/owasp/` |
| 106 | Wazuh | LXC | `services/x64/wazuh/` |
| 107 | Nextcloud | LXC | `services/x64/nextcloud/` |
| 108 | ESPHome | LXC | `services/x64/esphome/` |
| 109 | Immich | LXC | `services/x64/immich/` |
| 200 | OPNsense | QEMU VM | `services/x64/opnsense/` |
| 300 | Parrot | QEMU VM | `services/x64/parrot/` |
| 301 | Sandboxed Windows 10 for Malware Analysis | QEMU VM | `services/x64/sandbox/` |
| 400 | DC | QEMU VM | `services/x64/dc/` |
| 401 | SV1 | QEMU VM | `services/x64/sv1/` |
| 402 | SV2 | QEMU VM | `services/x64/sv2/` |
| 403 | Active Directory client | QEMU VM | `services/x64/client/` |
| 405 | RHEL | QEMU VM | `services/x64/rhel/` |

Each guest directory contains its Proxmox `.conf` definition. Selected LXC guests also have application configuration. VM definitions are QEMU/Proxmox configuration files; they are not Docker Compose services. The x64 directory has no root-level aggregate `docker-compose.yml`.

### Tracked application manifests

| Guest | Files tracked for the application |
| --- | --- |
| Home Assistant (100) | `docker-compose.yml`; configuration is mounted from `homeassistant/config/`. |
| Monitoring (104) | Compose stack with Grafana, Prometheus, Loki, Promtail, and Node Exporter; Prometheus scrape configuration. |
| OWASP (105) | Compose definition for OWASP Juice Shop, an intentionally vulnerable training application. |
| Wazuh (106) | `wazuh.conf`; application deployment is managed inside the guest. |
| Immich (109) | Compose stack, `.env.example`, and a guest definition. See [`services/x64/immich/README.md`](services/x64/immich/README.md). |

Mosquitto, Nextcloud, and ESPHome have guest definitions in this directory; their application configuration is managed inside the guests and is not represented by a tracked Compose file here.

## Running a Compose stack

Compose manifests are scoped to a guest directory. Run Docker Compose from the relevant directory, on the system that hosts that guest's application:

```sh
cd services/x64/homeassistant
docker compose up -d
```

Use the same pattern for `monitoring`, `owasp`, or `immich`. The Immich stack needs a local `.env` based on the tracked `.env.example`; set the storage and database values for the host before starting it. Do not commit credentials or a populated `.env` file.

For a Proxmox guest, use its `.conf` file as the tracked configuration reference. Terraform and Ansible have their own inventories, examples, and playbooks; review those files before applying changes to a host or cloud account. This README does not prescribe applying every configuration in the repository.


## Cybersecurity material

The `cyber/` tree contains defensive and research material, including:

- tools and data for threat intelligence;
- incident and infrastructure analysis case files;
- CTF writeups and vulnerability reports;

Some directories contain proof-of-concept or intentionally vulnerable material. Use it only in systems and environments where you have authorization. Keep training targets isolated from trusted networks.


## Configuration and secrets

Templates and examples are provided for some tools, including Terraform variable files and service environment files. Supply local credentials through the mechanism expected by the specific tool. Do not commit passwords, API tokens, private keys, generated state files, or populated environment files.

## License

This repository is distributed under the GNU Affero General Public License v3.0. See [`LICENSE`](LICENSE).


