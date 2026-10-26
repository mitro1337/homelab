# x64 Proxmox Architecture

## Scope

This document describes the x64 Proxmox guest definitions tracked under [services/x64/](services/x64/). The [inventory README](services/x64/README.md) is authoritative for the current guest IDs and names.

## Guest layout

The current inventory contains 16 guests:

- **LXC containers:** 100 Home Assistant, 101 Mosquitto, 104 Monitoring, 105 OWASP, 106 Wazuh, 107 Nextcloud, 108 ESPHome, and 109 Immich.
- **QEMU virtual machines:** 200 OPNsense, 300 Parrot, 301 Sandbox, 400 DC, 401 SV1, 402 SV2, 403 Active Directory client, and 405 RHEL.

Each guest has a Proxmox .conf definition. Application configuration, where tracked, is kept in that guest's directory. Compose manifests describe applications inside a guest; they do not replace Proxmox guest definitions.

## Tracked application manifests

The repository currently tracks Docker Compose manifests for Home Assistant (100), Monitoring (104), OWASP (105), and Immich (109). Wazuh also has a tracked wazuh.conf. Other guests have a Proxmox definition only in this directory.

These files document repository state. They do not guarantee that a guest or application is running or reachable.
