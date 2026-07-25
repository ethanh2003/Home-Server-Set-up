# dawarich/README.md

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

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
