# Stack: nginx-proxy-manager

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `nginx-proxy-manager/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: no
- README: no

## Project Status

- Runtime: not checked
- Project status: needs docs
- Last verified: 2026-07-04

## Remaining Tasks

- Keep as rollback during Traefik migration.
- Reconcile generated proxy configs with the live SQLite database before disabling stale rows.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

## Evidence

- Compose file: `nginx-proxy-manager/docker-compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: no
- Git status for stack path: omitted
- Live runtime state is monitored in Prometheus and omitted from deterministic wiki output.

## Services

- `npm`

## Images

- `jc21/nginx-proxy-manager:latest`

## Operations

```bash
cd /home/ethan/docker/nginx-proxy-manager
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
