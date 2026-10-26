<div align="center">

# Hardware Fleet & Host Virtualization Specification

</div>

<div align="center">

[![Fleet](https://img.shields.io/badge/Hardware-3%20Bare--Metal%20Nodes%20%2B%204%20ESP32-0f172a.svg?style=flat&logo=serverfault)](#)
[![Primary Node](https://img.shields.io/badge/Hypervisor-Intel%20i3--10100F%20(12GB%20DDR4)-blue.svg?style=flat&logo=intel)](#host-proxmox-node-1--primary-hypervisor)
[![Storage Node](https://img.shields.io/badge/Storage-ASUS%20X451MA%20(ZFS%20NAS)-059669.svg?style=flat&logo=asus)](#host-openmediavault-node-2--storage-nas)
[![Edge Worker](https://img.shields.io/badge/Worker-AMD%20Athlon%20II%20X2%20(4GB%20DDR3)-8b5cf6.svg?style=flat&logo=amd)](#host-k8s-node-04-node-4--kubernetes-worker-node)
[![Edge IoT](https://img.shields.io/badge/Edge%20Fleet-6%20ESP32%20Bare--Metal%20Nodes-e7352c.svg?style=flat&logo=espressif)](../iot/README.md)
[![Author](https://img.shields.io/badge/Hardware%20Architect-Moan%C4%83%20%C8%98tef%C4%83nu%C8%9B--Cornel-blue.svg?style=flat&logo=github)](https://github.com/stefanutc1)
[![University](https://img.shields.io/badge/University-Universitatea%20din%20Craiova%20%C2%B7%20FEAA-0284c7.svg?style=flat&logo=academia)](https://feaa.ucv.ro)

</div>

---

<div align="center">

## Executive Summary

</div>

This document describes the physical host hardware, compute chassis, power delivery, thermal envelopes, and embedded microcontrollers underpinning the `stefanutc1/infrastructure` platform. It serves as the primary reference for hardware capacity budgeting, failure domain mapping, and bare-metal disaster recovery planning.

---

<div align="center">

## 1. Physical Compute Hosts

</div>

<div align="center">

### Host: `proxmox` (Node 1 — Primary Hypervisor `pve_primary_x64`)

</div>

<div align="center">

#### Hardware Specifications

</div>

| Component | Engineering Specification |
| :--- | :--- |
| **Chassis** | Custom ATX Bare-Metal Tower Chassis |
| **Processor (CPU)** | Intel Core i3-10100F (Comet Lake) — 4 Cores / 8 Threads @ 3.60 GHz (4.30 GHz Turbo, 6MB Cache) |
| **Dedicated GPU** | NVIDIA GeForce GTX 1050 Ti — 4 GB GDDR5 VRAM (PCIe Passthrough to CT 102) |
| **System Memory (RAM)** | 12 GB DDR4 (1x 8GB + 1x 4GB @ 2666 MHz, non-ECC) |
| **Primary Storage** | 512 GB PCIe 3.0 NVMe M.2 Solid State Drive (`local-lvm`) |
| **Network Interface** | 1x Realtek RTL8111H PCIe Gigabit Ethernet (RJ-45) |



<div align="center">

#### Software & Operating System

</div>
- **Hypervisor**: Proxmox VE 9.2 (Debian 12 base / Linux 6.8+ pve kernel).
- **Virtualization Engine**: QEMU/KVM 8.x + LXC unprivileged containerization.
- **Security Agent**: Wazuh Agent 4.14 + Prometheus Node Exporter.
- **Static IPv4**: `192.168.1.132` (VLAN 10 Management).

---

<div align="center">

### Host: `openmediavault` (Node 2 — Storage NAS `omv_nas`)

</div>

<div align="center">

#### Hardware Specifications

</div>

| Component | Engineering Specification |
| :--- | :--- |
| **Physical Machine** | ASUS X451MA Low-Power Laptop Server |
| **Processor (CPU)** | Intel Celeron N2830 (Bay Trail) — 2 Cores / 2 Threads @ 2.16 GHz (2.41 GHz Burst, 7.5W TDP) |
| **Integrated Graphics** | Intel HD Graphics (Bay Trail) |
| **System Memory (RAM)** | 2 GB DDR3L-1333 MHz SO-DIMM |
| **Primary Storage** | 500 GB 2.5" SATA II Mechanical HDD (ZFS Single-Disk Pool `omv_tank`) |
| **Network Interface** | 1x Realtek RTL8101E 100M/Gigabit Ethernet |
| **Power Supply Unit (PSU)** | External 19V / 2.37A (45W) AC Adapter with integrated Li-Ion battery buffer |

<div align="center">

### Host: `k8s-node-04` (Node 4 — Edge Kubernetes Worker)

</div>

<div align="center">

#### Hardware Specifications

</div>

| Component | Engineering Specification |
| :--- | :--- |
| **Chassis** | Custom ATX Legacy Micro-Tower Chassis |
| **Processor (CPU)** | AMD Athlon II X2 220 (Regor / Socket AM3) — 2 Cores / 2 Threads @ 2.80 GHz (65W TDP) |
| **Dedicated Graphics** | NVIDIA GeForce GTS 250 — 1 GB GDDR3 (256-bit bus, legacy compute) |
| **System Memory (RAM)** | 4 GB DDR3-1066 MHz (2x 2GB Dual-Channel) |
| **Primary Storage** | 80 GB 3.5" SATA II 7200 RPM HDD |
| **Network Interface** | 1x Realtek Gigabit Ethernet PCI-e Adapter |
| **Power Supply Unit (PSU)** | Standard ATX 450W Power Supply Unit |

<div align="center">

