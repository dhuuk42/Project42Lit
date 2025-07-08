#!/bin/bash

# === CONFIG ===
CONTAINER_NAME=project42lit-db-1
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.env"
BACKUP_FILE=$1  # Pass filename as argument
ARCHIVE_SCHEMA=true  # true = rename schema instead of DROP

# === VALIDATION ===
if [ -z "$BACKUP_FILE" ]; then
  echo "❌ Usage: ./db_recovery.sh <backup_file.sql>"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Backup file not found: $BACKUP_FILE"
  exit 1
fi

# === STEP 1: Handle existing schema ===
if $ARCHIVE_SCHEMA; then
  ARCHIVE_NAME="schema_archive_$(date +%Y%m%d_%H%M%S)"
  echo "📦 Renaming schema 'public' to '$ARCHIVE_NAME'..."
  docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" <<EOF
ALTER SCHEMA public RENAME TO $ARCHIVE_NAME;
CREATE SCHEMA public;
EOF
else
  echo "🔥 Dropping existing schema 'public'..."
  docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" <<EOF
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
EOF
fi

# === STEP 2: Restore from SQL ===
echo "⏳ Restoring database '$DB_NAME' from $BACKUP_FILE ..."
cat "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"

if [ $? -eq 0 ]; then
  echo "✅ Recovery complete."
else
  echo "❌ Recovery failed."
fi
