@echo off
cd /d "%~dp0"
title Marmitex B2B
echo Parando o sistema Marmitex B2B (os dados ficam salvos)...
docker compose stop
echo Sistema parado.
timeout /t 5 >nul
