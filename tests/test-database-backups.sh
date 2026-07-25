#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TEST_ROOT=$(mktemp -d)
trap 'rm -rf "$TEST_ROOT"' EXIT

mkdir -p "$TEST_ROOT/bin" "$TEST_ROOT/backups"

cat > "$TEST_ROOT/bin/docker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' "$*" >> "$FAKE_DOCKER_CALL_LOG"

if [[ "${FAKE_DOCKER_FAIL_MATCH:-}" != "" && "$*" == *"$FAKE_DOCKER_FAIL_MATCH"* ]]; then
    printf 'injected failure\n' >&2
    exit 23
fi

case "$1" in
    exec)
        printf 'valid backup payload for %s\n' "$*"
        ;;
    cp)
        printf 'valid copied backup payload for %s\n' "$*" > "${3}"
        ;;
    *)
        printf 'unexpected docker action: %s\n' "$1" >&2
        exit 2
        ;;
esac
EOF
chmod +x "$TEST_ROOT/bin/docker"

export PATH="$TEST_ROOT/bin:$PATH"
export BACKUP_DIR="$TEST_ROOT/backups"
export BACKUP_LOCK_FILE="$TEST_ROOT/database-backup.lock"
export BACKUP_METRICS_FILE="$TEST_ROOT/backup.prom"
export FAKE_DOCKER_CALL_LOG="$TEST_ROOT/docker.calls"
export PAPERLESS_EXPORT_ENABLED=0

if grep -q 'new SQLite3' "$REPO_ROOT/backup_databases.sh"; then
    echo "FAIL: LinkStack image does not provide the PHP SQLite3 class" >&2
    exit 1
fi

if ! grep -q 'VACUUM INTO' "$REPO_ROOT/backup_databases.sh"; then
    echo "FAIL: LinkStack export does not use its available PDO SQLite runtime" >&2
    exit 1
fi

printf 'last known good dump\n' > "$BACKUP_DIR/wiki.sql"
chmod 600 "$BACKUP_DIR/wiki.sql"
export FAKE_DOCKER_FAIL_MATCH="wiki-db"

set +e
"$REPO_ROOT/backup_databases.sh"
failure_status=$?
set -e

if [[ "$failure_status" -ne 23 ]]; then
    echo "FAIL: expected injected Docker status 23, got $failure_status" >&2
    exit 1
fi

if [[ "$(cat "$BACKUP_DIR/wiki.sql")" != "last known good dump" ]]; then
    echo "FAIL: a failed export overwrote the last known-good Wiki dump" >&2
    exit 1
fi

if ! grep -q '^homelab_backup_last_run_success 0$' "$BACKUP_METRICS_FILE"; then
    echo "FAIL: failed backup did not publish a failure metric" >&2
    exit 1
fi

if find "$BACKUP_DIR" -maxdepth 1 -type f -name '.*.tmp.*' | grep -q .; then
    echo "FAIL: failed export left temporary files behind" >&2
    exit 1
fi

echo "PASS: a failed export preserves the last known-good dump"

rm -f "$FAKE_DOCKER_CALL_LOG"
unset FAKE_DOCKER_FAIL_MATCH
"$REPO_ROOT/backup_databases.sh"

if ! grep -q '^homelab_backup_last_run_success 1$' "$BACKUP_METRICS_FILE"; then
    echo "FAIL: successful backup did not publish a success metric" >&2
    exit 1
fi

if ! grep -Eq '^homelab_backup_last_success_timestamp_seconds [0-9]+$' "$BACKUP_METRICS_FILE"; then
    echo "FAIL: successful backup metric has no timestamp" >&2
    exit 1
fi

expected_files=(
    immich.sql
    dawarich.sql
    wiki.sql
    spotify-mongo.archive.gz
    obsidian-livesync-couchdb.tar.gz
    home-assistant.db
    home-assistant-2.db
    linkstack.db
)

for backup_file in "${expected_files[@]}"; do
    path="$BACKUP_DIR/$backup_file"
    if [[ ! -s "$path" ]]; then
        echo "FAIL: expected non-empty backup $backup_file" >&2
        exit 1
    fi
    if [[ "$(stat -c '%a' "$path")" != "600" ]]; then
        echo "FAIL: expected mode 600 on $backup_file" >&2
        exit 1
    fi
done

if [[ -e "$BACKUP_DIR/planka.sql" ]]; then
    echo "FAIL: retired Planka backup is still produced" >&2
    exit 1
fi

for required_container in immich_postgres dawarich_db wiki-db mongo obsidian-livesync-couchdb HomeAssistant HomeAssistant2 linkstack-linkstack-1; do
    if ! grep -q "$required_container" "$FAKE_DOCKER_CALL_LOG"; then
        echo "FAIL: no export command was issued for $required_container" >&2
        exit 1
    fi
done

echo "PASS: all active database exports are atomic, non-empty, and private"

mkdir -p "$TEST_ROOT/paperless-export/nested"
printf 'sensitive manifest fixture\n' > "$TEST_ROOT/paperless-export/manifest.json"
chmod 755 "$TEST_ROOT/paperless-export" "$TEST_ROOT/paperless-export/nested"
chmod 644 "$TEST_ROOT/paperless-export/manifest.json"
export PAPERLESS_EXPORT_ENABLED=1
export PAPERLESS_EXPORT_DIR="$TEST_ROOT/paperless-export"

"$REPO_ROOT/backup_databases.sh" >/dev/null

if [[ "$(stat -c '%a' "$PAPERLESS_EXPORT_DIR")" != "700" ]] ||
    [[ "$(stat -c '%a' "$PAPERLESS_EXPORT_DIR/manifest.json")" != "600" ]]; then
    echo "FAIL: Paperless plaintext export permissions were not restricted" >&2
    exit 1
fi

echo "PASS: Paperless plaintext export is restricted to its owner"
