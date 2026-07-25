# Stack: dockhand

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `dockhand/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: no
- README: no

## Project Status

- Runtime: not checked
- Project status: needs docs
- Last verified: 2026-07-04

## Remaining Tasks

- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

## Evidence

- Compose file: `dockhand/docker-compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: no
- Git status for stack path: omitted
- Live runtime state is monitored in Prometheus and omitted from deterministic wiki output.

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
