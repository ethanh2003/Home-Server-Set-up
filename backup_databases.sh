#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

BACKUP_DIR="${BACKUP_DIR:-/home/ethan/docker/.db_dumps}"
BACKUP_LOCK_FILE="${BACKUP_LOCK_FILE:-/run/user/$(id -u)/homelab-database-backup.lock}"
BACKUP_TIMEOUT="${BACKUP_TIMEOUT:-2h}"
BACKUP_METRICS_FILE="${BACKUP_METRICS_FILE:-/home/ethan/docker/monitoring-stack/node_exporter_textfile/backup.prom}"
DOCKER_BIN="${DOCKER_BIN:-docker}"
PAPERLESS_EXPORT_ENABLED="${PAPERLESS_EXPORT_ENABLED:-1}"
PAPERLESS_EXPORT_DIR="${PAPERLESS_EXPORT_DIR:-/mnt/misc_5tb/exports/paperless}"
backup_started_at=$(date +%s)

mkdir -p "$BACKUP_DIR" "$(dirname "$BACKUP_LOCK_FILE")"
chmod 700 "$BACKUP_DIR"

exec 9>"$BACKUP_LOCK_FILE"
if ! flock -n 9; then
    echo "A database backup is already running; exiting." >&2
    exit 75
fi

temporary_files=()
remote_files=()

cleanup() {
    local path container remote

    for path in "${temporary_files[@]:-}"; do
        [[ -n "$path" ]] && rm -f -- "$path"
    done

    for path in "${remote_files[@]:-}"; do
        container="${path%%:*}"
        remote="${path#*:}"
        timeout --foreground "$BACKUP_TIMEOUT" "$DOCKER_BIN" exec "$container" rm -f -- "$remote" \
            >/dev/null 2>&1 || true
    done
}

write_backup_metrics() {
    local status=$1
    [[ -n "$BACKUP_METRICS_FILE" ]] || return 0

    local now duration last_success temporary
    now=$(date +%s)
    duration=$((now - backup_started_at))
    last_success=0
    if [[ -f "$BACKUP_METRICS_FILE" ]]; then
        last_success=$(
            awk '$1 == "homelab_backup_last_success_timestamp_seconds" {print $2}' \
                "$BACKUP_METRICS_FILE" |
                tail -n 1
        )
        [[ "$last_success" =~ ^[0-9]+$ ]] || last_success=0
    fi
    if [[ "$status" == "0" ]]; then
        last_success=$now
    fi

    mkdir -p "$(dirname "$BACKUP_METRICS_FILE")"
    temporary=$(mktemp "$(dirname "$BACKUP_METRICS_FILE")/.backup.prom.tmp.XXXXXX")
    {
        echo '# HELP homelab_backup_last_run_success Whether the last application export job succeeded.'
        echo '# TYPE homelab_backup_last_run_success gauge'
        printf 'homelab_backup_last_run_success %s\n' "$((status == 0 ? 1 : 0))"
        echo '# HELP homelab_backup_last_run_timestamp_seconds Unix timestamp of the last export attempt.'
        echo '# TYPE homelab_backup_last_run_timestamp_seconds gauge'
        printf 'homelab_backup_last_run_timestamp_seconds %s\n' "$now"
        echo '# HELP homelab_backup_last_success_timestamp_seconds Unix timestamp of the last successful export.'
        echo '# TYPE homelab_backup_last_success_timestamp_seconds gauge'
        printf 'homelab_backup_last_success_timestamp_seconds %s\n' "$last_success"
        echo '# HELP homelab_backup_last_run_duration_seconds Duration of the last export attempt.'
        echo '# TYPE homelab_backup_last_run_duration_seconds gauge'
        printf 'homelab_backup_last_run_duration_seconds %s\n' "$duration"
    } >"$temporary"
    chmod 644 "$temporary"
    mv -f -- "$temporary" "$BACKUP_METRICS_FILE"
}

finish() {
    local status=$?
    cleanup
    write_backup_metrics "$status" || true
    exit "$status"
}
trap finish EXIT

run_docker() {
    timeout --foreground "$BACKUP_TIMEOUT" "$DOCKER_BIN" "$@"
}

atomic_stdout_export() {
    local destination_name=$1
    local container=$2
    shift 2

    local destination="$BACKUP_DIR/$destination_name"
    local temporary
    temporary=$(mktemp "$BACKUP_DIR/.${destination_name}.tmp.XXXXXX")
    temporary_files+=("$temporary")

    echo "Exporting $destination_name from $container..."
    if run_docker exec "$container" "$@" >"$temporary"; then
        if [[ ! -s "$temporary" ]]; then
            echo "Export for $destination_name was empty; preserving the previous backup." >&2
            return 65
        fi
        chmod 600 "$temporary"
        mv -f -- "$temporary" "$destination"
        temporary_files=("${temporary_files[@]/$temporary}")
    else
        local status=$?
        echo "Export for $destination_name failed; preserving the previous backup." >&2
        return "$status"
    fi
}

atomic_sqlite_export() {
    local destination_name=$1
    local container=$2
    local source_path=$3
    local runtime=$4

    local destination="$BACKUP_DIR/$destination_name"
    local temporary remote
    temporary=$(mktemp "$BACKUP_DIR/.${destination_name}.tmp.XXXXXX")
    remote="/tmp/homelab-backup-${destination_name}.$$"
    temporary_files+=("$temporary")
    remote_files+=("$container:$remote")

    echo "Exporting $destination_name from $container..."
    run_docker exec "$container" rm -f -- "$remote"

    case "$runtime" in
        python)
            run_docker exec "$container" python3 -c \
                'import sqlite3, sys
source = sqlite3.connect("file:" + sys.argv[1] + "?mode=ro", uri=True)
target = sqlite3.connect(sys.argv[2])
with target:
    source.backup(target)
result = target.execute("PRAGMA integrity_check").fetchone()[0]
source.close()
target.close()
if result != "ok":
    raise SystemExit("SQLite integrity check failed: " + result)' \
                "$source_path" "$remote"
            ;;
        php-pdo)
            run_docker exec "$container" php -r \
                '$source = new PDO("sqlite:" . $argv[1], null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$source->exec("VACUUM INTO " . $source->quote($argv[2]));
$target = new PDO("sqlite:" . $argv[2], null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$result = $target->query("PRAGMA integrity_check")->fetchColumn();
$source = null;
$target = null;
if ($result !== "ok") {
    fwrite(STDERR, "SQLite integrity check failed\n");
    exit(1);
}' \
                "$source_path" "$remote"
            ;;
        *)
            echo "Unsupported SQLite runtime: $runtime" >&2
            return 64
            ;;
    esac

    if run_docker cp "$container:$remote" "$temporary"; then
        if [[ ! -s "$temporary" ]]; then
            echo "Export for $destination_name was empty; preserving the previous backup." >&2
            return 65
        fi
        chmod 600 "$temporary"
        mv -f -- "$temporary" "$destination"
        temporary_files=("${temporary_files[@]/$temporary}")
    else
        local status=$?
        echo "Export for $destination_name failed; preserving the previous backup." >&2
        return "$status"
    fi

    run_docker exec "$container" rm -f -- "$remote"
    remote_files=("${remote_files[@]/$container:$remote}")
}

echo "Starting application-consistent database exports..."

atomic_stdout_export immich.sql immich_postgres sh -euc \
    'exec pg_dump --clean --if-exists --no-owner --no-privileges --username="$POSTGRES_USER" "$POSTGRES_DB"'

atomic_stdout_export dawarich.sql dawarich_db sh -euc \
    'exec pg_dump --clean --if-exists --no-owner --no-privileges --username="$POSTGRES_USER" "$POSTGRES_DB"'

atomic_stdout_export wiki.sql wiki-db sh -euc \
    'exec pg_dump --clean --if-exists --no-owner --no-privileges --username="$POSTGRES_USER" "$POSTGRES_DB"'

atomic_stdout_export spotify-mongo.archive.gz mongo mongodump --archive --gzip

atomic_stdout_export obsidian-livesync-couchdb.tar.gz obsidian-livesync-couchdb sh -euc '
work_directory=$(mktemp -d)
trap '\''rm -rf -- "$work_directory"'\'' EXIT
auth="${COUCHDB_USER}:${COUCHDB_PASSWORD}"

curl --fail --silent --show-error --user "$auth" http://127.0.0.1:5984/_all_dbs |
    tr -d '\''[]"'\'' |
    tr '\'','\'' '\''\n'\'' |
    while IFS= read -r database; do
        [ -n "$database" ] || continue
        if ! printf '\''%s\n'\'' "$database" | grep -Eq '\''^[_a-z][a-z0-9_$()+-]*$'\''; then
            printf '\''Refusing unexpected CouchDB database name\n'\'' >&2
            exit 64
        fi
        curl --fail --silent --show-error --user "$auth" \
            "http://127.0.0.1:5984/${database}/_all_docs?include_docs=true&attachments=true&conflicts=true" \
            >"$work_directory/${database}.json"
        [ -s "$work_directory/${database}.json" ]
    done

tar -C "$work_directory" -czf - .
'

atomic_sqlite_export home-assistant.db HomeAssistant /config/home-assistant_v2.db python
atomic_sqlite_export home-assistant-2.db HomeAssistant2 /config/home-assistant_v2.db python

# Home Assistant and Mosquitto deliberately protect portions of their live
# state with owner-only modes. Export those files through their containers so
# the unprivileged Kopia service can version stable, mode-600 copies.
atomic_stdout_export home-assistant-storage.tar.gz HomeAssistant \
    tar -C /config -czf - .storage
atomic_stdout_export mosquitto-persistence.db mosquitto \
    sh -euc 'exec cat /mosquitto/data/mosquitto.db'

atomic_sqlite_export linkstack.db linkstack-linkstack-1 /htdocs/database/database.sqlite php-pdo

if [[ "$PAPERLESS_EXPORT_ENABLED" == "1" ]]; then
    echo "Refreshing the Paperless portable export..."
    run_docker exec paperless document_exporter /usr/src/paperless/export \
        --delete \
        --compare-checksums \
        --compare-json \
        --no-progress-bar
    find "$PAPERLESS_EXPORT_DIR" -xdev -type d -exec chmod 700 {} +
    find "$PAPERLESS_EXPORT_DIR" -xdev -type f -exec chmod 600 {} +
fi

# Kopia versions these atomic files, so only stale temporary or retired output
# belongs in the local cleanup step.
find "$BACKUP_DIR" -maxdepth 1 -type f -name '.*.tmp.*' -mtime +1 -delete
rm -f -- "$BACKUP_DIR/planka.sql"

echo "Database exports completed successfully."
