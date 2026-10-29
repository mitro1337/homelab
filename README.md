# Workbench

This repository contains configuration and documentation for my personal workbench.

## Repository layout

| Path | Contents |
| --- | --- |
| `services/x64/` | Proxmox guest inventory and selected service configurations. |
| `terraform/` | Proxmox resources and reusable infrastructure modules. |
| `ansible/` | Inventories, playbooks, and host roles. |
| `cloud/` | AWS, Azure, and Google Cloud configurations. |
| `iot/` | Firmware and device projects. |
| `cyber/` | Defensive tooling, CTF work, incident analysis, and vulnerability research. |
| `hardware/` | Physical host and device specifications. |

## Hardware

| Host | Role | Main hardware |
| --- | --- | --- |
| `pve` | Proxmox VE | Intel Core i3-10100F, 12 GB RAM, GTX 1050 Ti, 512 GB NVMe. |
| `openmediavault` | Storage | Intel Celeron N2830, 2 GB RAM, 500 GB SATA disk. |
| `kubernetes` | Kubernetes worker | AMD Athlon II X2 220, 4 GB RAM, 80 GB SATA disk. |


## x64 Proxmox guests

| ID | Guest | Type | Directory |
| ---: | --- | --- | --- |
| 100 | Home Assistant | LXC | `services/x64/homeassistant/` |
| 101 | Mosquitto | LXC | `services/x64/mosquitto/` |
| 102 | Vigolium | LXC | `services/x64/vigolium/` |
| 104 | Monitoring | LXC | `services/x64/monitoring/` |
| 105 | OWASP | LXC | `services/x64/owasp/` |
| 106 | Wazuh | LXC | `services/x64/wazuh/` |
| 107 | Nextcloud | LXC | `services/x64/nextcloud/` |
| 108 | ESPHome | LXC | `services/x64/esphome/` |
| 109 | Immich | LXC | `services/x64/immich/` |
| 200 | OPNsense | QEMU VM | `services/x64/opnsense/` |
| 300 | Parrot | QEMU VM | `services/x64/parrot/` |
| 301 | Sandbox | QEMU VM | `services/x64/sandbox/` |
| 400 | Domain Controller | QEMU VM | `services/x64/dc/` |
| 401 | Server 1 | QEMU VM | `services/x64/sv1/` |
| 402 | Server 2 | QEMU VM | `services/x64/sv2/` |
| 403 | Active Directory Client | QEMU VM | `services/x64/client/` |
| 405 | Red Hat Enterprise Linux | QEMU VM | `services/x64/rhel/` |

See the [x64 inventory](services/x64/README.md) for tracked guest and application files. VM definitions are Proxmox configuration, not Docker Compose services. Vigolium (102) is listed in the operator inventory, but its guest definition and deployment manifest are not tracked here.

## Starting a Compose stack

Run Compose from the service directory on the system that hosts the application:

```sh
cd services/x64/service
docker compose up -d
```

Use the same approach for other tracked stacks. For Immich, create a local `.env` from `.env.example` and set the required storage and database values. Do not commit secrets or populated environment files.

## Cybersecurity material

The `cyber/` directory contains CTF writeups, defensive tooling, incident records, and vulnerability research. Run proof-of-concept or intentionally vulnerable material only in isolated environments where you have authorization.

## Secrets and changes

Review Terraform and Ansible files before applying them. Supply credentials through each tool's expected local mechanism. Do not commit passwords, tokens, private keys, generated state, or populated `.env` files.
