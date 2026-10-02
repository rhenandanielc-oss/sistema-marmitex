# INSTALL.md

# Instalação — Sistema Marmitex B2B

Guia para instalar o sistema no **notebook principal** (servidor) e acessá-lo também de um **segundo notebook** na mesma rede (Wi-Fi/roteador). Tempo estimado: 30 a 60 minutos.

---

## 1. Como funciona

```
Notebook principal (servidor)                  Segundo notebook (opcional)
┌──────────────────────────────────┐           ┌───────────────────────────┐
│ Docker Desktop                   │  Wi-Fi /  │ Navegador (Chrome/Edge)   │
│  ├─ frontend  (telas)    :8080 ◄─┼───rede────┤ http://192.168.x.x:8080   │
│  ├─ backend   (cálculos)         │   local   └───────────────────────────┘
│  ├─ db        (PostgreSQL)       │
│  └─ backup    (cópia diária)     │
│ pasta backups/  ← arquivos .dump │
└──────────────────────────────────┘
```

* Tudo roda no notebook principal. O segundo notebook só usa o navegador.
* O notebook principal precisa estar **ligado** para o outro acessar.
* Os dados ficam no próprio notebook (não vão para a internet).

---

## 2. Requisitos do notebook principal

| Item | Mínimo |
|---|---|
| Sistema | Windows 10/11 (64 bits), macOS ou Linux |
| Memória | 8 GB de RAM |
| Disco livre | 10 GB |
| Programas | **Docker Desktop** (inclui o Docker Compose) e **Git** (opcional — pode baixar o ZIP) |

### Windows

1. Instale o **Docker Desktop**: https://www.docker.com/products/docker-desktop/ — aceite usar o **WSL 2** quando perguntado e reinicie o notebook.
2. Abra o Docker Desktop e, em *Settings → General*, marque **"Start Docker Desktop when you sign in"** (o sistema volta sozinho quando o notebook liga).
3. (Opcional) Instale o **Git**: https://git-scm.com/download/win

### Linux

Instale `docker` e o plugin `docker compose` pelo gerenciador de pacotes da distribuição e habilite o serviço (`sudo systemctl enable --now docker`).

---

## 3. Baixar o sistema

Abra o **PowerShell** (Windows) ou o terminal e escolha uma pasta, por exemplo `C:\marmitex`:

```powershell
cd C:\
git clone https://github.com/rhenandanielc-oss/sistema-marmitex.git marmitex
cd marmitex
```

Sem Git: baixe o ZIP do repositório no GitHub, extraia em `C:\marmitex` e abra o PowerShell nessa pasta.

---

## 4. Configurar (arquivo `.env`)

1. Copie o modelo:

   ```powershell
   copy .env.example .env      # Windows
   # cp .env.example .env      # Linux/macOS
   ```

2. Gere um segredo aleatório (copie o resultado):

   ```powershell
   docker run --rm python:3.12-alpine python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

3. Abra o `.env` no Bloco de Notas e altere **obrigatoriamente**:

   | Linha | O que colocar |
   |---|---|
   | `POSTGRES_PASSWORD=` | uma senha forte para o banco (sem espaços) |
   | `DATABASE_URL=` | troque `troque-esta-senha` pela **mesma** senha acima |
   | `JWT_SECRET=` | o segredo gerado no passo 2 |
   | `INITIAL_ADMIN_EMAIL=` | o e-mail do administrador |
   | `INITIAL_ADMIN_PASSWORD=` | a senha do administrador (mínimo 8 caracteres) |

   Deixe `ENVIRONMENT=production`. Com valores de exemplo o sistema **se recusa a iniciar** — é proposital.

> O arquivo `.env` contém senhas: **não** envie para ninguém e não coloque no Git (ele já é ignorado).

---

## 5. Iniciar

```powershell
docker compose up -d --build
```

A primeira vez demora alguns minutos (baixa e monta tudo). Depois, confira:

```powershell
docker compose ps
```

Os serviços `db`, `backend`, `frontend` e `backup` devem aparecer como **running** / **healthy**.

### Criar o primeiro administrador

```powershell
docker compose exec backend python -m app.cli create-admin
```

Usa `INITIAL_ADMIN_EMAIL` e `INITIAL_ADMIN_PASSWORD` do `.env`. Depois de criado, você pode apagar a senha dessas linhas do `.env` e cadastrar outros administradores pela tela **Usuários**.

### Acessar

* No notebook principal: **http://localhost:8080**
* Entre com o e-mail e a senha do administrador.

---

## 6. Acessar pelo segundo notebook

1. No notebook principal, descubra o IP na rede:
   * Windows: `ipconfig` → "Endereço IPv4" (ex.: `192.168.0.15`)
   * Linux/macOS: `ip addr` / `ifconfig`
2. Libere a porta **8080** no firewall do notebook principal (Windows, PowerShell **como administrador**):

   ```powershell
   New-NetFirewallRule -DisplayName "Marmitex 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow -Profile Private
   ```

   Garanta que a rede Wi-Fi esteja marcada como **Privada** no Windows.
3. No segundo notebook, abra o navegador em **http://192.168.0.15:8080** (use o IP do passo 1).

Dica: no roteador, reserve um IP fixo para o notebook principal (reserva DHCP) para o endereço não mudar.

---

## 7. Conferência final

* [ ] `docker compose ps` mostra os 4 serviços rodando.
* [ ] http://localhost:8080 abre a tela de login.
* [ ] Login com o administrador funciona.
* [ ] Existe pelo menos um arquivo em `backups/` (o primeiro backup é feito ao iniciar).
* [ ] O segundo notebook abre o sistema pelo IP.

Operação do dia a dia (backup, restauração, atualização, problemas comuns): **`OPERACAO.md`**.
Como usar as telas: **`GUIA-DO-ADMIN.md`**.
