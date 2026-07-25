# 2026-07-11T00-43-00-Z0NX-dawarich_stack_npm_cloudflare_followup

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f4ea0-ac01-7d01-95fa-0bfe9da35c51
updated_at: 2026-07-11T02:04:06+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/11/rollout-2026-07-11T00-43-00-019f4ea0-ac01-7d01-95fa-0bfe9da35c51.jsonl
cwd: /home/ethan/Documents/Codex/2026-07-11-add-dawarich-to-my-stacks-npm

# Dawarich stack deployment, NPM routing, and a blocked Cloudflare public-route follow-up

Rollout context: The user asked to add Dawarich to the homelab stacks and include NPM. The agent first inferred local stack/NPM conventions from `/home/ethan/docker`, the live NPM SQLite DB, and Dawarich upstream Compose/docs. The user then clarified that all three owned domains should be used for new stacks. After Dawarich was deployed and wired through NPM, the user later asked how to log in, then asked to use Cloudflare to make the `ethan-herring.com` hostname public. That Cloudflare follow-up hit an auth/credential blocker. Finally, the user asked for an Obsidian vault note, which was written.

## Task 1: Add Dawarich to the Docker homelab and NPM

Outcome: success

Preference signals:

- When asked to choose hostnames, the user clarified: "Use all 3 domains i own for all new stacks" -> future new stacks should default to all three owned domains rather than asking for a per-stack hostname decision.
- When the agent suggested Cloudflare Access as a possible gate for the later public-route question, the user replied: "Ugh just do whatever is going to be easiest for me" -> the user prefers the least-friction option, even if it means using app-native auth instead of adding extra access layers.

Key steps:

- Checked `/home/ethan/docker` conventions, live containers, and NPM SQLite rows before editing.
- Created `/home/ethan/docker/dawarich/docker-compose.yml` and `README.md`; generated an ignored `/home/ethan/docker/dawarich/.env` with secrets.
- Used the upstream Dawarich service shape: app, Sidekiq, PostGIS, and Redis.
- Attached `dawarich_app` to `proxy_net` and kept DB/Redis internal.
- Added NPM proxy rows `146` and `147` for the three owned domains, using certificate `4` for `ethanh.online` + `ethan-herring.com` and certificate `5` for `pup-percy.com`.
- Verified with `docker compose config --services`, `docker compose ps`, internal health check, `docker exec npm nginx -t`, and HTTPS smoke checks.

Failures and how to do differently:

- The first healthcheck used plain HTTP to the app’s health endpoint, but Dawarich forced an HTTPS redirect internally, so Puma logged `Invalid HTTP format... Are you trying to open an SSL connection to a non-SSL Puma?`. The fix was to send `Host: dawarich.ethanh.online` and `X-Forwarded-Proto: https` in the healthcheck.
- Do not assume a plain local health probe works for Dawarich; use forwarded HTTPS headers for the app health endpoint.

Reusable knowledge:

- `/home/ethan/docker` is a one-folder-per-stack homelab layout, and `manage-stacks.sh` discovers stacks via `docker-compose.yml`.
- `proxy_net` is the shared external network for user-facing containers.
- The live NPM routing truth lives in `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite` and generated files under `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/nginx/proxy_host/`.
- For this Dawarich deployment, the effective public pattern was one NPM row for `ethanh.online` + `ethan-herring.com` and one for `pup-percy.com`.

References:

- [1] `/home/ethan/docker/dawarich/docker-compose.yml` — Dawarich stack definition with `dawarich_app`, `dawarich_sidekiq`, `dawarich_db`, `dawarich_redis`
- [2] `/home/ethan/docker/dawarich/README.md` — ops notes and public URLs
- [3] NPM DB backup: `/home/ethan/docker/nginx-proxy-manager/backups/database.sqlite.pre-dawarich-npm-20260711T010011Z`
- [4] NPM proxy rows created: `146.conf`, `147.conf`; `nginx -t` passed after regeneration
- [5] Verification evidence: `docker compose ps` showed all four containers healthy; `curl` to each public hostname returned `200`

## Task 2: Cloudflare public route follow-up for `dawarich.ethan-herring.com`

Outcome: partial

Preference signals:

- When the agent proposed Cloudflare Access or extra browser/login layers, the user said: "just do whatever is going to be easiest for me" -> for future Cloudflare/public-route work, prefer the simplest route that does not introduce extra access friction.
- The user specifically asked: "Using @cloudflare make the ethan-herring one public" -> they wanted the `ethan-herring.com` hostname exposed publicly, not just LAN/NPM-only access.

Key steps:

- Inspected the existing `cloudflared` stack and logs.
- Found the tunnel ID in `cloudflared` logs: `88f9a354-ec72-4cc6-9248-fb50c7fd2209`.
- Verified that local split-horizon DNS still resolved `dawarich.ethan-herring.com` to `192.168.1.113` on LAN, while public DNS for the name was `NXDOMAIN`.
- Confirmed the current cloudflared tunnel config did not include Dawarich.
- Confirmed the tunnel runtime token could not update Cloudflare API config (`Authentication failed (status: 400)` when calling the tunnel configuration endpoint with the token).

Failures and how to do differently:

- The rollout could not complete the Cloudflare public-route change because the shell lacked `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_ZONE_ID`, and a usable Cloudflare API auth context.
- The Cloudflare tunnel token is opaque and is not enough by itself to modify tunnel configuration via the Cloudflare API.
- Future similar work should first check whether Cloudflare API credentials are present before promising a public DNS/tunnel change.

Reusable knowledge:

- The Cloudflare tunnel token can reveal the tunnel ID indirectly from `cloudflared` logs, but it cannot be used as a substitute for an API token when updating remote config.
- LAN reachability through NPM does not prove public Cloudflare exposure; confirm with public DNS resolvers.
- The user’s lowest-friction preference here was to avoid Cloudflare Access in front of Dawarich so app/mobile/API auth remains simple.

References:

- [6] `cloudflared` tunnel ID from logs: `88f9a354-ec72-4cc6-9248-fb50c7fd2209`
- [7] API auth failure: `Authentication failed (status: 400)` when using the tunnel token against the Cloudflare tunnel config endpoint
- [8] Public DNS check for `dawarich.ethan-herring.com`: `NXDOMAIN`
- [9] LAN smoke: `https://dawarich.ethan-herring.com` returned `200` locally via NPM, showing LAN-only access

## Task 3: Write the Dawarich note into Obsidian

Outcome: success

Preference signals:

- The user asked: "Add a note with that to my obsidian vault" -> they want important rollout outcomes captured in the vault, not only in chat.

Key steps:

- Appended the Dawarich runtime / NPM / Cloudflare follow-up note to `/data/Obsidian/Main/Homelab/Memory/Dawarich.md`.
- Verified the file contained the new Cloudflare follow-up section.

Reusable knowledge:

- The Obsidian vault is mounted at `/data/Obsidian/Main`.
- A concise homelab memory note should include stack path, public URLs, NPM row IDs, backup path, verification, and any blocked follow-up state.

References:

- [10] `/data/Obsidian/Main/Homelab/Memory/Dawarich.md`
- [11] Appended section title: `## Cloudflare Public Route Follow-Up`
