#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
COMPOSE_FILE="$REPO_ROOT/kopia/docker-compose.yml"
IGNORE_FILE="$REPO_ROOT/.kopiaignore"

required_mounts=(
    '/data/Obsidian/Main:/source/obsidian:ro'
    '/mnt/data_14tb/Images/immich:/source/immich_originals:ro'
    '/mnt/data_14tb/paperless/media:/source/paperless_media:ro'
    '/mnt/misc_5tb/exports/paperless:/source/paperless_exports:ro'
)

for mount in "${required_mounts[@]}"; do
    if ! grep -Fq -- "$mount" "$COMPOSE_FILE"; then
        echo "FAIL: Kopia Compose is missing protected source $mount" >&2
        exit 1
    fi
done

if [[ ! -f "$IGNORE_FILE" ]]; then
    echo "FAIL: no .kopiaignore exists for inconsistent live database files" >&2
    exit 1
fi

required_ignores=(
    'immich/database/postgres'
    'immich/database/postgres_pg14_backup'
    'wiki/postgres-data'
    'obsidian-livesync/couchdb-data'
    'spotify-stats/your_spotify_db.corrupt-*'
    'spotify-stats/your_spotify_db.mongo8-crash-*'
    'pingvin-share/redis-data'
)

for pattern in "${required_ignores[@]}"; do
    if ! grep -Fxq -- "$pattern" "$IGNORE_FILE"; then
        echo "FAIL: .kopiaignore is missing $pattern" >&2
        exit 1
    fi
done

echo "PASS: Kopia source coverage and live-database exclusions are explicit"
