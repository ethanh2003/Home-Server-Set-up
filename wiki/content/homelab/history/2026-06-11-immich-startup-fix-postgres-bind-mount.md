# 2026-06-11T18-53-26-S6XT-immich_startup_fix_postgres_bind_mount

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019eb808-348b-7d82-bafa-8839fca8eac9
updated_at: 2026-06-11T18:55:46+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/11/rollout-2026-06-11T18-53-26-019eb808-348b-7d82-bafa-8839fca8eac9.jsonl
cwd: /home/ethan

# Immich stack repair by switching the Postgres data bind mount

Rollout context: The user asked to "fix immich" in `/home/ethan`. The Immich stack lives in `/home/ethan/docker/immich` and is managed with Docker Compose. The fix was about runtime startup failure, not Compose syntax.

## Task 1: Fix Immich startup failure

Outcome: success

Preference signals:
- The user only said "fix immich" and did not specify a narrower symptom -> future runs should start by inspecting the live stack, recent logs, and compose/env wiring before making assumptions.

Key steps:
- Found the Immich compose stack at `/home/ethan/docker/immich/docker-compose.yml` and the environment in `/home/ethan/docker/immich/.env`.
- `docker compose config` succeeded, so the problem was not YAML syntax.
- `docker compose ps` / logs showed Postgres restarting and Immich server errors like `getaddrinfo ENOTFOUND immich_postgres`.
- The live bind mount `database/postgres` was a partial/incomplete Postgres data directory; `database/postgres_pg14_backup` contained a full initialized cluster.
- Updated `.env` so `DB_DATA_LOCATION=./database/postgres_pg14_backup` instead of `./database/postgres`.
- Recreated the stack with `docker compose up -d --force-recreate database redis immich-machine-learning immich-server`.
- Verified Postgres, Redis, Immich server, and machine learning all reached healthy state after startup.

Failures and how to do differently:
- The first `docker compose ps` output showed the Postgres container still restarting; that was a transient state during the recreate, not the final state. Future checks should wait briefly and re-poll before concluding failure.
- Immich logs still mention older ML URLs from saved system config (`http://192.168.1.106:3003` and `http://192.168.1.129:3003`), but that was non-blocking because the stack came up healthy.

Reusable knowledge:
- In this Immich setup, the effective Postgres data path is controlled by `.env` via `DB_DATA_LOCATION`, and the live container mounts that value into `/var/lib/postgresql/data`.
- A bad/partial Postgres bind mount can cause the image to loop on startup with `initdb: error: directory "/var/lib/postgresql/data" exists but is not empty` and leave Immich unable to resolve `immich_postgres`.
- `docker compose config` is useful here to confirm the rendered mount path and env expansion before restarting anything.
- The working stack used the external network `proxy_net` and container names `immich_postgres`, `immich_redis`, `immich_server`, and `immich_machine_learning`.

References:
- [1] `/home/ethan/docker/immich/.env` originally had `DB_DATA_LOCATION=./database/postgres`; it was changed to `./database/postgres_pg14_backup`.
- [2] `docker compose logs --no-color --tail=80 database` showed `PostgreSQL Database directory appears to contain a database; Skipping initialization` and later `database system is ready to accept connections` after the fix.
- [3] `docker compose ps` after settling showed all services healthy:
  - `immich_postgres ... Up ... (healthy)`
  - `immich_redis ... Up ... (healthy)`
  - `immich_server ... Up ... (healthy)`
  - `immich_machine_learning ... Up ... (healthy)`
- [4] The problematic runtime symptom before the fix was `Error: getaddrinfo ENOTFOUND immich_postgres` in Immich server logs, caused by Postgres crash-looping.
