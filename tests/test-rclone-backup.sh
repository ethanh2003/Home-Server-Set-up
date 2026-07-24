#!/bin/bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TEST_ROOT=$(mktemp -d)
trap 'rm -rf "$TEST_ROOT"' EXIT

mkdir -p "$TEST_ROOT/bin"
cp "$REPO_ROOT/rclone_backup.sh" "$TEST_ROOT/rclone_backup.sh"

# Keep the pre-lock production script from touching the live log during the
# RED test. The production script will natively support this override.
sed -i \
    's#^LOG_FILE=.*#LOG_FILE="${RCLONE_BACKUP_LOG_FILE:-'"$TEST_ROOT"'/rclone.log}"#' \
    "$TEST_ROOT/rclone_backup.sh"

cat > "$TEST_ROOT/bin/rclone" <<'EOF'
#!/bin/bash
printf '%s\n' "$*" >> "$RCLONE_CALL_LOG"
if [[ "$1" == "sync" ]]; then
    prefix="output"
    if [[ "${FAKE_RCLONE_FAIL:-0}" == "1" ]]; then
        prefix="error"
    fi
    for number in $(seq 1 25); do
        printf '%s-line-%s\n' "$prefix" "$number"
    done
    if [[ "${FAKE_RCLONE_FAIL:-0}" == "1" ]]; then
        exit 7
    fi
fi
exit 0
EOF
chmod +x "$TEST_ROOT/bin/rclone"

export PATH="$TEST_ROOT/bin:$PATH"
export RCLONE_CALL_LOG="$TEST_ROOT/rclone.calls"
export RCLONE_BACKUP_LOCK_FILE="$TEST_ROOT/rclone.lock"
export RCLONE_BACKUP_LOG_FILE="$TEST_ROOT/rclone.log"

exec 8>"$RCLONE_BACKUP_LOCK_FILE"
flock -n 8
"$TEST_ROOT/rclone_backup.sh"

if [[ -e "$RCLONE_CALL_LOG" ]]; then
    echo "FAIL: rclone ran while the backup lock was already held" >&2
    exit 1
fi

if ! grep -q "already running" "$RCLONE_BACKUP_LOG_FILE"; then
    echo "FAIL: lock contention was not recorded in the backup log" >&2
    exit 1
fi

echo "PASS: a held lock prevents a second backup"

flock -u 8
rm -f "$RCLONE_CALL_LOG" "$RCLONE_BACKUP_LOG_FILE"
for number in $(seq 1 20); do
    printf 'old-history-%s\n' "$number" >> "$RCLONE_BACKUP_LOG_FILE"
done

export RCLONE_BACKUP_MAX_LOG_BYTES=100
export RCLONE_BACKUP_MAX_STAGE_LINES=10
unset FAKE_RCLONE_FAIL

"$TEST_ROOT/rclone_backup.sh"

sync_calls=$(grep -c '^sync ' "$RCLONE_CALL_LOG")
list_calls=$(grep -c '^lsf ' "$RCLONE_CALL_LOG")
if [[ "$sync_calls" -ne 3 || "$list_calls" -ne 1 ]]; then
    echo "FAIL: expected three sync calls and one archive listing" >&2
    exit 1
fi

if grep -qx 'output-line-1' "$RCLONE_BACKUP_LOG_FILE"; then
    echo "FAIL: early rclone output was not bounded" >&2
    exit 1
fi

grep -qx 'output-line-25' "$RCLONE_BACKUP_LOG_FILE"
grep -q 'rclone sync exit status: 0' "$RCLONE_BACKUP_LOG_FILE"

if grep -qx 'old-history-1' "$RCLONE_BACKUP_LOG_FILE"; then
    echo "FAIL: oversized persistent history was not trimmed" >&2
    exit 1
fi

echo "PASS: successful backup output is bounded"

calls_before_failure=$(wc -l < "$RCLONE_CALL_LOG")
export RCLONE_BACKUP_LOG_FILE="$TEST_ROOT/rclone-failure.log"
export FAKE_RCLONE_FAIL=1

set +e
"$TEST_ROOT/rclone_backup.sh"
failure_status=$?
set -e

if [[ "$failure_status" -ne 7 ]]; then
    echo "FAIL: expected failed rclone status 7, got $failure_status" >&2
    exit 1
fi

calls_after_failure=$(wc -l < "$RCLONE_CALL_LOG")
if [[ $((calls_after_failure - calls_before_failure)) -ne 1 ]]; then
    echo "FAIL: backup continued after the first failed sync" >&2
    exit 1
fi

if grep -qx 'error-line-1' "$RCLONE_BACKUP_LOG_FILE"; then
    echo "FAIL: early failed-rclone output was not bounded" >&2
    exit 1
fi

grep -qx 'error-line-25' "$RCLONE_BACKUP_LOG_FILE"
grep -q 'rclone sync exit status: 7' "$RCLONE_BACKUP_LOG_FILE"

echo "PASS: failed backup output is bounded and its status propagates"
