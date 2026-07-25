# Stack: vault-inbox

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `vault-inbox/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: no
- README: yes

## Project Status

- Runtime: not checked
- Project status: operational
- Last verified: 2026-07-04

## Remaining Tasks

- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

## Evidence

- Compose file: `vault-inbox/docker-compose.yml`
- Compose tracked in Git: yes
- README: yes
- SOPS env: no
- Git status for stack path: omitted
- Live runtime state is monitored in Prometheus and omitted from deterministic wiki output.

## Services

- `vault-inbox`

## Images

- No images parsed.

## Operations

```bash
cd /home/ethan/docker/vault-inbox
docker compose config
docker compose ps
```

## Notes

# vault-inbox

`vault-inbox` is a self-hosted PWA and backend control plane for Ethan's Obsidian second brain.

## Current v1 Capabilities

- Mobile-first capture composer for text, URLs, and pasted Markdown batches.
- Android PWA share target for shared text/URLs.
- SQLite-backed captures, jobs, audit events, validation failures, and note index tables.
- Command center for vault validation, policy sync, local Git initialization, processing one queued job, reindexing, SMTP test, Ollama check, and dashboard generation.
- Guardrail policy engine for protected paths, secret-like files, old Therapy history, and required Markdown frontmatter.
- Capture-only fallback that writes to `Vault Admin/Inbox/YYYY-MM-DD.md` and marks jobs for rerun when Codex processing is disabled or fails.
- Host-side Codex worker support with policy diff validation before committing vault changes.
- Local-only vault Git initialization with protected `.gitignore` rules.
- Generated Obsidian dashboard and policy copies under `Vault Admin/`.

## Deployment

```bash
cd /home/ethan/docker/vault-inbox
docker compose build
docker compose up -d
```

The service listens on port `8080` inside `proxy_net`. Route `inbox.ethan-herring.com` through the existing Cloudflare Tunnel and reverse proxy to `vault-inbox:8080`.

## Production Operations

Use [docs/operations/production-runbook.md](docs/operations/production-runbook.md) for production deployment, health checks, host Codex worker operation, queue recovery, vault Git safety, and Cloudflare Access setup.

## Safety Defaults

- `VAULT_INBOX_CODEX_ENABLED=false` and `VAULT_INBOX_WORKER_ENABLED=false` remain the safe container defaults. Production Codex processing should run from the host worker so Codex auth stays on the host.
- API docs and detailed health output are disabled by default. Enable `VAULT_INBOX_DOCS_ENABLED=true` or `VAULT_INBOX_HEALTH_DETAILS_ENABLED=true` only on trusted admin surfaces.
- URL ingestion blocks localhost, private, link-local, multicast, reserved, and unspecified network targets by default.
- Old Therapy transcripts, summaries, and archive notes are protected.
- Hidden folders, plugin config, trash, secret-like files, and private runtime logs are protected.
- SMTP alerts go to `admin@ethan-herring.com` when AI organization falls back to capture-only.

## Host Codex Worker

The Docker container intentionally does not mount `/home/ethan/.codex` or run the authenticated Codex CLI. Production Codex processing runs through the host user service template at `deploy/vault-inbox-host-worker.service`; operational commands and recovery steps are in the production runbook.

## Cloudflare Access

Target public hostname:

```text
https://inbox.ethan-herring.com
```

Recommended Cloudflare setup:

- Zero Trust Access application: self-hosted app named `vault-inbox`
- Public hostname: `inbox.ethan-herring.com`
- Tunnel service URL: `http://vault-inbox:8080` from the `cloudflared` container on `proxy_net`
- Access policy: Allow only `echerring.ech@gmail.com`
- Protect with Access: enabled on the Tunnel public hostname route

Manual dashboard steps and the script-based dry-run/apply flow are documented in the production runbook.

## Local Development

Backend:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest
uvicorn vault_inbox.app:app --reload --port 8080
```

Frontend:

```bash
cd frontend
npm install
npm run build
npm run test:e2e
npm run dev
```

## Important Follow-Ups

- Verify Cloudflare Access before using `inbox.ethan-herring.com` off-LAN; command-center actions are intentionally open behind the trusted Access boundary.
- Expand schema validation as the first staged cleanup dry-run reveals real note patterns.
