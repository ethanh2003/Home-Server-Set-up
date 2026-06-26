# home-assistant/README.md

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

# Home Assistant

Docker Compose-managed Home Assistant stack for this homelab.

## Layout

- `docker-compose.yml` runs Home Assistant, Mosquitto, Ring MQTT, and the Matter server.
- `config/homeassistant/` is the live Home Assistant configuration bind-mounted to `/config`.
- `config/mosquitto/`, `config/ring-mqtt/`, and `config/matter-server/` are live service data/config directories.
- `scripts/` contains backup, validation, deploy, restart, logs, and rollback helpers.
- `docs/` contains the runbook and conventions.

Runtime state, databases, logs, `.storage`, `.env`, and `secrets.yaml` are intentionally ignored by Git.

## Common Commands

```bash
./scripts/ha-backup.sh
./scripts/ha-validate.sh
./scripts/ha-deploy.sh
./scripts/ha-restart.sh
./scripts/ha-logs.sh 200
./scripts/ha-status.sh
./scripts/ha-rollback.sh /home/ethan/docker/home-assistant/backups/manual/YYYYmmdd-HHMMSS
```

Run commands from `/home/ethan/docker/home-assistant`.
