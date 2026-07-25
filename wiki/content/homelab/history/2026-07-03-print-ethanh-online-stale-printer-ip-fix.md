# 2026-07-03T00-46-13-URcB-print_ethanh_online_stale_printer_ip_fix

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f2570-bfb3-7d40-a88f-7fc7be2a9a91
updated_at: 2026-07-03T00:49:46+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/03/rollout-2026-07-03T00-46-13-019f2570-bfb3-7d40-a88f-7fc7be2a9a91.jsonl
cwd: /home/ethan

# Fixed the print.ethanh.online reverse-proxy outage by updating stale NPM printer upstreams to the printer’s current IP.

Rollout context: The user asked to "Fix print.ethanh.online" from `/home/ethan`. The agent treated it as a live homelab break/fix, checked NPM/proxy logs and the local print stack, and used systematic debugging to identify whether the failure was DNS, proxy, or upstream availability.

## Task 1: Diagnose and repair print.ethanh.online

Outcome: success

Preference signals:
- The user’s request was simply "Fix print.ethanh.online" -> in similar homelab break/fix tasks, start by checking the real service/proxy/logs rather than asking for more context or guessing from the hostname.

Key steps:
- Verified the hostname resolved locally to the NPM host (`192.168.1.113`) and that the `npm` container was up/healthy.
- Inspected the NPM SQLite DB and generated vhost configs for print-related routes; discovered the active print hosts were `proxy_host` rows `48` and `123`.
- Read NPM error logs and confirmed the public 502 was `connect() failed (113: No route to host)` to `192.168.1.158:443` for `print.ethanh.online`.
- Checked LAN discovery / CUPS state and found the printer advertised as `Ethans_printer.local`, resolving to `192.168.1.146`; `curl` to `192.168.1.146` returned the Brother status page behavior (HTTP `411` on plain request, then HTTP `200` after following redirects to `/home/status.html`).
- Backed up the NPM DB before mutation, updated the DB rows and generated NPM vhosts from `192.168.1.158` to `192.168.1.146`, and aligned the checked-in migration artifacts (`npm-migration-inventory.yml`, `traefik/dynamic/npm-migration.yml`) to the same IP.
- Reloaded NPM, verified `docker exec npm nginx -t` passed, and smoke-tested all three print hostnames.

Failures and how to do differently:
- The first attempt to patch generated NPM vhost files from the host failed because those files were not writable on the host filesystem; the fix was to update them inside the `npm` container instead.
- A broad `find`/`rg` sweep hit permission-restricted directories under `/home/ethan/docker`; future sweeps should expect those permission errors and focus on the relevant stack files once the active route is identified.
- The initial public symptom was a 502, but the root cause was not NPM itself; the decisive evidence was the NPM error log showing `No route to host` against a stale upstream IP.

Reusable knowledge:
- For print routes in this homelab, the live truth source is both the NPM SQLite DB and the generated vhost files under `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/nginx/proxy_host/`.
- `print.ethanh.online` and related print hostnames can drift if the Brother printer’s IP changes; verify the printer’s current mDNS name and reachable IP before editing proxy rows.
- CUPS on the host can reveal the current print queue and mDNS identity (`Ethan_s_Printer`, `Ethans_printer.local`) even when the public hostname is broken.
- The reconciler script is a useful drift check: `python3 /home/ethan/docker/scripts/npm_reconcile.py --db /home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite` reported `planned 0 change(s)` after the fix.

References:
- [1] NPM error log evidence: `connect() failed (113: No route to host) ... upstream: "https://192.168.1.158:443/"` for `server: print.ethanh.online`.
- [2] Printer discovery evidence: `getent hosts Ethans_printer.local -> 192.168.1.146`, `ping Ethans_printer.local` succeeded, and `curl -k -L https://print.ethanh.online/` returned `http_code=200 ... url=https://print.ethanh.online/home/status.html`.
- [3] Backup path: `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite.bak-print-route-20260703T004813Z`.
- [4] Updated active vhost files inside the container: `/data/nginx/proxy_host/48.conf` and `/data/nginx/proxy_host/123.conf` now point at `192.168.1.146`.
- [5] Updated checked-in route artifacts: `/home/ethan/docker/nginx-proxy-manager/npm-migration-inventory.yml` and `/home/ethan/docker/traefik/dynamic/npm-migration.yml`.
- [6] Verification: `docker exec npm nginx -t` passed; `curl -k -L` to `print.ethanh.online`, `print.ethan-herring.com`, and `print.pup-percy.com` each returned HTTP 200.
