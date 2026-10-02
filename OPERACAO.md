# OPERACAO.md

# Operação, backup e deploy — Sistema Marmitex B2B

Comandos executados no notebook onde o sistema está instalado, no PowerShell/terminal, **dentro da pasta do sistema** (ex.: `C:\marmitex`). Instalação inicial: `INSTALL.md`.

No Windows, as tarefas mais comuns também têm **atalhos de dois cliques** na pasta do sistema: `iniciar-marmitex.bat`, `parar-marmitex.bat` e `backup-agora.bat`.

---

## 1. Ligar, desligar e conferir

| Ação | Comando |
|---|---|
| Ver situação | `docker compose ps` |
| Iniciar (se estiver parado) | `iniciar-marmitex.bat` ou `docker compose up -d` |
| Parar tudo | `parar-marmitex.bat` ou `docker compose stop` |
| Reiniciar | `docker compose restart` |
| Saúde da API | abrir http://localhost:8080/api/v1/health/ready → `{"status":"ok","database":"up"}` |

Com o Docker Desktop configurado para iniciar com o Windows e `restart: unless-stopped`, o sistema volta sozinho quando o notebook é ligado.

---

## 2. Backup

### Automático

O serviço `backup` faz:

* um backup **ao iniciar** o sistema;
* um backup **todo dia às 23h** (`BACKUP_HOUR` no `.env`);
* apaga backups com mais de **30 dias** (`BACKUP_RETENTION_DAYS`).

Os arquivos ficam em **`backups/`** na pasta do sistema, com nome `marmitex_AAAA-MM-DD_HHMMSS.dump`. Cada arquivo é conferido (`pg_restore --list`) logo após ser criado.

> Se o horário agendado não puder ser calculado (versão do `date` do contêiner), o serviço faz o backup a cada 24 horas a partir do início — conferir o log na primeira semana: `docker compose logs backup`.

### Manual (antes de atualizar ou quando quiser)

Dois cliques em **`backup-agora.bat`** (já abre a pasta `backups` para copiar), ou:

```powershell
docker compose exec backup /ops/backup.sh
```

### Cópia externa — **obrigatória**

O backup na mesma máquina não protege contra roubo, defeito ou perda do notebook. **Toda semana** copie a pasta `backups/` (ou pelo menos o arquivo mais recente) para:

* um pendrive/HD externo, **e/ou**
* uma pasta sincronizada na nuvem (Google Drive, OneDrive).

Sugestão: configurar a pasta `backups/` dentro de uma pasta sincronizada do OneDrive/Google Drive para a cópia ser automática.

---

## 3. Restaurar um backup

Substitui **todos** os dados atuais pelos do arquivo escolhido.

```powershell
# 1. Faça um backup do estado atual (por segurança)
docker compose exec backup /ops/backup.sh

# 2. Pare as telas e a API
docker compose stop backend frontend

# 3. Restaure (troque pelo nome do arquivo desejado, listado em backups\)
docker compose exec backup /ops/restore.sh /backups/marmitex_2026-10-02_230000.dump

# 4. Inicie novamente
docker compose start backend frontend
```

Confira no Dashboard e no Histórico se os valores estão como esperado.

### Restaurar em outro notebook (o principal quebrou)

1. Instale o sistema no novo notebook seguindo `INSTALL.md` até o passo 5 (`docker compose up -d --build`) — **não** crie o administrador.
2. Copie o arquivo `.dump` mais recente para a pasta `backups/` do novo notebook.
3. Execute os passos 2 a 4 acima. Os usuários e senhas voltam junto com o backup.

**Teste de restauração:** realizado na Fase 5 (backup do banco de demonstração → restauração em banco novo e por cima de dados alterados → contagens e totais idênticos: 258 vendas, R$ 98.746,50 em vendas, R$ 70.948,40 em custos, 427 registros de auditoria). Recomenda-se repetir o teste a cada 3 meses restaurando num notebook de testes.

---

## 4. Atualizar o sistema (nova versão)

```powershell
docker compose exec backup /ops/backup.sh      # 1. backup antes de tudo
git pull                                        # 2. baixa a nova versão (ou extraia o novo ZIP por cima, mantendo .env e backups\)
docker compose up -d --build                    # 3. reconstrói e reinicia
docker compose ps                               # 4. confere
```

As **migrations do banco são aplicadas automaticamente** quando o backend inicia (`alembic upgrade head`). Se algo der errado, restaure o backup do passo 1 (seção 3) e volte para a versão anterior (`git checkout <versão anterior>` + `docker compose up -d --build`).

---

## 5. Logs

| O que | Comando |
|---|---|
| Últimas linhas da API | `docker compose logs --tail 100 backend` |
| Acompanhar ao vivo | `docker compose logs -f backend` |
| Backups | `docker compose logs backup` |
| Banco | `docker compose logs db` |

* A API registra cada requisição em JSON (método, rota, status, duração, `request_id`). Senhas e tokens nunca são registrados.
* Os logs são rotacionados (5 arquivos de 10 MB por serviço) para não encher o disco.
* Mensagens de erro na tela trazem um código de requisição; o mesmo `request_id` aparece no log.

Ações dos usuários (logins, cadastros, vendas, custos, alterações e exclusões, com antes/depois) ficam na **auditoria**, consultável pela API em `/api/v1/audit-logs` (somente administradores).

---

## 6. Problemas comuns

| Sintoma | O que fazer |
|---|---|
| `docker compose up` falha com "JWT_SECRET de exemplo em produção" ou "Senha de exemplo no DATABASE_URL" | Preencha o `.env` conforme `INSTALL.md` seção 4. |
| Tela "Não foi possível conectar ao servidor" | `docker compose ps`; se algum serviço estiver parado, `docker compose up -d`. Veja `docker compose logs backend`. |
| Segundo notebook não abre | Por padrão só o próprio notebook acessa. Para liberar, siga `INSTALL.md` seção 7 (`ACESSO_IP=0.0.0.0`, firewall e rede **Privada**). |
| Atalho `.bat` fecha sem abrir o sistema | Rode-o pelo PowerShell (`.\iniciar-marmitex.bat`) para ver a mensagem; confira se o Docker Desktop está instalado e o `.env` existe. |
| Esqueci a senha | Outro administrador redefine em **Usuários → Redefinir senha**. Se não houver outro: `docker compose exec backend python -m app.cli create-admin` com um novo e-mail no `.env` (`INITIAL_ADMIN_EMAIL`). |
| "Muitas tentativas" no login | Aguarde 15 minutos (proteção contra tentativas repetidas). |
| Disco cheio | Apague backups antigos já copiados para fora; `docker system prune` remove imagens não usadas. |
| Data/hora errada nas vendas | O "hoje" segue `APP_TIMEZONE` (padrão `America/Sao_Paulo`); confira o relógio do notebook. |

---

## 7. Segurança — boas práticas

* Senhas de administrador com 8+ caracteres e diferentes para cada pessoa; não compartilhar login (a auditoria registra quem fez cada operação).
* Desativar (não apagar) usuários que saírem.
* Manter o Windows e o Docker Desktop atualizados.
* Por padrão (`ACESSO_IP=127.0.0.1`) o sistema só aceita conexões do próprio notebook. Se liberar um segundo notebook, a porta 8080 deve ficar aberta **apenas** na rede privada (nunca no roteador para a internet).
* O banco (5432) e a API (8000) sempre aceitam conexões só do próprio notebook.
