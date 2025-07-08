#!/bin/bash

# === SETUP ===
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
TIMESTAMP=$(date +%F_%H:%M:%S)
FILENAME="backup_${TIMESTAMP}.sql"
CONTAINER_NAME=project42lit-db-1
source "$SCRIPT_DIR/.env"

# === ENSURE BACKUP DIR ===
mkdir -p "$BACKUP_DIR"

# === BACKUP ===
echo "⏳ Dumping database '$DB_NAME'..."
docker exec -t "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_DIR/$FILENAME"

if [ $? -eq 0 ]; then
  echo "✅ Backup saved to $BACKUP_DIR/$FILENAME"
else
  echo "❌ Backup failed."
  exit 1
fi

