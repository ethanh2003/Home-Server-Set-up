# Stack: monitoring-stack

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `monitoring-stack/docker-compose.yml`
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

- Compose file: `monitoring-stack/docker-compose.yml`
- Compose tracked in Git: yes
- README: no
- SOPS env: yes
- Git status for stack path: clean
- `blackbox-exporter`: running
- `cadvisor`: running (healthy)
- `grafana`: running (healthy)
- `loki`: running
- `node-exporter`: running
- `prometheus`: running (healthy)
- `promtail`: running

## Services

- `prometheus`
- `grafana`
- `node-exporter`
- `cadvisor`
- `loki`
- `promtail`
- `blackbox-exporter`

## Images

- `gcr.io/cadvisor/cadvisor:v0.47.2`
- `grafana/grafana-oss:latest`
- `grafana/loki:latest`
- `grafana/promtail:latest`
- `prom/blackbox-exporter:latest`
- `prom/node-exporter:latest`
- `prom/prometheus:latest`

## Operations

```bash
cd /home/ethan/docker/monitoring-stack
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
