# Stack: dockhand

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `dockhand/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: no
- README: no

## Project Status

- Runtime: stopped
- Project status: in progress
- Last verified: 2026-07-04

## Remaining Tasks

- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.
- Inspect `docker compose ps` and service logs before marking the runtime operational.

## Evidence

- Compose file: `dockhand/docker-compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: no
- Git status for stack path: clean
- No services are currently listed by `docker compose ps`.

## Services

- `dockhand`

## Images

- `fnsys/dockhand:latest`

## Operations

```bash
cd /home/ethan/docker/dockhand
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
