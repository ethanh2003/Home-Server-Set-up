# Stack: actual-budget

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `actual-budget/docker-compose.yml`
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

- Compose file: `actual-budget/docker-compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: yes
- Git status for stack path: clean
- `actualbudget`: running (healthy)

## Services

- `actualbudget`
- `actual-auto-sync`

## Images

- `actualbudget/actual-server:latest`
- `seriouslag/actual-auto-sync:latest`

## Operations

```bash
cd /home/ethan/docker/actual-budget
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
