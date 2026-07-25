# vault-inbox Operations Runbook Design

## Goal

Create a production operations documentation slice for `vault-inbox` that makes deployment, verification, host Codex worker operation, Cloudflare Access readiness, and recovery steps repeatable.

## Design

The README remains the quick-start entrypoint. Detailed operator procedures live in `docs/operations/production-runbook.md`, grouped by the real production responsibilities:

- Docker API/PWA deployment and health verification.
- Host Codex worker installation, status checks, logs, one-shot processing, and stale-running recovery behavior.
- Queue operations for capture fallback, reruns, historical attempts, and successful idle state.
- Vault Git safety checks and protected-path policy expectations.
- Cloudflare Access setup through both dashboard steps and `scripts/cloudflare-vault-inbox-access.py`.
- Common incident procedures that preserve vault content and avoid destructive commands.

## Production Invariants

- The Docker container keeps `VAULT_INBOX_CODEX_ENABLED=false` and `VAULT_INBOX_WORKER_ENABLED=false`.
- Authenticated Codex execution runs from `vault-inbox-host-worker.service` on the host.
- Cloudflare Access must protect `https://inbox.ethan-herring.com` before off-LAN use.
- Vault Git should be clean before and after automated processing.
- Runtime data, logs, generated caches, private vault content, and secrets are not committed.

## Verification

The implementation should run the existing backend tests, frontend build, Playwright E2E checks, Docker Compose config validation, container health check, host worker status check, queue-rerun check, and vault Git cleanliness check.
