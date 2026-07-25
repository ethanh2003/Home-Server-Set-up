# 2026-07-12T22-20-29-FKWF-dockhand_traefik_add_then_rollback

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f586a-e80c-7612-b651-0baf1a227475
updated_at: 2026-07-12T23:12:47+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/12/rollout-2026-07-12T22-20-29-019f586a-e80c-7612-b651-0baf1a227475.jsonl
cwd: /home/ethan

# Dockhand was briefly added to Traefik, then the change was reverted after the user said it broke everything.

Rollout context: In `/home/ethan/docker`, the user first asked to correct a Dockhand compose file without starting it, then clarified that it should be added to Traefik. The Traefik wiring was implemented and later immediately undone when the user said it broke everything. The undo left the earlier standalone Dockhand compose file in place.

## Task 1: Add Dockhand, then revert the Traefik integration

Outcome: success

Preference signals:
- When the user corrected the scope with "you were meant to add it to trafik", they wanted service exposure to be implemented through Traefik file-provider routing, not just as a host-port compose stack.
- When the user then said "Undo it broke everything", they wanted immediate rollback of the last change only, with no extra cleanup or unrelated edits.
- The user’s correction sequence suggests future similar work should confirm whether a service should be standalone or Traefik-routed before editing, and should revert narrowly and quickly if the new route causes problems.

Key steps:
- Initially created `/home/ethan/docker/dockhand/docker-compose.yml` and validated it with `docker compose config`.
- After the user clarified Traefik was the goal, changed Dockhand to join `proxy_net` and added `traefik/dynamic/dockhand.yml` routing `dockhand.ethanh.online` and `dockhand.ethan-herring.com` to `http://dockhand:3000`.
- After the user reported the change broke everything, removed the Traefik route file and restored the standalone compose shape with `3001:3000`.
- Verified both `docker compose config --quiet` checks passed and that no `dockhand` container was running.

Failures and how to do differently:
- The first compose version used a host port conflict-free standalone setup, but the user wanted Traefik integration instead.
- The Traefik addition should be treated as a reversible, isolated change; when the user says it broke everything, revert only the last route wiring and leave the rest of the repo untouched.
- Before making future service exposures, ask whether the target is Traefik or standalone compose if the request is ambiguous, because the user may be sensitive to unintended routing changes.

Reusable knowledge:
- Dockhand was expected to run with `DATA_DIR: /home/ethan/docker/dockhand/data` and a bind mount to the same path.
- The Traefik integration pattern in this repo is a file-provider YAML under `traefik/dynamic/` with an `http.routers` entry and `http.services` pointing at the service name on `proxy_net`.
- `dockhand` was not left running after either the add or revert.

References:
- [1] Added then removed: `/home/ethan/docker/traefik/dynamic/dockhand.yml`.
- [2] Restored standalone compose: `/home/ethan/docker/dockhand/docker-compose.yml` with `ports: - "3001:3000"`.
- [3] Validation commands that passed: `cd /home/ethan/docker/dockhand && docker compose config --quiet`, `cd /home/ethan/docker/traefik && docker compose config --quiet`.
- [4] Status evidence after undo: `docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' | rg 'traefik|npm|cloudflared|dockhand'` showed `npm` healthy, `traefik` up, `cloudflared_tunnel` up, and no `dockhand` container.
