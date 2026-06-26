# Stack: home-assistant

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `home-assistant/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: yes
- README: yes

## Services

- `home-assistant`
- `mosquitto`
- `ring-mqtt`
- `matter-server`

## Images

- `eclipse-mosquitto:latest`
- `ghcr.io/home-assistant-libs/python-matter-server:stable`
- `ghcr.io/home-assistant/home-assistant:stable`
- `tsightler/ring-mqtt:latest`

## Operations

```bash
cd /home/ethan/docker/home-assistant
docker compose config
docker compose ps
```

## Notes

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
