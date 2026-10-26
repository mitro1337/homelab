# x64 Services and Manifests

This catalog lists application manifests tracked under [services/x64/](services/x64/). It reflects repository files, not live service status.

| Guest ID | Guest | Tracked application configuration |
| ---: | --- | --- |
| 100 | Home Assistant | [Docker Compose](services/x64/homeassistant/docker-compose.yml) |
| 101 | Mosquitto | Proxmox guest definition only |
| 104 | Monitoring | [Docker Compose](services/x64/monitoring/docker-compose.yml), [Prometheus configuration](services/x64/monitoring/prometheus.yml) |
| 105 | OWASP | [Docker Compose](services/x64/owasp/docker-compose.yml) |
| 106 | Wazuh | [Wazuh configuration](services/x64/wazuh/wazuh.conf); application managed in the guest |
| 107 | Nextcloud | Proxmox guest definition only |
| 108 | ESPHome | Proxmox guest definition only |
| 109 | Immich | [Docker Compose](services/x64/immich/docker-compose.yml) |
| 200, 300, 301, 400–403, 405 | OPNsense, Parrot, Sandbox, DC, SV1, SV2, Active Directory client, RHEL | QEMU VM definitions; no Docker Compose manifest |

Compose files are scoped to individual guests. There is no aggregate services/x64/docker-compose.yml, and VM definitions are not Compose services. Refer to the [x64 inventory](services/x64/README.md) for the full guest list.
