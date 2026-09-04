#!/bin/bash
# Back up the SQLite database and uploaded attachments to Google Drive.
# Run this on the Oracle Cloud VM, manually or via cron.
#
# One-time setup (see README "Backups" section): install rclone and run
# `rclone config` to create a remote named "gdrive".
set -euo pipefail
cd "$(dirname "$0")"

RCLONE_REMOTE="${RCLONE_REMOTE:-gdrive:carstats-backups}"
REMOTE_RETENTION_DAYS="${REMOTE_RETENTION_DAYS:-30}"

timestamp="$(date +%Y%m%d-%H%M%S)"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"; docker compose exec -T app rm -f /app/data/backup.db' EXIT

# Online copy of the SQLite file via sqlite3's backup API, so a concurrent
# write from the running app can't produce a half-copied, corrupt file.
docker compose exec -T app python -c "
import sqlite3
src = sqlite3.connect('/app/data/carstats.db')
dst = sqlite3.connect('/app/data/backup.db')
src.backup(dst)
src.close()
dst.close()
"

docker compose cp app:/app/data/backup.db "$workdir/carstats.db"
docker compose cp app:/app/data/uploads "$workdir/uploads" 2>/dev/null || mkdir -p "$workdir/uploads"

archive="$workdir/carstats-backup-$timestamp.tar.gz"
tar czf "$archive" -C "$workdir" carstats.db uploads

rclone copy "$archive" "$RCLONE_REMOTE/"
rclone delete --min-age "${REMOTE_RETENTION_DAYS}d" "$RCLONE_REMOTE/"

echo "Backup uploaded: $(basename "$archive")"
