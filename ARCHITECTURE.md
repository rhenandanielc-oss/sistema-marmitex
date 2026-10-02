# ARCHITECTURE.md

# Arquitetura — Sistema de Gestão de Vendas B2B de Marmitex

Este documento descreve a arquitetura alvo do sistema. Ele é a referência para as Fases 1 a 5 e deve ser atualizado sempre que o código divergir dele.

Documentos relacionados:

* `DATABASE.md` — modelo de dados, constraints e índices;
* `API.md` — contrato HTTP;
* `FINANCIAL-RULES.md` — regras financeiras oficiais;
* `DASHBOARD.md` — indicadores, gráficos e filtros;
* `TEST-PLAN.md` — estratégia e cenários de teste.

---

## 1. Visão geral

```
┌──────────────────────┐   HTTPS / JSON    ┌───────────────────────────┐   SQL    ┌──────────────┐
│ Frontend (SPA)       │ ────────────────► │ Backend (FastAPI)         │ ───────► │ PostgreSQL   │
│ React + TS + Vite    │   Bearer token    │ routers → services →      │          │ 16           │
│ Tailwind, Router,    │ ◄──────────────── │ repositories → SQLAlchemy │ ◄─────── │              │
│ React Query          │                   │ motor financeiro (puro)   │          │              │
└──────────────────────┘                   └───────────────────────────┘          └──────────────┘
```

Princípios:

1. **Backend é a fonte de verdade** de datas oficiais, validações, permissões e cálculos financeiros.
2. **Frontend apenas apresenta** valores retornados pela API; não recalcula receita, custos, lucro, médias ou subtotais.
3. **Cálculo financeiro isolado** em um módulo puro (`financial_engine`), sem dependência de banco ou HTTP, testável por unidade.
4. **Auditoria transacional**: o registro de auditoria é gravado na mesma transação da operação auditada.
5. **Nada de secrets no Git**: toda configuração sensível vem de variáveis de ambiente (`.env`), com `.env.example` versionado.

---

## 2. Stack

| Camada | Tecnologia | Observação |
|---|---|---|
| Frontend | React 18, TypeScript (strict), Vite | SPA |
| Estilo | Tailwind CSS | |
| Rotas | React Router | rotas protegidas por sessão |
| Dados remotos | TanStack React Query | cache, invalidação após mutações |
| Formulários | React Hook Form + Zod | validação de UX (o backend revalida tudo) |
| Gráficos | Recharts | |
| Backend | Python 3.12, FastAPI | OpenAPI automático em `/api/docs` |
| Validação | Pydantic v2 | |
| ORM | SQLAlchemy 2.0 (modo síncrono) | endpoints síncronos executados no threadpool do FastAPI |
| Driver | psycopg 3 | |
| Migrations | Alembic | migrations versionadas no Git |
| Hash de senha | Argon2id (`argon2-cffi`) | |
| Token | JWT HS256 (`PyJWT`) vinculado a sessão no banco | permite logout/revogação |
| Banco | PostgreSQL 16 | |
| Testes backend | pytest, httpx/TestClient, PostgreSQL real | não usar SQLite (semântica de `NUMERIC`/datas difere) |
| Testes frontend | Vitest, Testing Library, Playwright (E2E) | |
| Qualidade | ruff, mypy, ESLint, `tsc --noEmit` | |
| Infra | Docker, Docker Compose | |

---

## 3. Estrutura do repositório

```
sistema-marmitex/
├── MASTER-PROMPT.md
├── PROJECT-STATE.md
├── ARCHITECTURE.md  DATABASE.md  API.md  FINANCIAL-RULES.md  DASHBOARD.md  TEST-PLAN.md
├── .env.example
├── docker-compose.yml            # desenvolvimento (db + backend + frontend)
├── docker-compose.prod.yml       # produção (Fase 5)
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── app/
│   │   ├── main.py               # criação do app, middlewares, routers, handlers de erro
│   │   ├── core/
│   │   │   ├── config.py         # Settings (pydantic-settings) lidas do ambiente
│   │   │   ├── db.py             # engine, SessionLocal, dependência get_db
│   │   │   ├── security.py       # hash de senha, JWT, sessões
│   │   │   ├── permissions.py    # papéis × permissões, dependência require_permission
│   │   │   ├── clock.py          # "hoje" no fuso do negócio (injetável em testes)
│   │   │   ├── errors.py         # exceções de domínio → resposta de erro padronizada
│   │   │   └── logging.py        # logs estruturados (JSON) com request_id
│   │   ├── models/               # modelos SQLAlchemy
│   │   ├── schemas/              # modelos Pydantic de entrada/saída
│   │   ├── repositories/         # acesso a dados e consultas agregadas
│   │   ├── services/
│   │   │   ├── financial_engine.py   # funções puras de cálculo (ver FINANCIAL-RULES.md)
│   │   │   ├── periods.py            # resolução de períodos (hoje/semana/mês/personalizado)
│   │   │   ├── audit.py              # gravação de auditoria
│   │   │   └── <entidade>_service.py # regras de negócio por entidade
│   │   └── api/v1/
│   │       ├── router.py
│   │       └── routes/           # auth, users, companies, customers, categories,
│   │                             # sales, costs, history, dashboard, audit, health
│   └── tests/
│       ├── unit/                 # motor financeiro, períodos, validadores
│       └── integration/          # API + PostgreSQL
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── app/                  # providers, router, layout
        ├── api/                  # cliente HTTP, tipos da API, hooks React Query
        ├── auth/                 # contexto de sessão, rota protegida
        ├── components/           # UI compartilhada (tabela, paginação, filtros, KPI, gráfico)
        ├── features/
        │   ├── companies/  customers/  categories/
        │   ├── sales/  costs/
        │   ├── history/
        │   └── dashboard/
        └── lib/                  # formatação pt-BR (moeda, data), utilitários
```

---

## 4. Backend — camadas

| Camada | Responsabilidade | Não pode |
|---|---|---|
| `routes` | HTTP: parâmetros, autenticação/autorização via dependências, status code | conter regra de negócio ou SQL |
| `schemas` | formato e validação sintática de entrada/saída | acessar banco |
| `services` | regras de negócio, validações que dependem do banco, transação, auditoria | montar respostas HTTP |
| `financial_engine` | fórmulas financeiras puras sobre `Decimal` | acessar banco, relógio ou HTTP |
| `repositories` | consultas SQL/ORM, agregações (`SUM`, `GROUP BY`) | decidir regras de negócio |
| `models` | mapeamento das tabelas | — |

Fluxo de uma requisição de escrita (ex.: criar venda):

1. `routes/sales.py` recebe o JSON, valida com `SaleCreate` e exige usuário autenticado e ativo (`ADMIN`).
2. `sales_service.create()` abre a transação e carrega o comprador — **empresa** (empreiteira) **ou** **cliente avulso**, nunca os dois — validando que existe e está ativo.
3. A data da venda é a informada pelo ADMIN (para lançamentos esquecidos) ou, se omitida, `clock.today()` (fuso `APP_TIMEZONE`); nunca futura. O subtotal é calculado por `financial_engine.sale_subtotal()`.
4. A venda é inserida e `audit.record(...)` grava o registro de auditoria na mesma transação.
5. Commit; a resposta é serializada por `SaleRead`.

Fluxo de leitura do dashboard:

1. `routes/dashboard.py` recebe `period`/`start_date`/`end_date`/`company_id`.
2. `periods.resolve()` converte em intervalo fechado `[start, end]` usando a data do servidor.
3. `repositories/dashboard_repo.py` executa agregações no PostgreSQL (somas por dia, por tipo, por empresa).
4. `financial_engine` combina os agregados (lucro, custo médio, ticket médio, rateio) e aplica arredondamento.
5. A resposta é devolvida com valores monetários como strings decimais.

---

## 5. Decisões arquiteturais

### D-01 — Monorepo com `backend/` e `frontend/`
Um único repositório, coerente com "o repositório é a fonte de verdade". A documentação fica na raiz.

### D-02 — SQLAlchemy síncrono
O volume esperado (uma operação de marmitex B2B) não justifica a complexidade do modo assíncrono. Endpoints `def` rodam no threadpool do FastAPI. Pode ser revisto na auditoria de performance.

### D-03 — Valores monetários com `Decimal` e `NUMERIC`
Nunca usar `float` para dinheiro. Banco: `NUMERIC(12,2)` para valores unitários/lançamentos. Python: `decimal.Decimal`. JSON: string decimal com ponto (`"1234.50"`), evitando perda de precisão em JavaScript. O frontend formata para `R$ 1.234,50` apenas na exibição.

### D-04 — Datas no fuso do negócio
* `APP_TIMEZONE` (padrão `America/Sao_Paulo`) define o "hoje" do negócio.
* Datas de negócio (`sale_date`, `cost_date`) são `DATE` (sem hora).
* Carimbos técnicos (`created_at`, `updated_at`) são `TIMESTAMPTZ` em UTC.
* Todo acesso ao "hoje" passa por `core/clock.py`, que é substituível em testes.

### D-05 — Autenticação por token vinculado a sessão
* Login devolve um JWT de acesso (HS256, expiração configurável, padrão 8 h) com `sub` (usuário) e `sid` (sessão).
* A tabela `user_sessions` guarda a sessão; logout define `revoked_at`.
* Toda requisição autenticada valida assinatura, expiração, sessão não revogada e usuário ativo.
* Desativar um usuário revoga todas as suas sessões.
* O frontend guarda o token em memória e `sessionStorage` (some ao fechar a aba) e envia `Authorization: Bearer <token>`.
* Não se usa cookie, portanto não há superfície de CSRF; o risco de XSS é mitigado por CSP e por não renderizar HTML vindo do usuário.

### D-06 — Papel único `ADMIN`
Há um único papel, `ADMIN`, que lança todas as vendas e todos os custos, mantém os cadastros e consulta histórico, dashboard e auditoria. Pode haver mais de um usuário ADMIN (ex.: dono e sócio), cada um com login próprio para que a auditoria identifique quem fez cada operação.

Implementação: coluna `users.role` restrita a `'ADMIN'` e dependência `require_admin` em `core/permissions.py`, aplicada a todas as rotas protegidas. A coluna e a dependência existem para permitir novos papéis no futuro sem refatoração, mas **nenhum outro papel é implementado agora**. Detalhes em `API.md`, seção 2.

### D-07 — Exclusão lógica
Cadastros são **desativados** (`is_active = false`), nunca apagados. Vendas e custos usam `deleted_at` (exclusão lógica) e deixam de entrar em cálculos e listagens, permanecendo para auditoria.

### D-08 — Concorrência otimista
Entidades editáveis possuem coluna `version` (inteiro). Toda edição envia a `version` lida; se divergir, a API responde `409 CONFLICT`. Evita que duas pessoas sobrescrevam a mesma venda/custo sem perceber.

### D-09 — Agregações no banco, fórmulas no motor financeiro
Somas e agrupamentos são feitos em SQL (eficiente, com índices). As fórmulas derivadas (lucro, médias, rateio, arredondamento) ficam em `financial_engine.py` para serem testadas isoladamente e não haver duas implementações da mesma regra.

### D-10 — Testes de integração com PostgreSQL real
Os testes de integração usam um PostgreSQL de teste (serviço do Docker Compose ou do CI), com migrations aplicadas e transação revertida por teste.

---

## 6. Frontend

* Interface em português (pt-BR), otimizada para desktop/notebook (largura mínima de referência 1280 px; utilizável a partir de 1024 px).
* Layout: menu lateral com as áreas **Cadastros**, **Lançamentos**, **Histórico** e **Dashboard**; cabeçalho com usuário e "Sair".
* Rotas:

| Rota | Tela | Acesso |
|---|---|---|
| `/login` | Login | pública |
| `/cadastros/empresas` | Empresas (empreiteiras) | ADMIN |
| `/cadastros/clientes` | Clientes avulsos | ADMIN |
| `/cadastros/categorias` | Tipos/categorias de custo (ex.: Ingredientes, Embalagens) | ADMIN |
| `/lancamentos/vendas` | Lançar/listar vendas (data escolhida pelo ADMIN, padrão hoje) | ADMIN |
| `/lancamentos/custos` | Lançar/listar custos do restaurante | ADMIN |
| `/historico` | Consulta de vendas e custos | ADMIN |
| `/dashboard` | Dashboard geral, por empresa (`?empresa=<id>`) e por cliente (`?cliente=<id>`) | ADMIN |

* Todas as rotas, exceto `/login`, exigem sessão válida; a proteção real é sempre feita pela API.
* No lançamento de venda, o ADMIN escolhe primeiro o tipo de comprador (**Empresa** ou **Cliente avulso**) e depois o comprador.
* Selects de empresa/cliente/categoria em lançamentos carregam **somente registros ativos** (`?active=true`).
* Feedback: estados de carregamento, mensagens de sucesso (toast), erros de validação por campo (mapeados de `error.details`), confirmação antes de desativar/excluir.
* React Query: invalidação das listas, histórico e dashboard após qualquer mutação.

---

## 7. Configuração (variáveis de ambiente)

| Variável | Exemplo | Uso |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://marmitex:***@db:5432/marmitex` | conexão |
| `JWT_SECRET` | (gerado, ≥ 32 bytes) | assinatura do token |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | expiração |
| `APP_TIMEZONE` | `America/Sao_Paulo` | "hoje" do negócio |
| `CORS_ORIGINS` | `http://localhost:5173` | origens permitidas |
| `LOG_LEVEL` | `INFO` | logs |
| `ENVIRONMENT` | `development` / `production` | ajustes (ex.: desativar `/api/docs` em produção se desejado) |
| `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD` | — | criação do primeiro admin por comando (`python -m app.cli create-admin`) |
| `VITE_API_BASE_URL` | `/api/v1` | base da API no frontend |

Os valores reais ficam somente em `.env` (ignorado pelo Git). `.env.example` contém apenas placeholders.

---

## 8. Observabilidade e operação

* Logs estruturados em JSON, com `request_id` (header `X-Request-ID`), método, rota, status e duração. Senhas e tokens nunca são logados.
* Health checks: `GET /api/v1/health/live` (processo vivo) e `GET /api/v1/health/ready` (banco acessível).
* Backup: `pg_dump` agendado (Fase 5), com procedimento de restauração documentado e testado.
* Migrations aplicadas no deploy (`alembic upgrade head`) antes de iniciar a nova versão.

---

## 9. Segurança (resumo)

* Senhas com Argon2id; política mínima de 8 caracteres.
* Limitação de tentativas de login (por e-mail + IP) com resposta genérica "credenciais inválidas".
* Todas as rotas, exceto `/auth/login` e `/health/*`, exigem autenticação.
* Validação de entrada em todas as rotas (Pydantic) e regras de negócio no serviço.
* SQL apenas via ORM/parâmetros (sem concatenação de strings).
* CORS restrito a `CORS_ORIGINS`.
* Cabeçalhos de segurança no proxy/servidor do frontend (CSP, `X-Content-Type-Options`, `Referrer-Policy`).
* Dados de seed/teste são fictícios.
