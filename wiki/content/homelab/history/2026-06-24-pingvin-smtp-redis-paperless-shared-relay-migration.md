# 2026-06-24T02-34-20-v0AG-pingvin_smtp_redis_paperless_shared_relay_migration

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019ef77a-7ca0-77e1-bd92-09a6362a60ba
updated_at: 2026-06-24T03:56:20+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/24/rollout-2026-06-24T02-34-20-019ef77a-7ca0-77e1-bd92-09a6362a60ba.jsonl
cwd: /home/ethan/docker
git_branch: main

# Docker homelab service setup and SMTP consolidation across Pingvin, SMTP relay, Redis, and Paperless

Rollout context: Work happened in `/home/ethan/docker`. The repo is a homelab Docker stack with `proxy_net`, Nginx Proxy Manager, and several existing services. The user repeatedly asked for concrete repo changes, then later asked to consolidate SMTP onto a shared local relay and finally to add Redis and migrate Paperless outbound mail to that relay. Several actions required preserving existing unrelated dirty changes and one compose file (`paperless-ngx/docker-compose.yml`) was already modified before the SMTP edit.

## Task 1: Set up Pingvin Share and make it UI-managed

Outcome: success

Preference signals:
- The user’s request was minimal (“Setup pingven share”), but later follow-ups showed they wanted the app usable on multiple domains and wanted UI-managed settings rather than a mounted config file. That suggests future stack setup should default to a working multi-domain deployment, not just the primary hostname.
- When the UI showed “Configuration file present… you can't change the configuration through the UI. I want ui level changes,” the user clearly preferred DB/UI-backed settings over a mounted config file. Future Pingvin runs should avoid mounting `/opt/app/config.yaml` unless the user explicitly wants config locked down.

Key steps:
- Chose the maintained fork `smp46/pingvin-share-x` after checking upstream docs/repo state.
- Created the Pingvin stack under `/home/ethan/docker/pingvin-share` and used `proxy_net` with no host ports.
- Verified the app start failed with a mounted config file because the fork expected `initUser.enabled` in the config object; fixed by removing the config mount and seeding equivalent settings into Pingvin’s SQLite DB.
- Added extra NPM routes for `share.ethan-herring.com` and `share.pup-percy.com`, using certificate ids `4` and `5` respectively, while keeping `share.ethanh.online` as the canonical `appUrl`.
- Documented the setup in `pingvin-share/README.md` and removed the local `config.yaml` file after proving the UI-managed path.

Failures and how to do differently:
- Mounting Pingvin config as a file caused the UI to reject edits. The fix was to remove the mount entirely and seed DB-backed config values instead.
- `sqlite3` was not installed, so DB inspection had to use Python `sqlite3`.

Reusable knowledge:
- Pingvin Share X works on `proxy_net` behind NPM and should be validated with `docker compose config`, `docker exec pingvin-share curl -fsS http://localhost:3000/api/health`, and a public HTTPS `200` check.
- NPM proxy rows were inserted directly into the SQLite DB, then matched with config files under `nginx-proxy-manager/nginx_config/data/nginx/proxy_host/`.
- `share.ethanh.online` remained the canonical `general.appUrl` even after adding alternate hostnames.

References:
- Pingvin stack: `/home/ethan/docker/pingvin-share/docker-compose.yml`
- NPM routes: `101.conf`, `102.conf`, `103.conf`
- NPM DB backup: `nginx-proxy-manager/nginx_config/data/database.sqlite.bak-pingvin-*`
- Final public checks returned `200` for all three hostnames.

## Task 2: Add a shared SMTP relay and point Pingvin at it

Outcome: success

Preference signals:
- The user asked for SMTP “using a consistent docker server and Ethan-herring.com domain that will link to Gmail where my domain email is hosted,” which indicates they wanted a stable internal relay container rather than app-specific SMTP credentials scattered in each stack.
- When they asked “Can you setup a Google admin map i can log into so you can configure that?”, that exposed a preference for a shared relay plus Google Workspace-side allowlisting, but the environment had no Google Admin connector. Future similar requests should mention that direct Google Admin configuration may not be possible from this session and provide the exact admin page/setting needed.
- The user later said “Try now” and the relay test succeeded, confirming they wanted the environment validated end-to-end after the allowlist change.

Key steps:
- Added `/home/ethan/docker/smtp-relay/docker-compose.yml` using `boky/postfix:latest` on `proxy_net` with `RELAYHOST=smtp-relay.gmail.com:587`, `POSTFIX_myhostname=smtp.ethan-herring.com`, and `POSTFIX_mynetworks` including the Docker subnet `172.25.0.0/16`.
- Documented the Google Workspace SMTP relay allowlist step in `smtp-relay/README.md`, including the host public IP `24.148.58.137`.
- Seeded Pingvin’s SMTP config in its SQLite DB so settings stay UI-managed, using `smtp-relay:587` and sender `no-reply@ethan-herring.com`.
- Verified the relay path twice: first Google rejected mail with `Mail relay denied [24.148.58.137]`, then after the allowlist was active, a fresh test returned `status=sent (250 2.0.0 OK ... - gsmtp)`.

Failures and how to do differently:
- The first relay test reached Google but was rejected because the IP was not yet registered in Google Workspace SMTP relay settings. This is a useful confirmation signal: a `250` from the local relay does not mean Google has accepted delivery.
- The environment only exposed a Google Calendar connector, not Google Admin/Admin SDK, so direct admin-side configuration was not possible here.

Reusable knowledge:
- Shared relay contract: app containers on `proxy_net` should use host `smtp-relay`, port `587`, no app SMTP username/password, sender `no-reply@ethan-herring.com`.
- Google Workspace allowlist must include the host public IP; in this rollout that IP was `24.148.58.137`.
- Good verification path: send from a container through `smtp-relay`, then inspect `smtp-relay` logs for `status=sent` vs `status=bounced`.

References:
- Relay compose: `/home/ethan/docker/smtp-relay/docker-compose.yml`
- Relay logs showed the crucial Google rejection and later acceptance.

## Task 3: Add Redis to Pingvin Share

Outcome: success

Preference signals:
- The user simply asked “Can you also add redis” and then explicitly approved the proposed approach. That suggests for similar small service additions, the agent should propose the minimal internal service approach first and then implement it in-place.

Key steps:
- Added `redis:8-alpine` as `pingvin-redis` inside `pingvin-share/docker-compose.yml`, with append-only persistence at `pingvin-share/redis-data`, healthcheck, and `depends_on` for Pingvin.
- Updated Pingvin’s DB-backed cache settings to `cache.redis-enabled=true` and `cache.redis-url=redis://redis:6379`.
- Restarted Pingvin to pick up the cache settings and verified both `pingvin-share` and `pingvin-redis` were healthy.
- Confirmed the cache config stayed UI-managed by reading the DB rows; the public config API did not expose the cache settings directly.

Failures and how to do differently:
- `docker compose config` for the Pingvin stack had to be run directly rather than relying on the config API; the API doesn’t surface cache keys.
- The app logs showed the cache module starting cleanly, but that alone was not enough; the DB rows and Redis `PONG` were the better proof.

Reusable knowledge:
- Pingvin’s cache settings already exist in its SQLite DB as `cache.redis-enabled`, `cache.redis-url`, `cache.ttl`, and `cache.maxItems`.
- Redis should live on `proxy_net` and be addressed by service name `redis` from Pingvin, not by the container name `pingvin-redis`.
- The live stack accepted `redis-cli ping` and Pingvin remained healthy after restart.

References:
- Compose: `/home/ethan/docker/pingvin-share/docker-compose.yml`
- Redis data dir: `/home/ethan/docker/pingvin-share/redis-data`
- DB backup: `pingvin-share/data/pingvin-share.db.bak-redis-*`

## Task 4: Migrate Paperless outbound email to the shared SMTP relay

Outcome: success

Preference signals:
- The user approved the proposed approach and later explicitly said “Implement the proposed plan.” That suggests future SMTP-related changes should proceed from a concise plan into execution once approved, rather than waiting for repeated confirmation.
- The user asked to “check all instances of docker composes using stmp and plan how to migrate them to this shared stmp instance,” and then specifically approved the scope “Outbound only (Recommended).” That indicates the user wanted outbound notification mail migrated, but not mailbox-bridge services or dormant configs.
- When asked about Google Admin access, the user wanted a log-in-able path, but the environment could not access Google Admin directly; future agents should proactively state that limitation and provide the exact admin steps.

Key steps:
- Inspected compose files and confirmed the active SMTP-related candidates were mostly `smtp-relay` itself, Paperless’s DavMail bridge, and dormant BookStack mail keys in a `.env` without a running BookStack compose.
- Kept DavMail unchanged because it is a mailbox/Exchange bridge, not the outbound SMTP relay target.
- Added outbound email env vars to `paperless-ngx/docker-compose.yml`:
  - `PAPERLESS_EMAIL_HOST=smtp-relay`
  - `PAPERLESS_EMAIL_PORT=587`
  - `PAPERLESS_EMAIL_FROM=no-reply@ethan-herring.com`
  - empty host user/password
  - TLS/SSL disabled from Paperless to the local relay
- Documented the shared SMTP contract in `paperless-ngx/README.md`.
- Recreated only the Paperless webserver container, leaving DavMail and the rest of the stack untouched.
- Verified with a Django `send_mail(...)` test from inside the Paperless container; `smtp-relay` logs showed Google accepted the message with `status=sent (250 2.0.0 OK ... - gsmtp)`.

Failures and how to do differently:
- `docker compose config` for `paperless-ngx` initially failed because `paperless-ngx/.env` was permission-restricted for the non-sudo user. The workaround was to use `sudo -n docker compose ... config` and `sudo -n docker compose ... up -d webserver`.
- `paperless-ngx/docker-compose.yml` already had an unrelated export-path change before the SMTP edit; future agents should preserve such pre-existing diffs.
