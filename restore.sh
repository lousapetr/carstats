#!/bin/bash
# Restore the SQLite database and uploaded attachments from a Google Drive
# backup made by backup.sh.
#
#   ./restore.sh                  # latest backup -> local dev DB (backend/data/)
#   ./restore.sh --list           # show what's on the remote
#   ./restore.sh --archive carstats-backup-20260922-141328.tar.gz
#   ./restore.sh --target prod    # latest backup -> the live container (run on the VM)
#
# Needs an rclone remote named "gdrive" (see README "Backups").
set -euo pipefail
cd "$(dirname "$0")"

RCLONE_REMOTE="${RCLONE_REMOTE:-gdrive:carstats-backups}"

target="dev"
archive=""
do_list=0
migrate=1
assume_yes=0

usage() {
    cat <<'EOF'
Usage: ./restore.sh [options]

  --target dev|prod   where to restore (default: dev)
  --prod              shorthand for --target prod
  --archive NAME      restore this archive instead of the newest one
  --list              list the archives on the remote and exit
  --no-migrate        skip `alembic upgrade head` (dev only; prod migrates on
                      container start)
  -y, --yes           don't ask for confirmation before overwriting prod
  -h, --help          this text
EOF
}

die() {
    echo "restore.sh: $1" >&2
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target) target="${2:-}"; [[ -n "$target" ]] || die "--target needs dev or prod"; shift 2 ;;
        --prod) target="prod"; shift ;;
        --archive) archive="${2:-}"; [[ -n "$archive" ]] || die "--archive needs a filename"; shift 2 ;;
        --list) do_list=1; shift ;;
        --no-migrate) migrate=0; shift ;;
        -y|--yes) assume_yes=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; die "unknown option: $1" ;;
    esac
done

[[ "$target" == "dev" || "$target" == "prod" ]] || die "--target must be dev or prod, got '$target'"
command -v rclone >/dev/null || die "rclone not found (see README \"Backups\")"

if (( do_list )); then
    rclone lsl "$RCLONE_REMOTE" | sort -k2
    exit 0
fi

# Checked up front so a prod restore fails before the download and the prompt.
if [[ "$target" == "prod" ]]; then
    command -v docker >/dev/null || die "docker not found — --target prod runs on the VM"
    container="$(docker compose ps -aq app 2>/dev/null)" \
        || die "can't reach the docker daemon (running? are you in the docker group?)"
    [[ -n "$container" ]] || die "no 'app' container in this compose project — --target prod runs on the VM"
fi

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

listing="$(rclone lsf "$RCLONE_REMOTE" --include '*.tar.gz' | sort)"
[[ -n "$listing" ]] || die "no backups found in $RCLONE_REMOTE"
if [[ -z "$archive" ]]; then
    # backup.sh names archives with a YYYYmmdd-HHMMSS stamp, so lexical order
    # is chronological order.
    archive="$(tail -1 <<<"$listing")"
elif ! grep -Fxq "$archive" <<<"$listing"; then
    die "$archive not found in $RCLONE_REMOTE (--list shows what's there)"
fi

echo "Restoring $archive -> $target"
rclone copy "$RCLONE_REMOTE/$archive" "$workdir/"
[[ -f "$workdir/$archive" ]] || die "$archive not found in $RCLONE_REMOTE"
tar xzf "$workdir/$archive" -C "$workdir"

[[ -f "$workdir/carstats.db" ]] || die "$archive contains no carstats.db"
[[ "$(head -c 15 "$workdir/carstats.db")" == "SQLite format 3" ]] \
    || die "$archive's carstats.db is not a SQLite file"
[[ -d "$workdir/uploads" ]] || mkdir "$workdir/uploads"

if [[ "$target" == "dev" ]]; then
    mkdir -p backend/data/uploads
    if [[ -f backend/data/carstats.db ]]; then
        kept="backend/data/carstats.db.replaced-$(date +%Y%m%d-%H%M%S)"
        mv backend/data/carstats.db "$kept"
        echo "Previous dev DB kept at $kept"
    fi
    cp "$workdir/carstats.db" backend/data/carstats.db
    # Journal files left by the old DB would be replayed into the new one.
    rm -f backend/data/carstats.db-wal backend/data/carstats.db-shm
    cp -r "$workdir/uploads/." backend/data/uploads/

    if (( migrate )); then
        (cd backend && uv run alembic upgrade head)
    fi
    echo "Dev DB restored. Restart the dev server to pick it up."
    exit 0
fi

if (( ! assume_yes )); then
    echo
    echo "This overwrites the LIVE production database and attachments with $archive."
    read -r -p "Type 'yes' to continue: " reply
    [[ "$reply" == "yes" ]] || die "aborted"
fi

# Snapshot the current live DB first so the restore itself is undoable. Same
# online-copy trick as backup.sh; skipped when there's nothing to snapshot
# (fresh VM, empty volume).
if [[ -n "$(docker compose ps -q app)" ]]; then
    safety="pre-restore-$(date +%Y%m%d-%H%M%S).db"
    if docker compose exec -T app test -f /app/data/carstats.db; then
        docker compose exec -T app python -c "
import sqlite3
from contextlib import closing

with closing(sqlite3.connect('/app/data/carstats.db')) as src, \
     closing(sqlite3.connect('/app/data/$safety')) as dst:
    src.backup(dst)
"
        echo "Current DB snapshotted to /app/data/$safety inside the volume"
    fi
fi

docker compose stop app
docker compose cp "$workdir/carstats.db" app:/app/data/carstats.db
docker compose cp "$workdir/uploads" app:/app/data/
# The stopped container can't exec, so clear stale journal files in a throwaway
# one that mounts the same volume.
docker compose run --rm --no-deps --entrypoint sh app \
    -c 'rm -f /app/data/carstats.db-wal /app/data/carstats.db-shm'
docker compose up -d app
docker compose ps app

echo "Prod restored from $archive (the entrypoint ran alembic upgrade head on start)."
