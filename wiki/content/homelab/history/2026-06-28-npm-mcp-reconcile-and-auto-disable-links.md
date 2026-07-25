# 2026-06-28T02-31-29-Vomp-npm_mcp_reconcile_and_auto_disable_links

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f0c11-5082-7780-9343-2aad2e9d1a45
updated_at: 2026-06-28T02:49:56+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/28/rollout-2026-06-28T02-31-29-019f0c11-5082-7780-9343-2aad2e9d1a45.jsonl
cwd: /home/ethan

# Added NPM MCP integration and a Codex hook-backed NPM reconciler for homelab public links

Rollout context: The user wanted Codex to manage Nginx Proxy Manager (NPM) “all aspects,” ideally via a prebuilt MCP server, and to add hooks so Codex updates/creates/disables links automatically. They later clarified they wanted auto-disable instead of delete, and that every app should have `ethan-herring.com`, `ethanh.online`, and `pup-percy.com` URLs. The work was done from `/home/ethan` with the NPM stack under `/home/ethan/docker/nginx-proxy-manager`.

## Task 1: Clarify NPM scope and choose an implementation shape

Outcome: success

Preference signals:
- The user asked for “all aspects of npm” and “a prebuilt one” -> future runs should default to checking for an existing MCP/server before inventing custom tooling.
- The user asked that “any time codex adds services it checks everything running and updates links to match the current state” -> future runs should treat route reconciliation as a lifecycle action, not a one-off manual edit.
- The user corrected delete to “auto disable instead of delete” -> stale-route cleanup should default to disabling, not destructive deletion.
- The user required `ethan-herring.com`, `ethanh.online`, and `pup-percy.com` coverage -> future link management should assume those three public domains are the canonical targets unless changed.

Key steps:
- Inspected Codex guidance and local NPM artifacts.
- Confirmed `npm` meant Nginx Proxy Manager, not Node package manager.
- Identified the live NPM DB at `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite` and existing route-writing history.
- Verified Codex hooks live in `~/.codex/hooks.json` or inline TOML, and MCP servers live in `~/.codex/config.toml`.
- Found a prebuilt NPM MCP candidate and chose the `uvx`-based integration route.

Failures and how to do differently:
- A prompt-based “auto mutate when links are mentioned” idea was too risky; explicit reconciliation after service changes was the right shape.
- The first dry-run showed NPM route/cert constraints, so the reconciler had to become certificate-aware rather than assuming one row can cover all three domains.

Reusable knowledge:
- NPM config source of truth in this setup is the SQLite DB plus generated `/data/nginx/proxy_host/*.conf` files; editing only one surface is insufficient.
- Codex hooks can be used as a post-turn reconciliation trigger, but they should be idempotent and non-destructive.
- `codex mcp add` supports stdio servers with `--env`/`env_vars`, and a local `uvx` launcher is a workable way to run prebuilt MCP packages.

References:
- [1] Live NPM DB: `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite`
- [2] Current NPM compose: `/home/ethan/docker/nginx-proxy-manager/docker-compose.yml`
- [3] `codex mcp` help confirmed `codex mcp add NAME (--url URL | -- COMMAND...)`

## Task 2: Implement the reconciler, Codex config, and live NPM sync

Outcome: success

Preference signals:
- The user wanted “auto disable instead of delete” -> implement stale-route cleanup by disabling rows.
- The user asked for “ensure each app has a ethan-herring.com ethanh.online and pup-percy.com url” -> the reconciler should enforce coverage for all three domains.
- The user said “the access token on all of them have access to all urls if you want to consolidate” -> future runs can consolidate where cert/domain coverage allows, rather than preserving unnecessary per-domain separation.
- The user wanted Codex to “check everything running and updates links to match the current state” -> reconciliation should use Docker runtime state, not just static compose files.

Key steps:
- Added NPM MCP to `/home/ethan/.codex/config.toml` using `/home/ethan/.local/bin/uvx nginx-proxy-manager-mcp`, with `NPM_URL` pointed at local NPM and credentials forwarded from environment variables.
- Added a `Stop` hook in `/home/ethan/.codex/hooks.json` that runs the reconciler after Codex turns and logs to `~/.codex/npm-reconcile-hook.log`.
- Built `/home/ethan/docker/scripts/npm_reconcile.py` with:
  - SQLite load/update of `proxy_host`
  - certificate-aware alias planning
  - auto-disable for stale Docker-name routes
  - companion row creation when a cert split requires multiple rows
  - generated config sync for `/data/nginx/proxy_host/*.conf`
  - fallback to `docker exec npm` when host-side config files are root-owned
  - dry-run and apply modes
  - NPM nginx validation/reload logic
- Wrote tests in `/home/ethan/docker/tests/test-npm-reconcile.py` covering alias expansion, duplicate consolidation, stale-route disablement, and generated config sync.
- Installed `uvx` locally via Astral’s installer because the host didn’t have `uv`, `uvx`, `pip`, or `pipx`.
- Applied the reconciler to the live NPM DB and synced generated configs.

Failures and how to do differently:
- The first implementation tried to collapse all three domains onto one row, but live NPM lacked a single certificate covering all three domains. The reconciler had to be adjusted to be cert-aware and create a `pup-percy.com` companion row when needed.
- Direct DB writes did not automatically regenerate NPM config files; generated config sync was required.
- Host-side writes to `/data/nginx/proxy_host/*.conf` failed because those files are root-owned; the correct fallback was `docker exec npm` to write/remove them inside the container.
- The apply path initially skipped config sync when DB changes were zero; that was corrected so `--apply --reload` always syncs generated configs.
- Some NPM-generated files caused a pre-existing `nextcloud.ethanh.online` warning, which turned out to be from an orphan config file rather than the active DB row; syncing/removing orphan configs cleared the mismatch.

Reusable knowledge:
- In this NPM setup, the live route truth is split across the SQLite DB and generated `proxy_host/*.conf`; after DB mutations, configs must be synced and nginx validated.
- Existing wildcard certs were validated in the DB: cert `4` covers `ethanh.online`/`ethan-herring.com`, and cert `5` covers `pup-percy.com`.
- The live stack had 33 app slugs with full three-domain coverage after reconciliation.
- `docker exec npm nginx -t` is a useful final gate, and `python3 ... --db ...` should become idempotent before any production apply.

References:
- [1] Added Codex MCP entry: `/home/ethan/.codex/config.toml`
- [2] Added hook: `/home/ethan/.codex/hooks.json`
- [3] Reconciler: `/home/ethan/docker/scripts/npm_reconcile.py`
- [4] Tests: `/home/ethan/docker/tests/test-npm-reconcile.py`
- [5] Plan doc: `/home/ethan/docker/docs/superpowers/plans/2026-06-28-npm-mcp-reconcile.md`
- [6] Backup created before live apply: `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite.bak-npm-reconcile-20260628T024630Z`
- [7] Verification outputs: `python3 /home/ethan/docker/tests/test-npm-reconcile.py` -> `PASS: [REDACTED] reconcile`; `python3 /home/ethan/docker/scripts/npm_reconcile.py --db ...` -> `npm-reconcile: planned 0 change(s)`; `docker exec npm nginx -t` -> syntax OK
- [8] Final domain checks returned `200` for `actual.*`, `share.*`, and `wiki.*`, and `302` for `jellyfin.*`
