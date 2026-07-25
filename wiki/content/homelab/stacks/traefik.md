# Stack: traefik

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `traefik/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: no
- README: no

## Project Status

- Runtime: not checked
- Project status: in progress
- Last verified: 2026-07-04

## Remaining Tasks

- Complete Cloudflare cutover from NPM to Traefik after route parity is verified.
- Keep NPM available as rollback until public ingress has been proven off-LAN.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

## Evidence

- Compose file: `traefik/docker-compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: no
- Git status for stack path: omitted
- Live runtime state is monitored in Prometheus and omitted from deterministic wiki output.

## Services

- `traefik`

## Images

- `traefik:v3.5`

## Operations

```bash
cd /home/ethan/docker/traefik
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
