# Stack: kopia

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `kopia/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: yes
- README: no

## Project Status

- Runtime: not checked
- Project status: needs docs
- Last verified: 2026-07-04

## Remaining Tasks

- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

## Evidence

- Compose file: `kopia/docker-compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: yes
- Git status for stack path: omitted
- Live runtime state is monitored in Prometheus and omitted from deterministic wiki output.

## Services

- `kopia`

## Images

- `kopia/kopia:latest`

## Operations

```bash
cd /home/ethan/docker/kopia
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
