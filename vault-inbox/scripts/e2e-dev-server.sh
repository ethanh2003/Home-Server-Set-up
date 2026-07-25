#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${VAULT_INBOX_E2E_TMP:-$(mktemp -d)}"
API_PORT="${VAULT_INBOX_E2E_API_PORT:-18080}"
WEB_PORT="${VAULT_INBOX_E2E_WEB_PORT:-5173}"
BACKEND_PID=""

cleanup() {
  if [[ -n "${BACKEND_PID}" ]]; then
    kill "${BACKEND_PID}" 2>/dev/null || true
  fi
  if [[ -z "${VAULT_INBOX_E2E_TMP:-}" ]]; then
    rm -rf "${TMP_DIR}"
  fi
}
trap cleanup EXIT

mkdir -p "${TMP_DIR}/data" "${TMP_DIR}/repo" "${TMP_DIR}/vault/Homelab/Memory"
cat > "${TMP_DIR}/vault/Homelab/Memory/Fixture Memory.md" <<'EOF'
---
note_type: homelab_memory
tags:
  - homelab/memory
---
# Fixture Memory

This fixture-memory note proves the E2E search path uses the backend.
EOF

export VAULT_INBOX_DATABASE_PATH="${TMP_DIR}/data/vault-inbox.sqlite3"
export VAULT_INBOX_VAULT_ROOT="${TMP_DIR}/vault"
export VAULT_INBOX_APP_REPO_ROOT="${TMP_DIR}/repo"
export VAULT_INBOX_CODEX_ENABLED=false
export VAULT_INBOX_SMTP_ENABLED=false
export VAULT_INBOX_WORKER_ENABLED=false
export VAULT_INBOX_DOCS_ENABLED=false
export VAULT_INBOX_HEALTH_DETAILS_ENABLED=false

"${ROOT}/backend/.venv/bin/python" -m uvicorn vault_inbox.app:app --host 127.0.0.1 --port "${API_PORT}" >/tmp/vault-inbox-e2e-api.log 2>&1 &
BACKEND_PID="$!"

for _ in {1..80}; do
  if curl -fsS "http://127.0.0.1:${API_PORT}/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

export VITE_API_PROXY_TARGET="http://127.0.0.1:${API_PORT}"
cd "${ROOT}/frontend"
npm run dev -- --host 127.0.0.1 --port "${WEB_PORT}"
