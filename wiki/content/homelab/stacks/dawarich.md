# Stack: dawarich

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `dawarich/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: no
- README: yes

## Project Status

- Runtime: not checked
- Project status: operational
- Last verified: 2026-07-04

## Remaining Tasks

- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

## Evidence

- Compose file: `dawarich/docker-compose.yml`
- Compose tracked in Git: yes
- README: yes
- SOPS env: no
- Git status for stack path: omitted
- Live runtime state is monitored in Prometheus and omitted from deterministic wiki output.

## Services

- `dawarich_redis`
- `dawarich_db`
- `dawarich_app`
- `dawarich_sidekiq`

## Images

- `freikin/dawarich:latest`
- `postgis/postgis:17-3.5-alpine`
- `redis:7.4-alpine`

## Operations

```bash
cd /home/ethan/docker/dawarich
docker compose config
docker compose ps
```

## Notes

# Dawarich

Dawarich is a self-hosted location history app exposed through Nginx Proxy Manager.

## Public URLs

- `https://dawarich.ethanh.online`
- `https://dawarich.ethan-herring.com`
- `https://dawarich.pup-percy.com`

## Operations

```bash
cd /home/ethan/docker/dawarich
docker compose pull
docker compose up -d
docker compose ps
docker compose logs --tail=100 dawarich_app
```

The stack is discovered by `/home/ethan/docker/manage-stacks.sh` because it uses `docker-compose.yml`.

Runtime secrets live in `.env`, which is ignored by the parent repo. Do not commit that file.
