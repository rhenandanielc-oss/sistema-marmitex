#!/bin/sh
# Agenda simples: um backup ao iniciar e depois todo dia no horário BACKUP_HOUR (padrão 23h).
set -u
BACKUP_HOUR="${BACKUP_HOUR:-23}"
until pg_isready -h "${PGHOST:-db}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q; do sleep 5; done
/ops/backup.sh || echo "falha no backup inicial"
while true; do
  now=$(date +%s)
  next=$(date -d "$(date +%Y-%m-%d) ${BACKUP_HOUR}:00:00" +%s 2>/dev/null || echo $((now + 86400)))
  [ "$next" -le "$now" ] && next=$((next + 86400))
  sleep $((next - now))
  /ops/backup.sh || echo "falha no backup agendado"
done
