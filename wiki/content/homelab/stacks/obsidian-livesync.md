# Stack: obsidian-livesync

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `obsidian-livesync/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: yes
- README: no

## Project Status

- Runtime: running
- Project status: needs docs
- Last verified: 2026-07-04

## Remaining Tasks

- Resolve the stale duplicate NPM row for `obsidian.ethan-herring.com` if it still exists.
- Keep LiveSync replication separate from the always-on Obsidian API/MCP service.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

## Evidence

- Compose file: `obsidian-livesync/docker-compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: yes
- Git status for stack path: untracked
- `couchdb`: running (healthy)

## Services

- `couchdb`

## Images

- `couchdb:latest`

## Operations

```bash
cd /home/ethan/docker/obsidian-livesync
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
