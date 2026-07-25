# 2026-07-05T02-22-20-oBOs-vault_inbox_ops_runbook_documentation

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f3015-73c8-7882-adca-46326e711edc
updated_at: 2026-07-05T17:57:48+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/05/rollout-2026-07-05T02-22-20-019f3015-73c8-7882-adca-46326e711edc.jsonl
cwd: /home/ethan/docker/vault-inbox
git_branch: main

# Added a production operations runbook for vault-inbox and kept the README as a quick-start.

Rollout context: The user asked to continue planning/implementation and ensure best practices and proper documentation. This became a documentation-only slice in `/home/ethan/docker/vault-inbox` focused on production operations, not runtime feature changes.

## Task 1: Define the documentation slice
Outcome: success

Preference signals:
- The user asked to "continue planning and implimentation, we need to ensure we are following best practices and have proper documentation" -> future similar work should default to documentation-first planning, not immediate code churn.
- When asked to choose the doc scope, the user selected "Ops Runbook (Recommended)" and then "Single Runbook (Recommended)" -> future documentation work should prefer one concrete operator runbook over many small docs when the system is tightly coupled.
- For Cloudflare setup, the user effectively accepted the combined manual + script approach (no alternative was chosen after the question) -> future runbooks should document both dashboard steps and script-based dry-run/apply paths when API permissions may vary.

Key steps:
- Read the existing README, deploy/service files, Cloudflare script, and repo doc layout before writing anything.
- Confirmed the repository already had strong ops/testing coverage and that the right place for durable ops guidance was `docs/operations/`.
- Kept README as quick-start and moved detail into a runbook.

Failures and how to do differently:
- None material. The main constraint was to avoid replacing the README with a long operator manual; the solution was to add a short pointer instead.

Reusable knowledge:
- This repo already has a useful ops automation script at `scripts/cloudflare-vault-inbox-access.py`; the runbook should reference it rather than re-describing Cloudflare API payloads from scratch.
- The right documentation structure for this repo is: README for quick start, `docs/operations/production-runbook.md` for operator procedures, and `docs/superpowers/specs/...` for the design record.

References:
- [1] Approved doc targets: `docs/operations/production-runbook.md` and `docs/superpowers/specs/2026-07-05-vault-inbox-operations-runbook-design.md`.
- [2] Cloudflare dry-run script command that worked with dummy env values:
  `CLOUDFLARE_API_TOKEN=[REDACTED] CLOUDFLARE_ACCOUNT_ID=acct CLOUDFLARE_ZONE_ID=zone CLOUDFLARE_TUNNEL_ID=00000000-0000-0000-0000-000000000000 CLOUDFLARE_ZERO_TRUST_TEAM_NAME=example python3 scripts/cloudflare-vault-inbox-access.py`

## Task 2: Write the production operations runbook and design record
Outcome: success

Preference signals:
- The user wanted "proper documentation" and this rollout confirmed the user values concrete operational guidance rather than just code comments.
- The Cloudflare question path ended with the manual+script framing, so the runbook should cover both dashboard steps and scripted dry-run/apply commands.

Key steps:
- Added `docs/operations/production-runbook.md` with sections for:
  - Docker deploy and health verification
  - host Codex worker install/status/logs/one-shot processing
  - queue operations and job state meanings
  - vault Git safety and protected-path policy
  - Cloudflare Access setup
  - common incidents and recovery steps
  - release verification checklist
- Added `docs/superpowers/specs/2026-07-05-vault-inbox-operations-runbook-design.md` to preserve the approved design.
- Updated `README.md` to point at the runbook and keep the quick-start concise.

Failures and how to do differently:
- The first Cloudflare script snippet exposed a secret-redaction artifact in the transcript; future memory/notes should avoid storing raw secret-shaped values and prefer command shape plus placeholders.
- The initial README had duplicated/expanded operational detail; the final shape worked better by moving those details into the runbook.

Reusable knowledge:
- The runbook should state the container invariants explicitly: `VAULT_INBOX_CODEX_ENABLED=false` and `VAULT_INBOX_WORKER_ENABLED=false` in Docker; host worker does Codex execution.
- The Cloudflare guidance should be framed as: Access self-hosted app + Tunnel public hostname route + optional script dry-run/apply.
- The docs verification benchmark for this repo can be non-destructive and command-oriented; syntax-valid or dry-run commands are enough for documentation changes.

References:
- [1] New docs files:
  - `docs/operations/production-runbook.md`
  - `docs/superpowers/specs/2026-07-05-vault-inbox-operations-runbook-design.md`
- [2] README addition: `## Production Operations` now points to `docs/operations/production-runbook.md`.
- [3] Runbook command examples that were verified in context:
  - `docker compose build && docker compose up -d`
  - `docker inspect -f '{{.State.Status}} {{.State.Health.Status}}' vault-inbox`
  - `docker exec vault-inbox curl -fsS http://127.0.0.1:8080/api/health`
  - `systemctl --user status vault-inbox-host-worker.service --no-pager`
  - `git -C /data/Obsidian/Main status --short --untracked-files=all`

## Task 3: Validate docs against live environment and preserve the vault note trail
Outcome: success

Preference signals:
- The user’s emphasis on best practices and proper documentation was matched by a runbook that includes explicit verification, recovery, and no-destructive-ops guidance.
- The rollout used the existing host-vault workflow and committed a new operational note, suggesting future similar work should preserve operator notes in the vault when they are valid and policy-compliant.

Key steps:
- Ran the full verification pass after docs changes:
  - backend tests
  - frontend build
  - Playwright E2E
  - Docker Compose config validation
  - container health check
  - queue-rerun check
  - host worker status check
  - vault Git cleanliness check
  - Cloudflare script dry run
- Found one dirty vault note under `Homelab/Memory/vault-inbox.md`; validated it with the app policy engine and committed it instead of deleting it.
- Re-ran the full verification after that vault commit and confirmed the vault tree was clean.

Failures and how to do differently:
- The first vault-cleanliness check surfaced an allowed operational memory note. Future runs should expect that notes written by the vault workflow may need to be committed rather than treated as stray dirty state.
- A couple of command invocations initially had malformed shell arguments or were missing the correct path; the final pass used the exact commands embedded in the runbook and avoided those issues.

Reusable knowledge:
- The live verification baseline for docs/ops changes in this repo is now well-defined: `30 passed` backend tests, frontend build, `3 passed` Playwright tests, container `running healthy`, `/api/health` redacted and OK, `queue-reruns` returns `queued: 0`, host worker active, and vault Git clean.
- The host worker service file is installed at `/home/ethan/.config/systemd/user/vault-inbox-host-worker.service` and runs `python -m vault_inbox.host_worker` with the backend venv.
- Cloudflare Access dry run works with dummy environment values and prints payloads without making live changes.

References:
- [1] Final verification evidence:
  - `backend/.venv/bin/python -m pytest -q` -> `30 passed, 1 warning`
  - `(cd frontend && npm run build && npm run test:e2e)` -> `3 passed`
  - `docker inspect -f '{{.State.Status}} {{.State.Health.Status}}' vault-inbox` -> `running healthy`
  - `docker exec vault-inbox curl -fsS http://127.0.0.1:8080/api/health` -> `{"app":{"ok":true,"name":"vault-inbox"},"vault":{"ok":true},"codex":{"enabled":false},"ollama":{"model":"nomic-embed-text"},"smtp":{"enabled":true}}`
  - `docker exec vault-inbox curl -fsS -X POST http://127.0.0.1:8080/api/commands/queue-reruns` -> `{"ok":true,"queued":0,"jobs":[]}`
  - `systemctl --user status vault-inbox-host-worker.service --no-pager` -> `active (running)` and `enabled`
  - `git -C /data/Obsidian/Main status --short --untracked-files=all` -> clean after committing the operational note
- [2] Vault note commit created during verification:
  - `cd0b9d3 Record vault-inbox production worker status`
- [3] Cloudflare dry-run result:
  - `python3 scripts/cloudflare-vault-inbox-access.py` with dummy env printed Access app, policy, DNS, and tunnel payloads and ended with `Dry run only. Re-run with --apply after reviewing payloads.`
