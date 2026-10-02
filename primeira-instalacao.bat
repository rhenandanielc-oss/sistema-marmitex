@echo off
cd /d "%~dp0"
title Marmitex B2B
if exist ".env" goto envOk
echo [ERRO] Arquivo .env nao encontrado.
echo Copie o .env.example para .env e preencha as senhas (INSTALL.md, secao 4).
pause
exit /b 1
:envOk
rem Primeira instalacao: monta o sistema, cria o administrador e abre o navegador.
docker info >nul 2>&1
if not errorlevel 1 goto dockerOk
echo Abrindo o Docker Desktop...
start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
set /a tentativas=0
:esperaDocker
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto dockerOk
set /a tentativas+=1
if %tentativas% lss 36 goto esperaDocker
echo [ERRO] O Docker Desktop nao iniciou. Abra o Docker Desktop manualmente e tente de novo.
pause
exit /b 1
:dockerOk
echo Montando o sistema (primeira vez: pode levar varios minutos)...
docker compose up -d --build
if errorlevel 1 goto falhou
echo Aguardando o sistema ficar pronto (na primeira vez pode levar alguns minutos)...
set /a tentativas=0
:esperaApi
curl.exe -s -f -o nul http://localhost:8080/api/v1/health/ready
if not errorlevel 1 goto pronto
set /a tentativas+=1
if %tentativas% geq 100 goto demorou
timeout /t 3 /nobreak >nul
goto esperaApi
:demorou
echo [AVISO] O sistema esta demorando para responder.
echo Veja o que aconteceu com:  docker compose logs --tail 50 backend
pause
exit /b 1
:pronto
echo Criando o administrador (dados INITIAL_ADMIN_* do arquivo .env)...
docker compose exec -T backend python -m app.cli create-admin
start "" http://localhost:8080
echo.
echo Instalacao concluida. Acesse http://localhost:8080
echo Nos proximos dias, use o atalho "iniciar-marmitex".
pause
exit /b 0
:falhou
echo [ERRO] Nao foi possivel montar o sistema. Confira o arquivo .env e veja OPERACAO.md, secao 6.
pause
exit /b 1
