# Stack: arr-suite

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `arr-suite/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: yes
- README: no

## Project Status

- Runtime: partial
- Project status: in progress
- Last verified: 2026-07-04

## Remaining Tasks

- Keep dry-run-first acquisition workflows and approval artifacts for bulk Radarr changes.
- Continue live queue verification before any Jellyfin collection or cleanup work.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.
- Inspect `docker compose ps` and service logs before marking the runtime operational.

## Evidence

- Compose file: `arr-suite/docker-compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: yes
- Git status for stack path: untracked
- `gluetun`: running (unhealthy)
- `prowlarr`: running (healthy)
- `qbittorrent`: running (healthy)
- `radarr`: running (healthy)
- `sonarr`: running (healthy)

## Services

- `gluetun`
- `qbittorrent`
- `prowlarr`
- `radarr`
- `sonarr`

## Images

- `lscr.io/linuxserver/prowlarr:latest`
- `lscr.io/linuxserver/qbittorrent:latest`
- `lscr.io/linuxserver/radarr:latest`
- `lscr.io/linuxserver/sonarr:latest`
- `qmcgaw/gluetun:latest`

## Operations

```bash
cd /home/ethan/docker/arr-suite
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
