#!/bin/sh
# Restaura um backup, substituindo TODOS os dados atuais.
# Uso (no notebook servidor, na pasta do projeto):
#   docker compose stop backend frontend
#   docker compose exec backup /ops/restore.sh /backups/marmitex_AAAA-MM-DD_HHMMSS.dump
#   docker compose start backend frontend
set -eu
FILE="${1:?Informe o arquivo de backup, ex.: /backups/marmitex_2026-10-02_230000.dump}"
[ -f "$FILE" ] || { echo "Arquivo não encontrado: $FILE"; exit 1; }
export PGPASSWORD="$POSTGRES_PASSWORD"
echo "Restaurando $FILE em $POSTGRES_DB (os dados atuais serão substituídos)..."
pg_restore -h "${PGHOST:-db}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner "$FILE"
echo "Restauração concluída."
