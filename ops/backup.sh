#!/bin/sh
# Backup do banco (pg_dump formato custom) com retenção.
# Usado pelo serviço "backup" do docker-compose (diário) e manualmente:
#   docker compose exec backup /ops/backup.sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
FILE="$BACKUP_DIR/marmitex_$STAMP.dump"

mkdir -p "$BACKUP_DIR"
export PGPASSWORD="$POSTGRES_PASSWORD"
pg_dump -h "${PGHOST:-db}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f "$FILE.tmp"
mv "$FILE.tmp" "$FILE"
# Confere se o arquivo é um dump válido (lista o conteúdo).
pg_restore --list "$FILE" > /dev/null
echo "$(date '+%Y-%m-%d %H:%M:%S') backup ok: $FILE ($(du -h "$FILE" | cut -f1))"

find "$BACKUP_DIR" -name 'marmitex_*.dump' -type f -mtime +"$RETENTION_DAYS" -print -delete
