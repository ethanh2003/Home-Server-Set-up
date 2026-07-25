# Stack: Minecraft

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `Minecraft/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: yes
- README: no

## Project Status

- Runtime: running
- Project status: needs docs
- Last verified: 2026-07-04

## Remaining Tasks

- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

## Evidence

- Compose file: `Minecraft/docker-compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: yes
- Git status for stack path: clean
- `mc`: running (healthy)

## Services

- `mc`

## Images

- `itzg/minecraft-server`

## Operations

```bash
cd /home/ethan/docker/Minecraft
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
