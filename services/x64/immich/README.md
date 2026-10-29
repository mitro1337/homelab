# Immich

Immich is tracked as an application stack for LXC guest 109. The directory contains the guest definition, Compose file, and .env.example.

Copy .env.example to .env, set the database password and host storage paths, and keep the populated file private. Review the bind mounts before starting.

Run from this directory on the application host: docker compose up -d. Inspect with docker compose ps and docker compose logs -f.
