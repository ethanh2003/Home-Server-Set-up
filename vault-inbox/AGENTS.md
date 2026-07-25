# Repository Guidelines

## Project Structure & Module Organization
`vault-inbox` is a self-hosted PWA and FastAPI control plane for an Obsidian vault. Backend code lives in `backend/src/vault_inbox/`, with tests in `backend/tests/`. Frontend code lives in `frontend/src/`, public PWA assets in `frontend/public/`, and production build output in `frontend/dist/`. Guardrail policy YAML files are in `policies/`. Runtime SQLite data and logs are mounted through `data/` and `logs/`; do not commit secrets or private vault content from those paths.

## Build, Test, and Development Commands
Backend setup:
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
npm run dev
npm run build
```
Deployment:
```bash
docker compose build
docker compose up -d
```
Use `docker logs --tail 80 vault-inbox` and `/api/health` for runtime checks.

## Coding Style & Naming Conventions
Use Python 3.11+ with 4-space indentation, typed functions where practical, and small modules grouped by responsibility. Backend files use `snake_case.py`; tests use `test_*.py`. React/TypeScript code should keep component logic clear and colocated in `frontend/src/`; prefer readable names over abbreviations.

## Testing Guidelines
Backend tests use `pytest` and are configured by `backend/pyproject.toml`. Add focused tests for policy validation, queue behavior, vault writes, command-center actions, and failure paths. Run `pytest` before backend changes and `npm run build` before frontend changes.

## Commit & Pull Request Guidelines
Use concise conventional-style commits seen in this repo family, such as `feat: add capture queue` or `fix: separate legacy validation backlog`. Pull requests should include a short summary, test results, screenshots for PWA UI changes, and notes for Docker, vault, policy, or security-impacting changes.

## Security & Configuration Tips
`VAULT_INBOX_CODEX_ENABLED=false` is the safe default. Do not commit tokens, private `.env` values, raw Codex logs, Obsidian secrets, or Therapy content. Treat `/data/Obsidian/Main` as the source of truth and preserve protected path rules when changing vault write behavior.
