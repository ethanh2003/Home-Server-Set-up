# 2026-07-11T02-58-18-dShz-obsidian_livesync_mobile_debugging

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f4f1c-8a46-7e00-a494-18e243221a71
updated_at: 2026-07-11T03:02:15+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/11/rollout-2026-07-11T02-58-18-019f4f1c-8a46-7e00-a494-18e243221a71.jsonl
cwd: /home/ethan

# Investigated why Obsidian LiveSync was struggling on mobile and found the server/proxy path healthy, with the likely problem on the mobile client side.

Rollout context: The user reported that their Obsidian LiveSync was struggling on mobile. The work was done from `/home/ethan`, with the existing LiveSync stack under `/home/ethan/docker/obsidian-livesync` and the vault plugin config under `/data/Obsidian/Main/.obsidian/plugins/obsidian-livesync`.

## Task 1: Diagnose mobile LiveSync slowness / sync failure

Outcome: uncertain

Preference signals:
- No strong new durable preference signal emerged beyond the user’s short report that mobile LiveSync was struggling; this looked like a one-off debugging request rather than a reusable instruction.

Key steps:
- Read prior Obsidian/LiveSync memory first to recover the known stack shape: CouchDB backend at `/home/ethan/docker/obsidian-livesync`, public hostname `obsidian.ethan-herring.com`, Cloudflare/NPM in front, and the vault API/MCP intentionally separate from sync.
- Checked the stack status: `obsidian-livesync-couchdb` was up and healthy, NPM and cloudflared were running, and CouchDB responded on `5984`.
- Verified the public path with authenticated requests to `https://obsidian.ethan-herring.com/`, `/therapy`, and a long-poll `_changes` request; the 60s long-poll completed normally with `pending:0`.
- Inspected CouchDB logs and saw a burst from mobile/client IP `192.168.8.207` around `2026-07-11 01:22 UTC`: hundreds of successful `_revs_diff`, `_local/...` GET/PUT, and `_bulk_docs` requests in a short window, with a few expected initial `_local/...` 404s.
- Checked the database state: `therapy` had about 11.2k docs, no active tasks, no scheduler jobs, no conflicts, no deleted-doc buildup, and no obvious server-side errors.
- Inspected the Obsidian LiveSync plugin config on disk and found `manifest.json` version `0.25.76`, `liveSync: true`, `keepReplicationActiveInBackground: true`, `readChunksOnline: true`, and `concurrencyOfReadChunksOnline: 100` in `data.json`.
- Searched the plugin bundle for relevant settings; the output was extremely large because `main.js` is bundled/minified, but it confirmed the settings are present in the plugin config file.
- Attempted to use a quick `jq`-based parser, but `jq` was not installed; the fallback Python inspection succeeded.
- Looked at the troubleshooting/docs on GitHub for LiveSync and used them only as background guidance.

Failures and how to do differently:
- The evidence did not point to a backend outage, proxy timeout, or CouchDB corruption; the mobile traffic succeeded, so a server-side “fix” would have been guesswork.
- The `jq` path failed because `jq` was missing; use Python for JSON inspection on this host when needed.
- The better next move is to focus on the mobile client/device: confirm the exact URI shape, reproduce with mobile logs, and lower overly aggressive client-side sync settings before touching the server.

Reusable knowledge:
- `obsidian-livesync-couchdb` was healthy, with no restarts and no OOM; `docker inspect` showed `RestartCount=0`, `OOMKilled=false`, `Health=healthy`.
- Public authenticated `/_changes?feed=longpoll&since=now&timeout=65000&limit=1` through `https://obsidian.ethan-herring.com` completed normally in about 60s, so Cloudflare/NPM was not killing long-poll requests.
- The server logs showed the mobile client doing a concentrated burst of successful checkpoint and replication calls (`_revs_diff`, `_local/...`, `_bulk_docs`) rather than obvious rejected requests.
- The plugin config on disk showed a notably high `concurrencyOfReadChunksOnline: 100`, which is a plausible mobile-side stressor to check first if the phone is slow or stuck.

References:
- [1] `docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' | rg -i 'obsidian|couch|npm|cloudflared|nginx|proxy'` → `obsidian-livesync-couchdb` healthy, `npm` healthy, `cloudflared_tunnel` up.
- [2] `curl -fsS -u "$COUCHDB_USER:$COUCHDB_PASSWORD" http://127.0.0.1:5984/` → CouchDB `3.5.2` welcome JSON.
- [3] `curl ... https://obsidian.ethan-herring.com/therapy/_changes?feed=longpoll&since=now&timeout=65000&limit=1` → `200` after `60.19s`, `pending:0`.
- [4] CouchDB log pattern from mobile IP: repeated successful `POST /therapy/_revs_diff 200`, `GET /therapy/_local/... 200`, `PUT /therapy/_local/... 201`, `POST /therapy/_bulk_docs 201` around `01:22 UTC`.
- [5] `/data/Obsidian/Main/.obsidian/plugins/obsidian-livesync/manifest.json` → version `0.25.76`.
- [6] `/data/Obsidian/Main/.obsidian/plugins/obsidian-livesync/data.json` → `liveSync: true`, `keepReplicationActiveInBackground: true`, `readChunksOnline: true`, `concurrencyOfReadChunksOnline: 100`, `syncMinimumInterval: 2000`.
