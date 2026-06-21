# Traefik Dynamic Configuration

`npm-migration.yml` is generated from `nginx-proxy-manager/npm-migration-inventory.yml`:

```bash
python3 scripts/traefik-generate-dynamic.py \
  --inventory nginx-proxy-manager/npm-migration-inventory.yml \
  --output traefik/dynamic/npm-migration.yml
```

Use Docker labels for Compose-managed services over time. Keep this file-provider route set for LAN services and migration compatibility.
