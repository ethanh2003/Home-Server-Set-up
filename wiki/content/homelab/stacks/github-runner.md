# Stack: github-runner

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `github-runner/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: no
- README: no

## Project Status

- Runtime: not checked
- Project status: needs docs
- Last verified: 2026-07-04

## Remaining Tasks

- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

## Evidence

- Compose file: `github-runner/docker-compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: no
- Git status for stack path: omitted
- Live runtime state is monitored in Prometheus and omitted from deterministic wiki output.

## Services

- `github-runner`

## Images

- `homelab/github-actions-runner:2.335.1`

## Operations

```bash
cd /home/ethan/docker/github-runner
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
