# docs/traefik-migration.md

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

# NPM to Traefik Migration

Traefik is the long-term IaC reverse proxy. Nginx Proxy Manager remains the rollback path until Cloudflared is moved and routes are verified.

## Current State

- Public ingress: Cloudflare Tunnel via `cloudflared`.
- Current reverse proxy: Nginx Proxy Manager on `proxy_net`.
- New reverse proxy: Traefik on `proxy_net`, running in parallel on host port `8088`.
- Migration inventory: `nginx-proxy-manager/npm-migration-inventory.yml`.
- Generated Traefik routes: `traefik/dynamic/npm-migration.yml`.
- Wiki.js target-state routes: `traefik/dynamic/wiki.yml`.

## Validate Before Cutover

Start Traefik without stopping NPM:

```bash
cd /home/ethan/docker/traefik
docker compose up -d
```

Test routes by sending the original host header to Traefik's validation port:

```bash
curl -H 'Host: actual.ethanh.online' http://127.0.0.1:8088/
curl -H 'Host: radarr.ethanh.online' http://127.0.0.1:8088/
curl -H 'Host: obsidian.ethanh.online' http://127.0.0.1:8088/
curl -H 'Host: wiki.ethan-herring.com' http://127.0.0.1:8088/
```

Wiki.js should answer for:

- `wiki.ethan-herring.com`
- `wiki.pup-percy.com`
- `wiki.ethanh.online`

## Cutover

After route checks pass, update the Cloudflare Tunnel public-service target from NPM to Traefik:

```text
http://traefik:80
```

Do not remove NPM immediately. Leave it stopped or idle until external routing is verified and a rollback window has passed.

## Rollback

Point Cloudflared back to NPM:

```text
http://npm:80
```

Then restart `cloudflared` if needed.

## Ongoing IaC Model

- Compose-managed services should gradually move to Docker labels in their stack files.
- LAN/IP services should stay in Traefik file-provider YAML.
- `nginx-proxy-manager/npm-migration-inventory.yml` is a migration artifact, not the permanent source after labels are added.
- During transition, existing NPM DNS/Let's Encrypt certificate material can remain
  the rollback source. Do not delete NPM certificate data until Traefik owns
  certificate automation and all Cloudflared routes have been verified.
