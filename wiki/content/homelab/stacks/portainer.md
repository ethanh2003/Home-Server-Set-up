# Stack: portainer

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `portainer/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: no
- README: no

## Project Status

- Runtime: running
- Project status: needs docs
- Last verified: 2026-07-04

## Remaining Tasks

- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

## Evidence

- Compose file: `portainer/docker-compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: no
- Git status for stack path: clean
- `portainer`: running
- `portainer_agent`: running

## Services

- `portainer`
- `portainer_agent`

## Images

- `portainer/agent:latest`
- `portainer/portainer-ce:latest`

## Operations

```bash
cd /home/ethan/docker/portainer
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
