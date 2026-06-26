# Stack: monitoring-stack

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `monitoring-stack/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: yes
- README: no

## Services

- `prometheus`
- `grafana`
- `node-exporter`
- `cadvisor`
- `loki`
- `promtail`

## Images

- `gcr.io/cadvisor/cadvisor:v0.47.2`
- `grafana/grafana-oss:latest`
- `grafana/loki:latest`
- `grafana/promtail:latest`
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
