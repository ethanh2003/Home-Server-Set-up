# Stack: linkstack

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `linkstack/compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: no
- README: no

## Project Status

- Runtime: not checked
- Project status: needs docs
- Last verified: 2026-07-04

## Remaining Tasks

- Normalize the stack into the broader IaC model and document public hardening settings.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

## Evidence

- Compose file: `linkstack/compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: no
- Git status for stack path: omitted
- Live runtime state is monitored in Prometheus and omitted from deterministic wiki output.

## Services

- `linkstack`

## Images

- `'linkstackorg/linkstack:latest'`

## Operations

```bash
cd /home/ethan/docker/linkstack
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
