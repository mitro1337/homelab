# Infrastructure

Infrastructure as code, Proxmox guest definitions, service configuration, and operational documentation for this homelab.

## Current x64 Proxmox inventory

The x64 node currently contains the 16 guests listed in [services/x64/README.md](services/x64/README.md): LXC containers 100, 101, 104–109; and QEMU virtual machines 200, 300, 301, 400–403, and 405.

The inventory README is the source of truth for guest IDs, display names, types, and tracked service manifests. In particular:

- CT 100 is Home Assistant.
- VM 403 is the Active Directory client.
- VM 404 is not part of the current inventory.
- Docker Compose files are kept with the guest application they configure. Proxmox VM definitions remain separate .conf files.

## Repository documentation

- [x64 Proxmox inventory](services/x64/README.md) — current guest list and configuration layout.
- [Architecture](ARCHITECTURE.md) — how the tracked x64 guest definitions are organized.
- [Infrastructure inventory](INFRASTRUCTURE.md) — guest IDs, names, and tracked files.
- [Services](SERVICES.md) — application manifests tracked for the x64 guests.
- [Network](NETWORK.md), [operations](OPERATIONS.md), [backup](BACKUP.md), and [disaster recovery](DISASTER-RECOVERY.md) — domain-specific plans and runbooks.
- [Security](SECURITY.md) and [contributing](CONTRIBUTING.md) — security and repository practices.

Service-level details belong beside the corresponding configuration. A guest's presence in the Proxmox inventory does not by itself assert that its application is currently running.


<!-- AUTO-METRICS-START -->
[![Active Workloads](https://img.shields.io/badge/Workloads-4%20Services-blue?style=flat&logo=docker)](https://stefanutc1.github.io/infrastructure/)
[![CI Pipeline](https://img.shields.io/badge/CI%20Pipeline-Passed%20(100%25)-brightgreen?style=flat&logo=githubactions)](https://github.com/stefanutc1/infrastructure/actions/workflows/ci.yml)
[![CD Pipeline](https://img.shields.io/badge/CD%20Pipeline-Active-blue?style=flat&logo=githubactions)](https://github.com/stefanutc1/infrastructure/actions/workflows/cd.yml)
[![Last Sync](https://img.shields.io/badge/Last%20Auto--Sync-2026--10--26-informational?style=flat&logo=githubactions)](https://github.com/stefanutc1/infrastructure/actions)
<!-- AUTO-METRICS-END -->
