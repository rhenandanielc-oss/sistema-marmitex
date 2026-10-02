@echo off
cd /d "%~dp0"
title Marmitex B2B - Backup
echo Fazendo backup agora...
docker compose exec -T backup /ops/backup.sh
if errorlevel 1 goto falhou
echo.
echo Backup concluido. Abrindo a pasta de backups (copie para um pendrive ou para a nuvem).
start "" "%~dp0backups"
pause
exit /b 0
:falhou
echo [ERRO] O backup falhou. O sistema esta ligado? Rode o "iniciar-marmitex" e tente de novo.
pause
exit /b 1
