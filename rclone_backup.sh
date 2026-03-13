#!/bin/bash

# Configuration
RCLONE_REMOTE="GDrive"
BACKUP_ROOT="Backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
ARCHIVE_DIR="${BACKUP_ROOT}/Archive/${TIMESTAMP}"
LOG_FILE="/home/ethan/docker/rclone_backup.log"
RETENTION_COUNT=30

# Ensure log file exists
touch "$LOG_FILE"

# Function to perform backup
perform_backup() {
    SRC="$1"
    DEST_NAME="$2"
    shift 2
    EXTRA_ARGS="$@"

    echo "[$(date)] Backing up $SRC to ${BACKUP_ROOT}/Current/${DEST_NAME}..." >> "$LOG_FILE"
    
    rclone sync "$SRC" "${RCLONE_REMOTE}:${BACKUP_ROOT}/Current/${DEST_NAME}" \
        --backup-dir "${RCLONE_REMOTE}:${ARCHIVE_DIR}/${DEST_NAME}" \
        --drive-use-trash=false \
        --fast-list \
        --progress \
        $EXTRA_ARGS >> "$LOG_FILE" 2>&1
}

# Function to perform clone (no retention)
perform_clone() {
    SRC="$1"
    DEST_NAME="$2"
    shift 2
    EXTRA_ARGS="$@"

    echo "[$(date)] Cloning $SRC to ${BACKUP_ROOT}/Current/${DEST_NAME}..." >> "$LOG_FILE"
    
    rclone sync "$SRC" "${RCLONE_REMOTE}:${BACKUP_ROOT}/Current/${DEST_NAME}" \
        --drive-use-trash=false \
        --fast-list \
        --progress \
        $EXTRA_ARGS >> "$LOG_FILE" 2>&1
}

echo "----------------------------------------------------------------" >> "$LOG_FILE"
echo "[$(date)] Starting Backup Routine" >> "$LOG_FILE"

# 1. Backup Docker Configs
perform_backup "/home/ethan/docker" "docker"

# 2. Backup Home Directory (excluding docker, cache, downloads, trash)
perform_backup "/home/ethan" "home" \
    --exclude "/docker/**" \
    --exclude "/.cache/**" \
    --exclude "/Downloads/**" \
    --exclude "/.local/share/Trash/**" \
    --exclude "/.thumbnails/**"

# 3. Clone Paperless (No Retention)
perform_clone "/mnt/data_14tb/paperless" "paperless"

# 4. Prune Old Archives
echo "[$(date)] Checking for old archives to prune (Keeping last $RETENTION_COUNT)..." >> "$LOG_FILE"

# List directories in Archive, sorted (oldest first)
ARCHIVES=$(rclone lsf "${RCLONE_REMOTE}:${BACKUP_ROOT}/Archive" --dirs-only | sort)
COUNT=$(echo "$ARCHIVES" | wc -l)

if [ "$COUNT" -gt "$RETENTION_COUNT" ]; then
    TO_DELETE=$((COUNT - RETENTION_COUNT))
    echo "[$(date)] Found $COUNT archives. Deleting $TO_DELETE oldest..." >> "$LOG_FILE"
    
    echo "$ARCHIVES" | head -n "$TO_DELETE" | while read -r DIR; do
        echo "Deleting old archive: $DIR" >> "$LOG_FILE"
        rclone purge "${RCLONE_REMOTE}:${BACKUP_ROOT}/Archive/$DIR" >> "$LOG_FILE" 2>&1
    done
else
    echo "[$(date)] Only $COUNT archives found. No pruning needed." >> "$LOG_FILE"
fi

echo "[$(date)] Backup Routine Complete." >> "$LOG_FILE"
echo "----------------------------------------------------------------" >> "$LOG_FILE"
