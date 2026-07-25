# 2026-06-29T15-19-23-Zz1Y-komga_fix_and_stash_buffering_diagnosis

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f13f6-b5f9-71d3-a8ba-0b51b56d07ee
updated_at: 2026-06-29T15:55:59+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/29/rollout-2026-06-29T15-19-23-019f13f6-b5f9-71d3-a8ba-0b51b56d07ee.jsonl
cwd: /home/ethan

# Fixed Komga startup and diagnosed Stash buffering as non-server-side

Rollout context: homelab debugging from `/home/ethan`, with live Docker/Nginx Proxy Manager checks against public hostnames. The assistant used the required debugging/verification workflow and verified fixes with fresh commands before claiming success.

## Task 1: Fix `https://komga.ethan-herring.com/`

Outcome: success

Preference signals:
- The user gave a terse outage report: `fix https://komga.ethan-herring.com/` -> for service outages, the user wants direct incident response grounded in live evidence, not a long back-and-forth.

Key steps:
- Checked the public URL first and confirmed `HTTP/1.1 502 Bad Gateway` from openresty.
- Found the `komga` container in a restart loop and then read its logs.
- Root cause from logs: Komga failed during SQLite initialization with `SQLITE_CANTOPEN Unable to open the database file`.
- Compared the compose file and mount state: `/home/ethan/docker/stash/config/komga` was bind-mounted into `/config`, but the host directory was `root:root` while the container runs as `1000:1000`.
- Passwordless sudo was available, so the agent used `sudo chown -R 1000:1000 /home/ethan/docker/stash/config/komga`, restarted only `komga`, and let it complete startup.
- Verified with fresh evidence: Komga applied Flyway migrations, Tomcat started on port `25600`, `docker inspect` showed `running=true` and `restart_count=0`, `http://komga:25600/` returned 200, and `https://komga.ethan-herring.com/` returned 200.

Failures and how to do differently:
- The first plain `chown` failed with `Operation not permitted`; switching to `sudo` was required for the host-owned bind mount.
- The raw post-fix log filter initially still included old crash attempts; narrowing the log window to after successful startup was necessary for a meaningful verification.

Reusable knowledge:
- For Komga, `SQLITE_CANTOPEN` during startup can be caused by bind-mount ownership on `/config`, not only by a missing database file.
- In this stack, Komga’s config lived under `/home/ethan/docker/stash/config/komga`, and the service runs as UID/GID `1000:1000`.
- The live public hostname was fronted by Nginx Proxy Manager/openresty; 502 here meant upstream container failure, not necessarily proxy config failure.

References:
- Public failure: `HTTP/1.1 502 Bad Gateway`
- Root-cause log snippet: `Failed to initialize pool: [SQLITE_CANTOPEN] Unable to open the database file`
- Compose mount: `source: ./config/komga`, `target: /config`; container user `1000:1000`
- Fix command: `sudo chown -R 1000:1000 /home/ethan/docker/stash/config/komga && docker compose -f /home/ethan/docker/stash/docker-compose.yml restart komga`
- Verification: `docker inspect komga ... status=running ... restart_count=0`, `https://komga.ethan-herring.com/` -> `HTTP/1.1 200`

## Task 2: Diagnose why `stash.ethanh.online` was buffering badly

Outcome: partial

Preference signals:
- The user asked: `why is stash.ethanh.online buffering so bad` -> they want a root-cause diagnosis, not guesswork.
- The assistant explicitly reused prior Stash/NPM context, which implies future similar homelab outages should check historical routing/migration notes and live state together.

Key steps:
- Verified the public host and the direct upstream separately.
- Confirmed `stash.ethanh.online` resolves locally to `192.168.1.113`, so the host is being hit directly on the LAN.
- Inspected NPM’s live SQLite DB and generated config. There are two enabled Stash rows for the same hostnames: one active row forwards to Docker service `stash:9999`, and one stale row forwards to `192.168.1.102:9999`.
- Checked the generated NPM vhost file `nginx-proxy-manager/nginx_config/data/nginx/proxy_host/10.conf`; it currently forwards to `stash` on port `9999`, so the stale DB row is not the active route.
- Measured direct throughput with `curl` range fetches:
  - `http://stash:9999/scene/1160/stream` inside the NPM network was very fast.
  - `https://stash.ethanh.online/scene/1160/stream` was also fast from this host.
  - A 100 MiB range fetch returned 206 quickly from both localhost and the public hostname.
- Pulled Stash logs and saw lots of normal preview/sprite/GraphQL/range activity from a browser client at `192.168.1.234`, including some long preview/sprite fetches, but no sign of transcode CPU saturation or backend failure.
- Queried scene `1160` via GraphQL; it is a direct-served 1080p H.264/AAC MP4 at about 5.1 Mbps and appears twice under two `/data/...` paths, indicating duplicate library-path metadata from migration.
- Confirmed the server-side container CPU was low and the filesystem had plenty of space.

Failures and how to do differently:
- `sudo rg` failed because `rg` was not in the sudo environment; using plain `grep` or invoking `rg` without sudo would avoid that tool-path mismatch.
- One attempt to run curl inside the NPM container had quoting issues and returned `curl: option : blank argument where content is expected`; the host-side curl and simpler container tests were sufficient.
- The evidence points away from Stash throughput as the bottleneck, so further work should target the actual client/WAN/Wi-Fi/browser path rather than more server-side tuning unless a new symptom appears.

Reusable knowledge:
- `stash.ethanh.online` currently resolves to the LAN address `192.168.1.113`, so this host’s local tests bypass Cloudflare and hit NPM directly.
- The active generated NPM config for Stash is `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/nginx/proxy_host/10.conf`, forwarding to `stash:9999`.
- NPM’s DB still contains a stale duplicate Stash row pointing at `192.168.1.102`, which is a cleanup risk but not the active path.
- `scene/1160` is not an unusually heavy encode: 1080p, H.264/AAC, ~5.1 Mbps, direct file serving.
- Stash logs showed client requests with many small preview/sprite/GraphQL calls and large range GETs; buffering on one client is more likely a client/Wi-Fi/WAN/Cloudflare-tunnel issue than a raw origin throughput problem.

References:
- DNS/LAN resolution: `stash.ethanh.online -> 192.168.1.113`
- NPM DB rows:
  - active: `forward_host='stash'`, `forward_port=9999`
  - stale duplicate: `forward_host='192.168.1.102'`, `forward_port=9999`
- Generated vhost: `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/nginx/proxy_host/10.conf`
- Scene metadata via GraphQL: `findScene(id: 1160)` shows `files[0].bit_rate = 5061318`, `width=1920`, `height=1080`, `video_codec=h264`, `audio_codec=aac`
- Throughput samples:
  - direct: `code=206 size=104857600 time=0.073901 speed=1418892843`
  - public: `code=206 size=104857600 time=0.251735 speed=416539615`
- Logs showing client-side activity: Stash access logs for `192.168.1.234` during scene browsing/streaming
