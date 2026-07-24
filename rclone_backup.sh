#!/bin/bash

set -o pipefail

# Configuration
RCLONE_REMOTE="GDrive"
BACKUP_ROOT="Backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
ARCHIVE_DIR="${BACKUP_ROOT}/Archive/${TIMESTAMP}"
LOG_FILE="${RCLONE_BACKUP_LOG_FILE:-/home/ethan/docker/rclone_backup.log}"
LOCK_FILE="${RCLONE_BACKUP_LOCK_FILE:-/run/user/$(id -u)/rclone_backup.lock}"
MAX_LOG_BYTES="${RCLONE_BACKUP_MAX_LOG_BYTES:-10485760}"
MAX_STAGE_LOG_LINES="${RCLONE_BACKUP_MAX_STAGE_LINES:-2000}"
RETENTION_COUNT=30

# Ensure runtime files exist.
mkdir -p "$(dirname "$LOG_FILE")" "$(dirname "$LOCK_FILE")"
touch "$LOG_FILE"

# Only one scheduled or manual backup may mutate the remote destinations.
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "[$(date)] Backup already running; skipping this invocation." >> "$LOG_FILE"
    exit 0
fi

for numeric_setting in "$MAX_LOG_BYTES" "$MAX_STAGE_LOG_LINES"; do
    if [[ ! "$numeric_setting" =~ ^[1-9][0-9]*$ ]]; then
        echo "[$(date)] Invalid positive-integer logging limit: $numeric_setting" >> "$LOG_FILE"
        exit 2
    fi
done

trim_persistent_log() {
    local log_size
    local trimmed_log

    log_size=$(stat -c %s "$LOG_FILE")
    if ((log_size <= MAX_LOG_BYTES)); then
        return 0
    fi

    trimmed_log="${LOG_FILE}.trim.$$"
    if ! tail -c "$MAX_LOG_BYTES" "$LOG_FILE" > "$trimmed_log"; then
        rm -f "$trimmed_log"
        echo "[$(date)] Failed to trim oversized backup log." >> "$LOG_FILE"
        return 1
    fi

    chmod --reference="$LOG_FILE" "$trimmed_log"
    mv -f "$trimmed_log" "$LOG_FILE"
}

run_rclone() {
    local operation="$1"
    local rclone_status
    shift

    rclone "$operation" "$@" 2>&1 | awk -v max="$MAX_STAGE_LOG_LINES" '
        { lines[NR % max] = $0 }
        END {
            if (NR > max) {
                printf "[... %d earlier lines omitted ...]\n", NR - max
            }
            start = NR > max ? NR - max + 1 : 1
            for (line = start; line <= NR; line++) {
                print lines[line % max]
            }
        }
    ' >> "$LOG_FILE"
    rclone_status=${PIPESTATUS[0]}

    echo "[$(date)] rclone $operation exit status: $rclone_status" >> "$LOG_FILE"
    return "$rclone_status"
}

# Function to perform backup
perform_backup() {
    local src="$1"
    local dest_name="$2"
    local extra_args
    shift 2
    extra_args=("$@")

    echo "[$(date)] Backing up $src to ${BACKUP_ROOT}/Current/${dest_name}..." >> "$LOG_FILE"

    run_rclone sync "$src" "${RCLONE_REMOTE}:${BACKUP_ROOT}/Current/${dest_name}" \
        --backup-dir "${RCLONE_REMOTE}:${ARCHIVE_DIR}/${dest_name}" \
        --drive-use-trash=false \
        --fast-list \
        "${extra_args[@]}"
}

# Function to perform clone (no retention)
perform_clone() {
    local src="$1"
    local dest_name="$2"
    local extra_args
    shift 2
    extra_args=("$@")

    echo "[$(date)] Cloning $src to ${BACKUP_ROOT}/Current/${dest_name}..." >> "$LOG_FILE"

    run_rclone sync "$src" "${RCLONE_REMOTE}:${BACKUP_ROOT}/Current/${dest_name}" \
        --drive-use-trash=false \
        --fast-list \
        "${extra_args[@]}"
}

if ! trim_persistent_log; then
    exit 1
fi

echo "----------------------------------------------------------------" >> "$LOG_FILE"
echo "[$(date)] Starting Backup Routine" >> "$LOG_FILE"

# 1. Backup Docker Configs
perform_backup "/home/ethan/docker" "docker" || exit $?

# 2. Backup Home Directory (excluding docker, cache, downloads, trash)
perform_backup "/home/ethan" "home" \
    --exclude "/docker/**" \
    --exclude "/.cache/**" \
    --exclude "/Downloads/**" \
    --exclude "/.local/share/Trash/**" \
    --exclude "/.thumbnails/**" || exit $?

# 3. Clone Paperless (No Retention)
perform_clone "/mnt/data_14tb/paperless" "paperless" || exit $?

# 4. Prune Old Archives
echo "[$(date)] Checking for old archives to prune (Keeping last $RETENTION_COUNT)..." >> "$LOG_FILE"

# List directories in Archive, sorted (oldest first)
ARCHIVES=$(rclone lsf "${RCLONE_REMOTE}:${BACKUP_ROOT}/Archive" --dirs-only 2>> "$LOG_FILE")
LIST_STATUS=$?
echo "[$(date)] rclone lsf exit status: $LIST_STATUS" >> "$LOG_FILE"
if ((LIST_STATUS != 0)); then
    exit "$LIST_STATUS"
fi

ARCHIVES=$(printf '%s\n' "$ARCHIVES" | sort)
if [[ -z "$ARCHIVES" ]]; then
    COUNT=0
else
    COUNT=$(printf '%s\n' "$ARCHIVES" | wc -l)
fi

if [ "$COUNT" -gt "$RETENTION_COUNT" ]; then
    TO_DELETE=$((COUNT - RETENTION_COUNT))
    echo "[$(date)] Found $COUNT archives. Deleting $TO_DELETE oldest..." >> "$LOG_FILE"

    while read -r DIR; do
        echo "Deleting old archive: $DIR" >> "$LOG_FILE"
        run_rclone purge "${RCLONE_REMOTE}:${BACKUP_ROOT}/Archive/$DIR" || exit $?
    done < <(printf '%s\n' "$ARCHIVES" | head -n "$TO_DELETE")
else
    echo "[$(date)] Only $COUNT archives found. No pruning needed." >> "$LOG_FILE"
fi

echo "[$(date)] Backup Routine Complete." >> "$LOG_FILE"
echo "----------------------------------------------------------------" >> "$LOG_FILE"
