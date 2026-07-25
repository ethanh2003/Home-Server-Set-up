# 2026-07-22T13-41-02-ETYN-frigate_stack_npm_update_and_https_upstream_fix

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f8a0e-f156-7a80-8d56-81a23ffe83d5
updated_at: 2026-07-22T13:51:32+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/22/rollout-2026-07-22T13-41-02-019f8a0e-f156-7a80-8d56-81a23ffe83d5.jsonl
cwd: /home/ethan

# Frigate stack configured and routed through existing NPM

Rollout context: The user asked to configure a Frigate stack from a pasted compose snippet, then clarified they wanted to use the existing Home Assistant Mosquitto broker (`existing`) and later explicitly added `approved, ensure npm is updated as well`. The work happened in `/home/ethan` with the main Docker repo under `/home/ethan/docker`.

## Task 1: Configure the Frigate stack

Outcome: success

Preference signals:
- The user said `existing` after being asked whether to use the existing Home Assistant Mosquitto broker or a separate Frigate-only broker -> future similar setups should default to reusing the existing broker when the user answers with a short affirmative.
- The user said `approved, ensure npm is updated as well` -> future similar deployment work should treat NPM updates as part of the requested deliverable, not an optional follow-up.
- The pasted snippet included a devcontainer-oriented Frigate compose example, but the chosen implementation moved to a production stack under `/home/ethan/docker/frigate` -> for similar homelab stack requests, prefer a normal stack layout rather than preserving devcontainer scaffolding unless the user explicitly wants dev tooling.

Key steps:
- Inspected the host’s homelab Docker conventions: one stack per `/home/ethan/docker/<name>`, `docker-compose.yml` discovery, `proxy_net` as the shared routed network, and relative bind mounts.
- Checked host groups and devices; actual IDs were `render=993`, `video=44`, `plugdev=46`, with `/dev/dri/renderD128` and `/dev/bus/usb` available.
- Found an existing `/home/ethan/docker/frigate/compose.yml.save` and used that as the source snippet while creating a new production `docker-compose.yml`.
- Created `/home/ethan/docker/frigate/docker-compose.yml` using `ghcr.io/blakeblackshear/frigate:stable`, `proxy_net`, `/config`, `/media/frigate`, `/tmp/cache`, `8971` UI exposure, and the observed device/group mappings.
- Created `/home/ethan/docker/frigate/config/config.yml` pointing MQTT at `mosquitto:1883` and including a disabled dummy camera so the service could boot before real cameras were added.
- `docker compose -f /home/ethan/docker/frigate/docker-compose.yml config` succeeded and showed only the `frigate` service.

Failures and how to do differently:
- The first HTTP check against `http://127.0.0.1:8971/` returned `400 Bad Request` because Frigate’s listener is HTTPS, not plain HTTP. Future similar checks should test `https://127.0.0.1:8971/` (or use the correct scheme in NPM) once the service is up.
- The initial NPM route insertion used `forward_scheme: http`; that produced the HTTP/HTTPS mismatch and had to be corrected to `https`.

Reusable knowledge:
- Frigate’s HTTPS listener on `8971` can still be fronted by NPM, but the upstream scheme must be `https` for this host setup.
- The Frigate container started cleanly and reported healthy once the compose file was corrected and the image finished pulling.
- Frigate generated first-boot admin credentials in container logs; do not store those in memory/notes.

References:
- [1] New stack files: `/home/ethan/docker/frigate/docker-compose.yml`, `/home/ethan/docker/frigate/config/config.yml`
- [2] Compose validation: `docker compose -f /home/ethan/docker/frigate/docker-compose.yml config` -> rendered service `frigate` with `proxy_net`
- [3] Host hardware discovery: `getent group render video plugdev` showed `render:x:993:ethan`, `video:x:44:ethan`, `plugdev:x:46:ethan`; `/dev/dri/renderD128` existed

## Task 2: Update Nginx Proxy Manager for Frigate

Outcome: success

Preference signals:
- The user explicitly requested `ensure npm is updated as well` -> future similar homelab service setups should update NPM routes during the same task when asked, not leave routing for later.
- The user did not ask for a separate broker or separate ingress path -> the route update reused the existing NPM instance and existing cert coverage.

Key steps:
- Backed up the NPM database first to `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite.bak-frigate-20260722T134840Z`.
- Created NPM proxy host rows `148` and `149` for:
  - `frigate.ethanh.online`, `frigate.ethan-herring.com`
  - `frigate.pup-percy.com`
- Both routes were updated to forward to `frigate:8971` with `forward_scheme='https'` after discovering the Frigate listener is HTTPS.
- Regenerated NPM generated config files `148.conf` and `149.conf`, and `docker exec npm nginx -t` passed.
- Ran `python3 /home/ethan/docker/scripts/npm_reconcile.py --db /home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite` and got `npm-reconcile: planned 0 change(s)` after the update.

Failures and how to do differently:
- The first route attempt pointed NPM at `http://frigate:8971`, which produced `400 The plain HTTP request was sent to HTTPS port`. Future similar routes should verify the upstream protocol before committing the NPM row.

Reusable knowledge:
- In this homelab, NPM routing truth lives in both the SQLite DB and the generated `nginx/proxy_host/*.conf` files; both should be checked after route changes.
- This repo already has a `scripts/npm_reconcile.py` helper that can regenerate generated configs and verify `nginx -t`.
- Certificate mapping used here: cert `4` for Ethan domains, cert `5` for `pup-percy.com`.

References:
- [1] Backup: `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite.bak-frigate-20260722T134840Z`
- [2] NPM rows:
  - id `148`: `frigate.ethanh.online`, `frigate.ethan-herring.com` -> `https://frigate:8971`, cert `4`
  - id `149`: `frigate.pup-percy.com` -> `https://frigate:8971`, cert `5`
- [3] Generated vhosts: `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/nginx/proxy_host/148.conf`, `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/nginx/proxy_host/149.conf`
- [4] NPM reload verification: `nginx -t` succeeded inside the NPM container

## Task 3: Verify service health and routed access

Outcome: success

Preference signals:
- The user did not need a separate progress report before verification, but the actual work was only complete after live checks passed -> for similar stack work, finish with live container and route verification rather than only file-level edits.

Key steps:
- Started the stack with `docker compose -f /home/ethan/docker/frigate/docker-compose.yml up -d`.
- The image pull took time because `ghcr.io/blakeblackshear/frigate:stable` is large; the session was kept open until startup completed.
- Verified the container was `Up ... (healthy)` via `docker compose ... ps`.
- Verified Frigate’s local HTTPS endpoint with `curl -k -I --resolve frigate.ethanh.online:443:127.0.0.1 https://frigate.ethanh.online/` and the other two hostnames.
- Verified all three NPM hostnames returned `200 OK` with `X-Served-By` headers matching the requested Frigate domains.
- Confirmed Frigate health via `docker inspect frigate --format '{{json .State.Health}}'`.

Failures and how to do differently:
- A plain `curl -I http://127.0.0.1:8971/` returned `400` and was not a valid health check for this service. The correct local test is HTTPS with the host header or through NPM.

Reusable knowledge:
- Frigate’s first boot can emit a default admin user/password in logs; the password should not be preserved in notes.
- After the upstream scheme fix, the three hostnames returned `200 OK` and `npm-reconcile` reported zero planned changes, which is a strong post-change drift check.

References:
- [1] Frigate container status: `Up ... (healthy)` after `docker compose -f /home/ethan/docker/frigate/docker-compose.yml up -d`
- [2] Successful route checks:
  - `curl -k -I --resolve frigate.ethanh.online:443:127.0.0.1 https://frigate.ethanh.online/` -> `200 OK`
  - `curl -k -I --resolve frigate.ethan-herring.com:443:127.0.0.1 https://frigate.ethan-herring.com/` -> `200 OK`
  - `curl -k -I --resolve frigate.pup-percy.com:443:127.0.0.1 https://frigate.pup-percy.com/` -> `200 OK`
- [3] Drift check: `python3 /home/ethan/docker/scripts/npm_reconcile.py --db /home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite` -> `npm-reconcile: planned 0 change(s)`
