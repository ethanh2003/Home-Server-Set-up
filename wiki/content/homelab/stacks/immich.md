# Stack: immich

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `immich/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: yes
- README: no

## Services

- `immich-server`
- `immich-machine-learning`
- `redis`
- `database`

## Images

- `docker.io/valkey/valkey:8-bookworm`
- `ghcr.io/immich-app/immich-machine-learning:release-openvino`
- `ghcr.io/immich-app/immich-server:${IMMICH_VERSION:-release}`
- `ghcr.io/immich-app/postgres:14-vectorchord0.4.3-pgvectors0.2.0`

## Operations

```bash
cd /home/ethan/docker/immich
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
