#!/bin/bash
# Back up the SQLite database and uploaded attachments to Google Drive.
# Run this on the Oracle Cloud VM, manually or via cron.
#
# One-time setup (see README "Backups" section): install rclone and run
# `rclone config` to create a remote named "gdrive".
#
# RCLONE_REMOTE and REMOTE_RETENTION_DAYS come from the environment, then
# .env, then the defaults below.
set -euo pipefail
cd "$(dirname "$0")"

# Separates runs in the appended cron log.
echo

# Read one key from .env without sourcing it, so secrets in there are never
# evaluated by the shell.
env_value() {
    [[ -f .env ]] || return 0
    sed -n "s/^$1=//p" .env | tail -1 | sed -E "s/^([\"'])(.*)\1\$/\2/"
}

RCLONE_REMOTE="${RCLONE_REMOTE:-$(env_value RCLONE_REMOTE)}"
RCLONE_REMOTE="${RCLONE_REMOTE:-gdrive:carstats-backups}"
REMOTE_RETENTION_DAYS="${REMOTE_RETENTION_DAYS:-$(env_value REMOTE_RETENTION_DAYS)}"
REMOTE_RETENTION_DAYS="${REMOTE_RETENTION_DAYS:-30}"

timestamp="$(date +%Y%m%d-%H%M%S)"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"; docker compose exec -T app rm -f /app/data/backup.db' EXIT

# Online copy of the SQLite file via sqlite3's backup API, so a concurrent
# write from the running app can't produce a half-copied, corrupt file.
# Prints a content hash: an SQL dump of the copy (deterministic, unlike its raw
# pages) plus every attachment's path and bytes.
digest="$(docker compose exec -T app python -c "
import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path

h = hashlib.sha256()
# closing(), not 'with sqlite3.connect(...)' — the connection's own context
# manager only commits/rolls back on exit, it doesn't close the connection.
with closing(sqlite3.connect('/app/data/carstats.db')) as src, \
     closing(sqlite3.connect('/app/data/backup.db')) as dst:
    src.backup(dst)
    for line in dst.iterdump():
        h.update(line.encode() + b'\n')

uploads = Path('/app/data/uploads')
for path in sorted(p for p in uploads.rglob('*') if p.is_file()):
    h.update(str(path.relative_to(uploads)).encode() + b'\0')
    h.update(hashlib.sha256(path.read_bytes()).digest())
print(h.hexdigest()[:12])
")"

# A missing remote folder (first run) lists as empty instead of aborting.
latest="$({ rclone lsf "$RCLONE_REMOTE" --include '*.tar.gz' || true; } | sort | tail -1)"
if [[ "$latest" == *"-$digest.tar.gz" ]]; then
    # No upload, so no pruning either: the newest backup must survive however
    # long the data stays unchanged.
    echo "Unchanged since $latest, skipping upload"
    exit 0
fi

docker compose cp app:/app/data/backup.db "$workdir/carstats.db"
docker compose cp app:/app/data/uploads "$workdir/uploads" 2>/dev/null || mkdir -p "$workdir/uploads"

archive="$workdir/carstats-backup-$timestamp-$digest.tar.gz"
tar czf "$archive" -C "$workdir" carstats.db uploads

if ! rclone copy "$archive" "$RCLONE_REMOTE/"; then
    echo "Upload failed, keeping existing backups" >&2
    exit 1
fi
rclone delete --min-age "${REMOTE_RETENTION_DAYS}d" "$RCLONE_REMOTE/"

echo "Backup uploaded: $(basename "$archive")"
