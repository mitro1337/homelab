# Immich

Immich is tracked as an application stack for Proxmox LXC guest 109.

## Files

- `109.conf` — Proxmox guest definition.
- `docker-compose.yml` — Immich server, machine-learning service, Redis, and PostgreSQL database.
- `.env.example` — example variables consumed by the Compose file.

## Configuration

Copy `.env.example` to `.env` and set the database password and storage locations for the host before starting the stack. The Compose file mounts the upload location into the Immich server and the database data location into PostgreSQL. Keep `.env` private and do not commit populated credentials.

The database image in the Compose file is PostgreSQL 14 with `pgvecto-rs`. The server exposes port 2283. Other containers communicate through the Compose network.

## Start and inspect

Run these commands on the system hosting the application, from this directory:

```sh
docker compose up -d
docker compose ps
docker compose logs -f
```

Review `docker-compose.yml` and the configured bind-mount paths before starting the stack. This repository tracks configuration; it does not indicate whether the service is currently running.
