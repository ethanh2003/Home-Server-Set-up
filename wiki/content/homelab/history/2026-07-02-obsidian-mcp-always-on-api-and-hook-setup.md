# 2026-07-02T14-21-39-7huS-obsidian_mcp_always_on_api_and_hook_setup

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f2334-f0d3-71a2-9dc3-664ed7e262d6
updated_at: 2026-07-02T16:05:09+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/02/rollout-2026-07-02T14-21-39-019f2334-f0d3-71a2-9dc3-664ed7e262d6.jsonl
cwd: /home/ethan

# User wants an always-on LAN Obsidian MCP/API service, and clarified that it is not meant to replace LiveSync syncing.

Rollout context: The user asked to confirm the Obsidian stack under `/data` was fully and properly set up. Investigation found that CouchDB/LiveSync backend pieces were healthy, but no Obsidian desktop process was running, so the built-in REST/MCP plugin was not actually serving. The user then clarified they needed a LAN-accessible always-running Obsidian API/MCP server, not a UI-based 24/7 Obsidian instance, and later clarified that the new service should be used as an always-on MCP for notebook access whether Obsidian is running or not, while LiveSync remains their cross-network sync system.

## Task 1: Verify existing Obsidian stack under `/data` and `/home/ethan/docker/obsidian-livesync`

Outcome: success

Preference signals:
- The user asked to confirm the setup was “fully and properly setup” -> future work should verify live processes, ports, and sync surfaces rather than trusting folder layout or installed plugins.
- The user corrected `/data/obsidian` to `/data/Obsidian` by path/casing and wanted the check to cover “always running” REST/MCP behavior -> future checks should treat case-sensitive path mismatches and running services as first-class.
- The user later said they did not have any UI devices running Obsidian 24/7 and wanted to keep LiveSync because it works inside and outside the network -> future guidance should not assume a desktop Obsidian client can be kept open as the sync engine.

Key steps:
- Verified `/data/Obsidian/Main` existed and contained `obsidian-livesync` and `obsidian-local-rest-api` plugins.
- Verified the CouchDB container `obsidian-livesync-couchdb` was `healthy`, `restart: unless-stopped`, and serving authenticated requests.
- Verified `/data/Obsidian/Main/.obsidian/plugins/obsidian-livesync/data.json` had an active encrypted CouchDB remote config, but no Obsidian/Electron process was running, so the plugin was not actively serving REST/MCP.
- Confirmed `127.0.0.1:27123` and `127.0.0.1:27124` were closed at the time of the initial verification.
- Found a stale duplicate NPM row for `obsidian.ethan-herring.com` pointing at `192.168.1.185:8081`, while the generated config still routed the current Obsidian hostname(s) to CouchDB.

Failures and how to do differently:
- The built-in Obsidian Local REST API with MCP is not an always-on daemon; it depends on the Obsidian app running.
- The running `node ./mcp/server.cjs --stdio` process encountered during inspection belonged to a Codex plugin cache, not the vault.
- For this host, “installed plugin” is not enough evidence; verify the live app process and the listening ports.

Reusable knowledge:
- The Obsidian vault path on this host is `/data/Obsidian/Main`.
- The LiveSync backend stack is at `/home/ethan/docker/obsidian-livesync` and CouchDB is exposed on `5984` with auth.
- `obsidian-local-rest-api` has default ports `27124` (secure) and `27123` (insecure), but neither was listening without the desktop app running.
- `obsidian-livesync` plugin settings stored an encrypted CouchDB connection in `data.json`; plain fields were empty.

References:
- [1] `docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | rg -i 'obsidian|couch|mcp|live|api'` -> `obsidian-livesync-couchdb Up 2 weeks (healthy) 0.0.0.0:5984->5984/tcp`
- [2] `curl -sS -u "$COUCHDB_USER:$COUCHDB_PASSWORD" http://127.0.0.1:5984/therapy` -> `doc_count: 8737`, `HTTP:200`
- [3] `ss -ltnp | rg ':27123|:27124|:5984'` -> `27123/27124 closed`, `5984 open`
- [4] `/data/Obsidian/Main/.obsidian/plugins/obsidian-livesync/data.json` and `obsidian-local-rest-api/data.json` showed the plugins installed/configured, but not serving.

## Task 2: Build an always-on LAN Obsidian API/MCP service backed by the mounted vault

Outcome: success

Preference signals:
- The user asked for a “lan accessible always running obsidan api/mpc server” -> future default should be to create a real daemon/service rather than a GUI-plugin workaround.
- The user said the service was “more of an always on mcp so i can use the same notebook regardless of if obsidian is running or not” -> future implementations should prioritize notebook access independent of the Obsidian desktop app.
- The user explicitly said the setup is not meant to be a sync engine -> future agents should not conflate MCP/API access with LiveSync replication responsibility.
- The user later clarified they need LiveSync kept intact because it works inside and outside the network -> future designs should preserve the existing LiveSync fabric rather than replacing it.

Key steps:
- Created `/home/ethan/obsidian-api-mcp` as a Python 3.12 `uv` project with FastAPI and the MCP Python SDK.
- Implemented a shared vault core with guarded note read/write/append/patch/delete, search, and tag listing.
- Added tests first for path safety, symlink escape denial, hidden-folder denial, REST auth, and MCP tool registration; the initial test run failed on missing modules as expected after fixing packaging.
- Added Streamable HTTP MCP support using `FastMCP` and verified the SDK’s `streamable_http_app()` / `streamablehttp_client` path.
- Installed a user systemd service `obsidian-api-mcp.service` with `Restart=always`, linger enabled, and bound to `0.0.0.0:27124`.
- Stored a private bearer [REDACTED] in `/home/ethan/obsidian-api-mcp/.env` with mode `600`.
- Wrote a status note into the vault through the new REST API, proving real authenticated writes to the mounted vault.

Failures and how to do differently:
- The first `uv run pytest` failed because `hatchling` could not determine wheel contents; adding `[tool.hatch.build.targets.wheel] packages = ["src/obsidian_api_mcp"]` fixed packaging.
- The MCP HTTP integration initially failed with `403 Forbidden` because the SDK enforced its own DNS rebinding/Origin protection; the fix was to use `TransportSecuritySettings` and allow localhost/LAN host/origin patterns explicitly.
- Don’t assume a test passing only at the unit layer proves live MCP HTTP works; add a real streamable HTTP smoke test.

Reusable knowledge:
- The service runs from `/home/ethan/obsidian-api-mcp/.venv/bin/obsidian-api-mcp` and listens on `0.0.0.0:27124`.
- Local and LAN REST GETs to `/vault/` returned `200` with the bearer [REDACTED]; unauthenticated requests returned `401` and hidden technical paths like `.obsidian` returned `403`.
- The MCP server exposes `vault_list`, `vault_read`, `vault_write`, `vault_append`, `vault_delete`, `search_simple`, and `tag_list`.
- The service uses the same vault path as the Obsidian files: `/data/Obsidian/Main`.

References:
- [1] `/home/ethan/obsidian-api-mcp/pyproject.toml`, `/home/ethan/obsidian-api-mcp/src/obsidian_api_mcp/{vault.py,app.py,main.py}`
- [2] `/home/ethan/.config/systemd/user/obsidian-api-mcp.service`
- [3] `uv run pytest` -> `8 passed`
- [4] `systemctl --user status obsidian-api-mcp.service` -> `active (running)` and `ss -ltnp` -> `0.0.0.0:27124`
- [5] `codex mcp add obsidian --url http://127.0.0.1:27124/mcp/ --bearer-token-env-var OBSIDIAN_API_TOKEN` -> Codex registered the server as `obsidian`

## Task 3: Add conservative Codex MCP and Stop-hook automation for Obsidian vault updates

Outcome: success

Preference signals:
- The user asked to “add the codex mcp hooks to update it but only when appropriate” -> future automation should be conservative and opt-in, not always-write.
- The user later clarified they wanted “the same notebook regardless of if obsidian is running or not” -> future hook behavior should support durable notebook updates without depending on a desktop app being open.
- The user asked for an AI prompt for other devices to add the MCP server and hook within the network -> future work should produce copy-paste setup instructions for secondary devices when asked.

Key steps:
- Registered a Codex MCP server named `obsidian` using the supported Streamable HTTP URL + bearer [REDACTED] var pattern.
- Added `/home/ethan/.codex/hooks/obsidian_vault_update.py`, a marker-driven Stop hook helper that only writes when an assistant response contains an explicit `<codex-vault-update>` block.
- Added tests for the hook’s marker parsing, path rejection, secret rejection, and session-text extraction.
- Updated `/home/ethan/.codex/hooks.json` to run the new Obsidian hook after the existing NPM reconciliation Stop hook.
- Updated `/home/ethan/.codex/AGENTS.md` so future Codex runs know when to emit a vault-update marker and when not to.
- Verified the hook by dry-run, by live marker-driven write, and by reading the note back through the REST API.

Failures and how to do differently:
- The first attempt to run hook tests used global `pytest`, which was missing on PATH; using the already-created project virtualenv’s pytest worked.
- There was ambiguity around Codex hook trust hashes; the hook script and config were installed and tested, but a future Codex session may still prompt for trust depending on its hook-state model.
- The assistant intentionally avoided using a marker in its final response while recording hook setup notes, to prevent recursive hook-triggered writes.

Reusable knowledge:
- The hook is intentionally marker-driven: no `<codex-vault-update>` block means no write.
- Allowed auto-write areas: `Homelab/Documentation/`, `Homelab/Projects/`, `Homelab/Memory/`, `Work/Projects/`, `Vault Admin/`, and `Personal/Miscellaneous/AI Working Memory.md`.
- The hook rejects Therapy, hidden technical folders, ambiguous Personal notes, and secret-like content.
- Hook state is persisted in `/home/ethan/.codex/obsidian-vault-hook-state.json` to avoid duplicate writes.
- The hook log is `/home/ethan/.codex/obsidian-vault-hook.log`.

References:
- [1] `/home/ethan/.codex/hooks/obsidian_vault_update.py`
- [2] `/home/ethan/.codex/hooks/test_obsidian_vault_update.py`
- [3] `/home/ethan/.codex/hooks.json`
- [4] `/home/ethan/.codex/AGENTS.md`
- [5] `PYTHONPATH=/home/ethan/.codex/hooks /home/ethan/obsidian-api-mcp/.venv/bin/pytest -q /home/ethan/.codex/hooks/test_obsidian_vault_update.py` -> `8 passed`
- [6] Live marker write returned `HTTP:204` and the written note read back `HTTP:200`

## Task 4: Determine whether LiveSync is fully functional without a 24/7 UI Obsidian client

Outcome: partial
