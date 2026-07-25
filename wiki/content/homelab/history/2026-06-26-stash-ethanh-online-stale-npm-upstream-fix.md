# 2026-06-26T18-23-57-vlfS-stash_ethanh_online_stale_npm_upstream_fix

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f052c-9af1-7302-a0ca-e3d5c07238d4
updated_at: 2026-06-26T18:27:55+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/26/rollout-2026-06-26T18-23-57-019f052c-9af1-7302-a0ca-e3d5c07238d4.jsonl
cwd: /home/ethan/docker
git_branch: main

# Stash public hostname outage traced to stale NPM upstream and fixed by switching proxy host to the Docker service name.

Rollout context: The user reported that `stash.ethanh.online` was not working from the `/home/ethan/docker` homelab checkout. The agent used systematic debugging, checked the live Stash container, NPM/Traefik-ish proxy state, and the generated Nginx Proxy Manager config/database before editing anything.

## Task 1: Diagnose and fix `stash.ethanh.online`

Outcome: success

Preference signals:
- The user’s terse report, `Stash.ethanh.online isnt working`, indicates they expect a direct live-systems triage rather than speculation or a high-level explanation.
- The user did not ask for an app-level change; the agent’s final fix was at the proxy/config layer, which matches the user’s likely expectation that public hostname breakage should be traced from the edge inward.

Key steps:
- Verified the Stash container was up and serving locally on `127.0.0.1:9999` with HTTP 200.
- Verified the public hostname was hanging/timeouting while local service calls worked.
- Inspected Nginx Proxy Manager’s SQLite DB and generated vhost config under `nginx-proxy-manager/nginx_config/data/nginx/proxy_host/10.conf`.
- Found the generated vhost for `stash.ethanh.online` was proxying to `192.168.1.113:9999` instead of the Docker service name `stash:9999`.
- Confirmed that `http://stash:9999/` worked from inside the NPM container, while `http://192.168.1.113:9999/` from inside NPM timed out.
- Backed up the NPM DB and generated vhost file before changing the config.
- Updated the generated vhost file to use `set $server "stash";`, reloaded Nginx, and restarted NPM to verify the fix persisted.
- Verified end to end that `https://stash.ethanh.online/` returned 200 again, including after the NPM restart.

Failures and how to do differently:
- An initial attempt to patch the generated vhost from the host failed because the file was root-owned; editing had to be done inside the NPM container where the mounted config was writable.
- One edit command initially did not actually modify the file because of shell quoting/sed pattern issues; the later simplified replacement (`sed -i 's/192\.168\.1\.113/stash/g'`) succeeded.
- There were unrelated pre-existing NPM warnings about duplicate `nextcloud.ethanh.online` server names; they were noisy but not the cause of the Stash outage.

Reusable knowledge:
- In this checkout, the live NPM config is under `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/`, and the practical truth source for a proxy host is the generated file in `data/nginx/proxy_host/` plus the SQLite DB in `data/database.sqlite`.
- For Stash specifically, the Docker service name `stash` on `proxy_net` was reachable from NPM, while the host-IP upstream `192.168.1.113:9999` was not reliable from inside NPM.
- NPM can keep serving a stale generated vhost even when the DB row has already been updated/deleted; check both the DB row and the generated `*.conf` before assuming the active route matches the DB.
- Restarting NPM after the edit was a useful persistence check: the corrected vhost still returned 200 after restart.

References:
- [1] `docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | rg -i 'stash|nginx|npm|cloudflared|traefik'` showed `stash` up with `0.0.0.0:9999->9999/tcp` and `npm` healthy.
- [2] `docker compose -f /home/ethan/docker/stash/docker-compose.yml config` confirmed the Stash service used `image: stashapp/stash:latest`, `proxy_net`, and bind mounts for `/data`, `/metadata`, and `/root/.stash`.
- [3] `python3 ... select id, domain_names, forward_scheme, forward_host, forward_port, enabled ... from proxy_host where domain_names like '%stash%'` showed an active row `id=10` with `forward_host='stash'` and a deleted stale row `id=72` with `forward_host='192.168.1.102'`.
- [4] `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/nginx/proxy_host/10.conf` originally contained `set $server         "192.168.1.113";`; after the fix it contained `set $server         "stash";`.
- [5] Verification after the fix: `curl ... https://stash.ethanh.online/` returned `public_code=200`, and inside NPM `curl http://stash:9999/` returned `backend_code=200`.
- [6] After `docker restart npm`, `docker ps --filter name=npm` showed `Up ... (healthy)`, and the same public/NPM HTTPS probes still returned 200.
