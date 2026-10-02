# INSTALL.md

# Instalação — Sistema Marmitex B2B

Instalação em **um único notebook**: tudo roda nele e o acesso é pelo navegador do próprio notebook. Não é preciso mexer em rede, roteador ou firewall. Tempo estimado: 30 a 45 minutos.

Se no futuro quiser usar também um segundo notebook, veja a seção 7 (opcional).

---

## 1. Como funciona

```
Notebook
┌──────────────────────────────────────────────┐
│ Navegador → http://localhost:8080            │
│                                              │
│ Docker Desktop                               │
│  ├─ frontend  (telas)                        │
│  ├─ backend   (cálculos)                     │
│  ├─ db        (banco de dados PostgreSQL)    │
│  └─ backup    (cópia diária do banco)        │
│                                              │
│ pasta backups\  ← arquivos de backup         │
└──────────────────────────────────────────────┘
```

* Os dados ficam no próprio notebook (não vão para a internet).
* Por padrão, **só este notebook** consegue abrir o sistema (`ACESSO_IP=127.0.0.1` no `.env`).

---

## 2. Requisitos

| Item | Mínimo |
|---|---|
| Sistema | Windows 10/11 (64 bits) — também funciona em macOS e Linux |
| Memória | 8 GB de RAM |
| Disco livre | 10 GB |
| Programas | **Docker Desktop** e, opcionalmente, **Git** |

### Instalar o Docker Desktop (Windows)

1. Baixe e instale: https://www.docker.com/products/docker-desktop/ — aceite usar o **WSL 2** quando perguntado e reinicie o notebook.
2. Abra o Docker Desktop uma vez e aceite os termos.
3. Em *Settings → General*, marque **"Start Docker Desktop when you sign in"** (o sistema volta sozinho quando o notebook liga).

---

## 3. Baixar o sistema

**Opção A — sem Git (mais simples):** no GitHub, botão **Code → Download ZIP**. Extraia em `C:\marmitex`.

**Opção B — com Git:** no PowerShell:

```powershell
cd C:\
git clone https://github.com/rhenandanielc-oss/sistema-marmitex.git marmitex
```

A pasta `C:\marmitex` deve conter, entre outros, `docker-compose.yml`, `.env.example` e os atalhos `primeira-instalacao.bat` e `iniciar-marmitex.bat`.

---

## 4. Configurar senhas (arquivo `.env`)

1. Na pasta `C:\marmitex`, copie o arquivo **`.env.example`** e renomeie a cópia para **`.env`**.
   (No Explorador de Arquivos, ative *Exibir → Extensões de nomes de arquivos* para ver o nome completo.)
2. Gere um segredo aleatório. Abra o **PowerShell** e rode (copie o resultado):

   ```powershell
   docker run --rm python:3.12-alpine python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

3. Abra o `.env` no **Bloco de Notas** e altere:

   | Linha | O que colocar |
   |---|---|
   | `POSTGRES_PASSWORD=` | uma senha forte para o banco (sem espaços) |
   | `DATABASE_URL=` | troque `troque-esta-senha` pela **mesma** senha acima |
   | `JWT_SECRET=` | o segredo gerado no passo 2 |
   | `INITIAL_ADMIN_NAME=` | seu nome |
   | `INITIAL_ADMIN_EMAIL=` | seu e-mail (será o login) |
   | `INITIAL_ADMIN_PASSWORD=` | sua senha de acesso (mínimo 8 caracteres) |

   Não altere `ENVIRONMENT=production` nem `ACESSO_IP=127.0.0.1`. Com valores de exemplo, o sistema **se recusa a iniciar** — é proposital.

> O `.env` contém senhas: não envie para ninguém. Ele não vai para o GitHub (é ignorado).

---

## 5. Instalar (dois cliques)

Com o Docker Desktop aberto, dê **dois cliques em `primeira-instalacao.bat`**. Ele:

1. monta o sistema (a primeira vez demora alguns minutos — deixe a janela aberta);
2. espera ficar pronto;
3. cria o administrador com o e-mail e a senha do `.env`;
4. abre o navegador em **http://localhost:8080**.

Entre com o e-mail e a senha do administrador.

<details>
<summary>Prefere o terminal? (equivalente manual)</summary>

```powershell
cd C:\marmitex
docker compose up -d --build
docker compose exec backend python -m app.cli create-admin
start http://localhost:8080
```
</details>

Depois de criar o administrador, você pode apagar a senha da linha `INITIAL_ADMIN_PASSWORD` do `.env`.

---

## 6. Dia a dia — atalhos

| Atalho (dois cliques) | O que faz |
|---|---|
| **`iniciar-marmitex.bat`** | Abre o Docker se necessário, liga o sistema e abre o navegador |
| `parar-marmitex.bat` | Desliga o sistema (os dados ficam salvos) |
| `backup-agora.bat` | Faz um backup na hora e abre a pasta `backups` para copiar |

Dica: clique com o botão direito em `iniciar-marmitex.bat` → **Enviar para → Área de trabalho (criar atalho)**. Renomeie o atalho para "Marmitex".

Se o Docker Desktop estiver configurado para iniciar com o Windows, o sistema também volta sozinho ao ligar o notebook — basta abrir **http://localhost:8080** (vale salvar nos favoritos do navegador).

### Conferência final

* [ ] O navegador abre http://localhost:8080 e o login funciona.
* [ ] No Docker Desktop, em *Containers*, os serviços `db`, `backend`, `frontend` e `backup` aparecem rodando.
* [ ] Existe um arquivo `marmitex_....dump` dentro da pasta `backups` (o primeiro backup é feito ao ligar).
* [ ] Toda semana, copie a pasta `backups` para um pendrive ou para a nuvem (`OPERACAO.md`, seção 2).

Operação (backup, restauração, atualização, problemas comuns): **`OPERACAO.md`**. Uso das telas: **`GUIA-DO-ADMIN.md`**.

---

## 7. (Opcional) Acessar também de um segundo notebook

Só se um dia precisar. O sistema continua instalado apenas no notebook principal; o segundo usa só o navegador.

1. No `.env` do notebook principal, troque `ACESSO_IP=127.0.0.1` por **`ACESSO_IP=0.0.0.0`** e rode `iniciar-marmitex.bat` (ou `docker compose up -d`).
2. Descubra o IP do notebook principal: PowerShell → `ipconfig` → "Endereço IPv4" (ex.: `192.168.0.15`).
3. Libere a porta 8080 no firewall (PowerShell **como administrador**):

   ```powershell
   New-NetFirewallRule -DisplayName "Marmitex 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow -Profile Private
   ```

   A rede Wi-Fi deve estar marcada como **Privada** no Windows.
4. No segundo notebook, abra **http://192.168.0.15:8080** (o IP do passo 2).

Para voltar ao modo de um notebook só, coloque `ACESSO_IP=127.0.0.1` de novo e reinicie.
