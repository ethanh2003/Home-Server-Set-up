#!/bin/bash

# Directory mapped to Kopia
BACKUP_DIR="/home/ethan/docker/.db_dumps"
mkdir -p "$BACKUP_DIR"

echo "Starting database backups..."

# 1. Planka Backup
echo "Backing up Planka..."
docker exec planka-postgres-1 pg_dump -U postgres planka > "$BACKUP_DIR/planka.sql"

# 2. Immich Backup
echo "Backing up Immich..."
docker exec -e PGPASSWORD=postgres immich_postgres pg_dump -U postgres immich > "$BACKUP_DIR/immich.sql"

# 3. Prune old dumps (Keep last 3 days locally to save space)
echo "Pruning old backups..."
find "$BACKUP_DIR" -type f -mtime +3 -delete

echo "Backup complete."