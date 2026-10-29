# Vulnerability research

This directory contains reports and remediation notes for Proxmox VE, Hyper-V, Windows DNS, and Windows DHCP. Verify affected versions and fixes against vendor advisories before applying changes.

| Advisory | Component | Report | Fix |
| --- | --- | --- | --- |
| **CVE-2023-54391** | Proxmox VE (`libpve-access-control` < 8.0.4) | [Technical Report](./CVE-2023-54391/report.md) | [Hardening Plan](./CVE-2023-54391/fix.md) |
| **CVE-2025-57539** | Proxmox VE 8.4 (`pve-manager` / ExtJS GUI) | [Technical Report](./CVE-2025-57539/report.md) | [Hardening Plan](./CVE-2025-57539/fix.md) |
| **CVE-2026-69603** / **CVE-2026-80083** | Windows Hyper-V Virtualization Stack | [Technical Report](./CVE-2026-69603-CVE-2026-80083/report.md) | [Hardening Plan](./CVE-2026-69603-CVE-2026-80083/fix.md) |
| **CVE-2026-69730** | Windows DNS Server Service (`dns.exe`) | [Technical Report](./CVE-2026-69730/report.md) | [Hardening Plan](./CVE-2026-69730/fix.md) |
| **CVE-2026-69845** / **CVE-2026-72979** | Windows DHCP Server Service (`dhcpssvc.dll`) | [Technical Report](./CVE-2026-69845-CVE-2026-72979/report.md) | [Hardening Plan](./CVE-2026-69845-CVE-2026-72979/fix.md) |
