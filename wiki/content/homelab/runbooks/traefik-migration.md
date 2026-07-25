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

Run the parity gate from the repo root:

```bash
cd /home/ethan/docker
./scripts/traefik-route-parity.py
```

The parity gate compares:

- NPM HTTP on local port `80`
- NPM HTTPS on local port `443`
- staged Traefik HTTP on local port `8088`

It blocks Traefik-only regressions when NPM currently returns a real `2xx`,
expected redirect, `401`, or `403`. It does not block on routes that are already
broken under NPM, and it treats the NPM default "host is not set up yet" page as
not working even though NPM returns `200`.

Manual spot checks can still send the original host header to Traefik's
validation port:

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

While Cloudflare still points at NPM, temporary NPM proxy hosts also forward
these wiki hostnames to `http://wikijs:3000`:

- NPM proxy host `104`: `wiki.ethan-herring.com`, `wiki.ethanh.online`
- NPM proxy host `105`: `wiki.pup-percy.com`

These are transition routes for first-run setup and rollback access. Once the
Cloudflare Tunnel target is moved to Traefik and verified, Traefik becomes the
authoritative IaC route and the temporary NPM rows can be retired.

Known route fixes that must remain in place before cutover:

- Home Assistant trusts the Traefik proxy IP in
  `home-assistant/config/homeassistant/configuration.yaml`.
- Stash is attached to `proxy_net` so Traefik can reach `stash:9999`.
- HTTPS origins addressed by LAN IPs use generated per-service Traefik
  `serversTransport` entries with `insecureSkipVerify`. This is currently
  required for the printer and Cockpit routes because their certificates do not
  validate for their LAN IPs.

## Cutover

After route parity passes, export or screenshot the current Cloudflare Tunnel
public-hostname configuration. Then update the Cloudflare Tunnel public-service
target from NPM to Traefik:

```text
http://traefik:80
```

The repo helper can do this through the Cloudflare API when these environment
variables are available. It rewrites every Cloudflare public hostname that
appears in `nginx-proxy-manager/npm-migration-inventory.yml` to the Traefik
target, even when the current tunnel route points directly at a backend service
instead of `npm`.

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_TUNNEL_ID`

Dry-run and backup:

```bash
./scripts/cloudflare-tunnel-cutover.py
```

Apply:

```bash
./scripts/cloudflare-tunnel-cutover.py --apply
```

Add or verify these public hostnames in the same tunnel:

- `wiki.ethan-herring.com`
- `wiki.pup-percy.com`
- `wiki.ethanh.online`

Preserve DNS records, Cloudflare Access policies, non-HTTP routes, and the
existing token-run tunnel setup.

Do not remove NPM immediately. Leave it stopped or idle until external routing is verified and a rollback window has passed.

## Rollback

Point Cloudflared back to NPM:

```text
http://npm:80
```

If the helper was used, restore the timestamped backup it created:

```bash
./scripts/cloudflare-tunnel-cutover.py --rollback cloudflared/backups/tunnel-config-YYYYmmddTHHMMSSZ.json --apply
```

Then restart `cloudflared` only if Cloudflare does not apply the remote config promptly.

## Ongoing IaC Model

- Compose-managed services should gradually move to Docker labels in their stack files.
- LAN/IP services should stay in Traefik file-provider YAML.
- `nginx-proxy-manager/npm-migration-inventory.yml` is a migration artifact, not the permanent source after labels are added.
- During transition, existing NPM DNS/Let's Encrypt certificate material can remain
  the rollback source. Do not delete NPM certificate data until Traefik owns
  certificate automation and all Cloudflared routes have been verified.
