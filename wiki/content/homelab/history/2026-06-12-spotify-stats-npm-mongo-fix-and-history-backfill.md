# 2026-06-12T19-54-51-XO9d-spotify_stats_npm_mongo_fix_and_history_backfill

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019ebd66-cbe3-72c2-bd2a-1a6fdc2747bb
updated_at: 2026-06-12T20:51:11+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/12/rollout-2026-06-12T19-54-51-019ebd66-cbe3-72c2-bd2a-1a6fdc2747bb.jsonl
cwd: /home/ethan

# Spotify stats stack was configured for the public domain, then debugged through a Mongo crash that caused NPM 502s; the user also asked whether listening history can be backfilled.

Rollout context: working in `/home/ethan/docker/spotify-stats` on a Your Spotify deployment behind Nginx Proxy Manager (`proxy_net`), with public hostnames under `ethanh.online`.

## Task 1: Set up and stabilize Spotify stats behind NPM

Outcome: success

Preference signals:
- When asked what to manually add to NPM, the user wanted exact proxy entries rather than guesswork; the answer that matched the final working setup used split hostnames (`spotify.ethanh.online` for the web UI and `spotify-api.ethanh.online` for the API).
- When the user reported `https://spotify-api.ethanh.online/oauth/spotify got 502 bad gateway`, they expected the agent to trace each layer (public URL, NPM config, container reachability, backend) rather than assume an app bug.
- The user later interrupted and explicitly said to use “any accessible files tools or scripts as well as @browser,” indicating comfort with using local files/scripts plus browser verification when diagnosing stack issues.

Key steps:
- Inspected `/home/ethan/docker/spotify-stats/docker-compose.yml` and `.env`, then updated endpoints from localhost to the public domain.
- Removed host port publishes for `web` and `server` because `3000` and `8080` were already occupied locally; the stack already lived on `proxy_net`, so ingress was meant to come through NPM.
- Confirmed NPM proxy hosts in its SQLite DB: host `96` for `spotify.ethanh.online -> web:3000` and host `97` for `spotify-api.ethanh.online -> server:8080`.
- Verified the API route inside NPM with `curl http://server:8080/oauth/spotify`, which returned a `302 Found` and the correct redirect URI `https://spotify-api.ethanh.online/oauth/spotify/callback`.
- The real outage was Mongo: `mongo:8` repeatedly exited with code `139`, so the Spotify backend never kept a listener up on `8080` and NPM surfaced `502 Bad Gateway`.
- Recovery path that worked: preserved the old Mongo data directories by renaming them, reinitialized a fresh bind-mounted DB, then pinned Mongo to `mongo:7`, added `restart: always`, added a smaller WiredTiger cache, added a healthcheck, and made the server wait for Mongo health before starting.
- Verified the final fix with a 2-minute hold: `mongo` stayed healthy with `restarts=0`, `https://spotify-api.ethanh.online/oauth/spotify` continued to return `302 Found`, and `https://spotify.ethanh.online` returned `200 OK`.

Failures and how to do differently:
- The initial assumption that NPM was broken was wrong; the upstream backend was failing because Mongo was unstable. Future similar 502s should be checked against backend container listener state (`netstat`/`curl` inside NPM) before touching proxy config.
- `mongo:8` latest was unstable on this host even after fresh reinitialization, so pinning to `mongo:7` was the durable fix.
- The Mongo 8 data files should not be downgraded in place; preserving them under timestamped names before switching versions avoided destructive loss.

Reusable knowledge:
- For this stack, the working public routing is split-host NPM: `spotify.ethanh.online -> web:3000`, `spotify-api.ethanh.online -> server:8080`.
- The Spotify OAuth redirect URI that needs to be registered is `https://spotify-api.ethanh.online/oauth/spotify/callback`.
- The Spotify backend listens on `8080` when healthy; if `curl http://server:8080/oauth/spotify` returns `Connection refused`, the issue is inside the stack, not NPM.
- The compose file now uses a Mongo healthcheck plus `depends_on: condition: service_healthy` for the server, which prevents the backend from racing a not-yet-ready database.

References:
- [1] `/home/ethan/docker/spotify-stats/.env` final values:
  - `API_ENDPOINT=https://spotify-api.ethanh.online`
  - `CLIENT_ENDPOINT=https://spotify.ethanh.online`
- [2] `/home/ethan/docker/spotify-stats/docker-compose.yml` final key changes:
  - `mongo:7`
  - `restart: always`
  - `command: ["mongod", "--wiredTigerCacheSizeGB", "0.25"]`
  - healthcheck ping via `mongosh`
  - `server` depends on Mongo health
- [3] NPM DB rows:
  - `(96, '["spotify.ethanh.online"]', 'http', 'web', 3000, 1, '[]', '')`
  - `(97, '["spotify-api.ethanh.online"]', 'http', 'server', 8080, 1, '[]', '')`
- [4] Successful verification outputs:
  - `curl -skI https://spotify-api.ethanh.online/oauth/spotify` → `HTTP/1.1 302 Found` with `redirect_uri=https://spotify-api.ethanh.online/oauth/spotify/callback`
  - `curl -skI https://spotify.ethanh.online` → `HTTP/1.1 200 OK`
  - `docker inspect mongo ...` → `image=mongo:7 status=running health=healthy restarts=0`
- [5] Preserved old DB directories:
  - `/home/ethan/docker/spotify-stats/your_spotify_db.corrupt-20260612`
  - `/home/ethan/docker/spotify-stats/your_spotify_db.mongo8-crash-20260612-2046`

## Task 2: Ask whether listening history can be backfilled

Outcome: success

Preference signals:
- The user asked a direct capability question: “is it possible to manually or automatically backfill my listening history,” indicating they want concise, actionable guidance on what the app supports and the practical import path.

Key steps:
- Checked current Your Spotify docs and Spotify export guidance.
- Answered that automatic backfill is limited: the app records new listens going forward and only fetches about the last 24 hours by API default.
- Recommended manual backfill via Spotify data export and import into Your Spotify settings.

Failures and how to do differently:
- None significant; the answer should stay grounded in what the app/docs support and avoid implying full historical API sync is possible.

Reusable knowledge:
- Your Spotify supports importing past history from Spotify export files; for fuller history, request Spotify’s extended streaming history/full privacy data, then import in the app’s Settings.
- Regular Spotify account data exports are faster but more limited than extended streaming history.

References:
- Your Spotify import docs: `https://github.com/Yooooomi/your_spotify#importing-past-history`
- Spotify privacy/data export info: `https://support.spotify.com/us/article/data-rights-and-privacy-settings/`
- Spotify import workflow reference used during lookup: `https://support.stats.fm/docs/import/spotify-import/`
