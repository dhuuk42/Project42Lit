#!/bin/bash

# === CONFIG ===
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/db_backup.sh"
BACKUP_DIR="$SCRIPT_DIR/backups"
source "$SCRIPT_DIR/.env"
# === 1. Run the backup script ===
echo "📦 Running backup script..."
$BACKUP_SCRIPT

if [ $? -ne 0 ]; then
  echo "❌ Backup script failed."
  exit 1
fi

# === 2. Find the latest backup file ===
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.sql | head -n 1)

if [ ! -f "$LATEST_BACKUP" ]; then
  echo "❌ No backup file found in $BACKUP_DIR"
  exit 1
fi

echo "🚀 Uploading latest backup: $LATEST_BACKUP to $REMOTE_HOST..."

# === 3. Upload via sshpass + scp ===
sshpass -p "$REMOTE_PASS" scp "$LATEST_BACKUP" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH"

if [ $? -eq 0 ]; then
  echo "✅ Upload complete."
else
  echo "❌ Upload failed."
fi

