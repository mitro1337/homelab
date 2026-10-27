# Vigolium (guest 102)

Vigolium is a self-hosted vulnerability scanner recorded in the x64 Proxmox inventory as LXC guest 102. This repository documents the service at the operator's request; it does not currently track the guest's Proxmox `.conf` file or a Vigolium Compose manifest.

## What it does

Vigolium provides two scanning modes:

- **Native scan:** a modular, multi-phase scanner for web applications and APIs. Its workflow can include content discovery, browser-based spidering, and active or passive vulnerability checks.
- **Agentic scan:** AI-assisted workflows that can plan scanning tasks, select modules, run scans, and triage findings. The upstream project also provides source-code audit workflows.

The upstream project documents support for URL targets and inputs such as OpenAPI specifications, raw HTTP requests, and other common scanner formats. It can produce HTML reports and provides a server mode with traffic ingestion.

## Deployment and operations

The upstream project publishes a Docker image, `j3ssie/vigolium:latest`, and documents other installation methods. The repository does not specify how the instance in guest 102 is installed or configured.

The following operational details are not recorded here and should be checked on the live guest: IP address or DNS name, listening ports, reverse-proxy route, API authentication key, AI provider and model, scan scope, and data or report storage locations. Do not commit API keys, provider credentials, session material, or populated environment files.

Use the service only to assess systems for which you have authorization. The upstream documentation warns that agent mode is not sandboxed and that extensions can execute arbitrary commands. Keep the guest and its scan scope isolated appropriately, especially when handling untrusted targets or extensions.

## References

- [Vigolium source repository](https://github.com/vigolium/vigolium)
- [Vigolium documentation](https://docs.vigolium.com/)
- [Upstream security guidance](https://github.com/vigolium/vigolium#security)
