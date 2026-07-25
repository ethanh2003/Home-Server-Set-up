# 2026-06-20T03-35-52-gvkx-homelab_iac_npm_to_traefik_wiki_transition

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019ee319-644e-7f23-8575-3eab44ee9ad5
updated_at: 2026-06-26T07:03:23+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/20/rollout-2026-06-20T03-35-52-019ee319-644e-7f23-8575-3eab44ee9ad5.jsonl
cwd: /home/ethan

# Homelab IaC migration, then NPM-to-Traefik staging with wiki transition routes

Rollout context: The user started with a broad homelab request to move fully to infrastructure-as-code with Git tracking, self-hosted runners, and Renovate-managed container updates. They then refined it to include Nginx Proxy Manager as IaC, secrets extraction so arr services can be re-linked after rebuilds, and finally asked whether to migrate from NPM to Traefik. The work happened in `/home/ethan/docker`, which already had many unrelated uncommitted changes, so the implementation had to stay additive and backup-first.

## Task 1: Build the homelab IaC scaffolding, runner stack, Renovate, and SOPS secret flow

Outcome: success

Preference signals:
- When the user said they wanted to "migrate fully to infastructure as code with full git tracking and selfhosted runners and renovate to update containers (a configurable number of days after releases)," that established the default future expectation: treat the repo as the source of truth, add self-hosted CI, and make container update timing configurable.
- When asked about runner hosting, the user chose "Container runner (Recommended)", indicating a preference for containerized self-hosted runners over host services.
- When asked about update policy, the user chose "Automerge patch/minor", so low-risk container updates should be able to auto-merge after checks rather than always requiring manual PR review.
- When asked about deployment behavior, the user chose "Auto deploy main", so merges to main should generally drive live deployment rather than leaving deploys entirely manual.
- When asked about secrets, the user chose "SOPS age (Recommended)", indicating encrypted secrets should be committed and decrypted only on the runner/host, not stored as plaintext `.env`.
- When asked about Renovate delay, the user chose "7 days (Recommended)", so the default release-age buffer for container updates should be seven days.

Key steps:
- Added a small shell-based IaC test harness first and used it as the red-green anchor.
- Implemented shared scripts for stack validation, changed-stack detection, deploy-on-change, and SOPS decryption.
- Added a containerized GitHub Actions runner stack under `github-runner/` and verified it could build successfully.
- Added `renovate.json5` with 7-day release age, digest pinning, and patch/minor automerge.
- Added `.sops.yaml`, docs for the runner and IaC workflow, and `.gitignore` entries for encrypted env files and runner workdirs.
- Verified the new script test harness, full Compose validation, JSON5/YAML parsing, and runner image build.

Failures and how to do differently:
- The first workflow/config syntax checks needed adjustment because the host lacked some helper binaries; future checks should prefer parsers that are actually present locally or install them in CI.
- The repo had significant pre-existing dirty state. The implementation had to avoid touching unrelated files and should continue to be treated as additive rather than a clean-room refactor.
- The final deploy workflow was intentionally not exercised against live stacks; future work should keep that separation until a dedicated deploy gate is available.

Reusable knowledge:
- `docker compose config --services` is not enough on its own here; `docker compose config` across each stack is the useful validation shape, because several stacks use env-file indirection.
- The host had `docker` but not `sops`, `age`, `shellcheck`, `jq`, or `actionlint` installed initially, so workflow checks that depend on those tools should not assume they exist on the host.
- The runner image build used `ghcr.io/actions/actions-runner:2.335.1` and built cleanly.
- `proxy_net` remains the shared external network for user-facing services in this repo.

References:
- [1] New IaC scripts: `scripts/iac-validate.sh`, `scripts/iac-changed-stacks.sh`, `scripts/iac-deploy-changed.sh`, `scripts/secrets-decrypt.sh`.
- [2] Runner stack: `github-runner/docker-compose.yml`, `github-runner/Dockerfile`, `github-runner/entrypoint.sh`.
- [3] Renovate config: `renovate.json5` with `minimumReleaseAge: "7 days"`, Docker digest pinning, patch/minor automerge.
- [4] Verification evidence: `./tests/test-iac-scripts.sh` passed; `./scripts/iac-validate.sh` passed across the stack tree; `docker compose build` succeeded for `github-runner`.

## Task 2: Move NPM toward IaC, stage Traefik, and make wiki accessible during the transition

Outcome: partial

Preference signals:
- When the user said "This should also include NPM being infastrucutre as code, as well as you pulling all api keys into their respective areas to ensure they can easily re-link for the arr stack," that established that proxy state should be tracked, and that arr-related API keys should live in service-specific, recoverable places.
- When asked whether NPM desired state should include all current rows or only active Compose-managed services, the user chose "All current rows (Recommended)", so the initial NPM IaC inventory should preserve the full live routing set, including LAN targets and older rows, rather than pruning aggressively.
- When the user asked "eh what about migrating from npm to trafick", they were explicitly considering a Traefik target-state reverse proxy, but the rollout also showed they still needed NPM as the live edge during migration.
- When the user later said "i cant access it with npm still being the main router unless upi add it to npm", that was a strong correction: during the Cloudflare/NPM transition, the wiki hostnames must exist in NPM as temporary proxy rows until Cloudflare is repointed to Traefik.
- When the user pasted a Wiki.js token, the interaction showed they wanted the wiki fully published and reachable, not merely documented as a future cutover item.

Key steps:
- Inspected the live NPM SQLite DB and current generated NPM proxy host files to ground the Traefik migration in the actual live routing table.
- Built `scripts/traefik-route-parity.py` and a regression test so staged Traefik routes could be compared against NPM’s effective behavior, not just raw status codes.
- Added `scripts/cloudflare-tunnel-cutover.py` as a guarded backup/dry-run/apply/rollback helper for remote tunnel config updates, but the rollout could not complete the actual Cloudflare write because no API token/env was available in the shell.
- Fixed staged Traefik parity issues for specific hosts, including a Cockpit self-signed backend via an insecure servers transport, and confirmed the staged parity scan passed.
- Updated the Traefik migration runbook and regenerated wiki content after each documentation change.
- Fixed `scripts/wiki-sync.py` for the live Wiki.js v2 GraphQL schema (`singleByPath(path, locale)` instead of `single(path, locale)`), then successfully published 52 wiki pages and verified a GraphQL page lookup.
- Added temporary NPM proxy rows for the wiki hostnames so the wiki was reachable while NPM remained the active edge:
  - NPM proxy host `104` for `wiki.ethan-herring.com` and `wiki.ethanh.online`
  - NPM proxy host `105` for `wiki.pup-percy.com`
  Both point to `wikijs:3000`.
- Backed up the NPM SQLite DB before editing and reloaded NPM successfully; local and public checks returned `200` for all three wiki hostnames.

Failures and how to do differently:
- The actual Cloudflare cutover was blocked because `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, and `CLOUDFLARE_TUNNEL_ID` were not available in the shell, and no callable Cloudflare tunnel-management tool was exposed in the session.
- Local hostname resolution on this host points the domains at `192.168.1.113`, so some `curl` checks only prove LAN/NPM behavior, not the off-LAN Cloudflare edge. Future cutover verification should distinguish local resolver results from public resolver/edge behavior.
- The first version of the Wiki.js publish logic used the wrong GraphQL lookup shape and failed against Wiki.js v2. The fix was to inspect the live schema and switch to `singleByPath(path, locale)`.
- The Cloudflare helper correctly failed at the credential boundary; future attempts should not expect remote tunnel changes to work until the API token and IDs are supplied.

Reusable knowledge:
- The live NPM DB lives at `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite`.
- NPM’s certificate table includes separate cert ids; the wiki transition used cert `4` for `ethan-herring.com`/`ethanh.online` and cert `5` for `pup-percy.com`.
- NPM can resolve `wikijs` on `proxy_net`, so temporary transition proxy hosts can point directly at `wikijs:3000`.
- The live Wiki.js GraphQL schema exposes page lookup as `pages.singleByPath(path, locale)` and mutations `create(...)` / `update(id, ...)`.
- The wiki sync tool now publishes successfully with the current Wiki.js schema and can be used to keep `wiki/content/` and the live site in sync.
- NPM reload warnings about duplicate `nextcloud.ethanh.online` server names are pre-existing and did not block the wiki transition.

References:
- [1] Temporary NPM wiki proxy hosts: `nginx-proxy-manager/nginx_config/data/nginx/proxy_host/104.conf`, `105.conf`; DB rows inserted for ids `104` and `105`.
- [2] Traefik staging: `traefik/dynamic/npm-migration.yml`, `scripts/traefik-route-parity.py`, `tests/test-traefik-route-parity.py`.
- [3] Cloudflare cutover helper: `scripts/cloudflare-tunnel-cutover.py`.
- [4] Wiki fixes: `scripts/wiki-sync.py` and `tests/test-wiki-sync.py` updated for `singleByPath`; published successfully with `Published 52 pages to https://wiki.ethan-herring.com`.
- [5] Wiki access verification: local/public checks returned `200` for `wiki.ethan-herring.com`, `wiki.ethanh.online`, and `wiki.pup-percy.com` after adding the temporary NPM rows.

Overall outcome:
- The homelab IaC scaffolding is in place and validated.
- Traefik is staged and parity-checked.
- Wiki.js is published and reachable through NPM transition routes.
- Full migration to Traefik/Cloudflare is not yet complete because the Cloudflare write path and final edge cutover still need credentials and a final external verification pass.
