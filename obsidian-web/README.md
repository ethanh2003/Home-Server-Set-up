# Obsidian Web

Browser-accessible Obsidian desktop for the SSD vault at `/data/Obsidian/Main`.

## Access

- LAN/VPN URL: `https://obsidian-web.ethanh.online`
- NPM upstream: `https://obsidian-web:3001`
- Vault path inside the container: `/vaults/Main`
- Persistent app config: `/home/ethan/docker/obsidian-web/config`
- Resource limits: 2 CPU cores, 3 GiB RAM, 4 GiB RAM+swap, 512 PIDs

The route is intended for LAN/VPN use only. Do not add this hostname to the public Cloudflare tunnel without adding stronger access control.

## Operations

```bash
cd /home/ethan/docker/obsidian-web
docker compose config
docker compose up -d
docker compose ps
docker compose logs -f --tail=100
```

The `.env` file contains the local basic-auth credentials and is intentionally git-ignored.

The existing always-on Codex REST/MCP daemon remains separate at `/home/ethan/obsidian-api-mcp` and listens on `0.0.0.0:27124`.
