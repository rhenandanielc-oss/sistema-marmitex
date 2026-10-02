# PROJECT-STATE.md

# Sistema de Gestão de Vendas B2B de Marmitex e Controle Financeiro

Este arquivo representa o estado atual do projeto.

O Claude Code deve atualizá-lo ao final de cada etapa significativa.

---

# STATUS GERAL

**Status:** CONCLUÍDO (pendente apenas a validação do `docker compose up -d --build` no notebook)

**Fase atual:** Fases 0 a 5 CONCLUÍDAS.

**Última atualização:** 2026-10-02 (Sessão 1).

**Último commit:** `feat: production readiness (phase 5)` (branch `claude/sistema-marmitex-b2b-j8apnv`).

**Próxima ação:** Instalar no notebook seguindo `INSTALL.md` (preencher `.env` e dois cliques em `primeira-instalacao.bat`), conferir a seção 6 e configurar a cópia externa dos backups.

---

# FASE 0 — ARQUITETURA

**Status:** CONCLUÍDA (2026-10-02)

### Entregáveis

* [x] `ARCHITECTURE.md` — stack, camadas, estrutura de pastas, decisões D-01 a D-10, configuração, segurança
* [x] `DATABASE.md` — tabelas, constraints, índices, seed de categorias, consultas de referência, migrations
* [x] `API.md` — convenções (paginação, ordenação, erros, concorrência), matriz de permissões, todos os endpoints
* [x] `FINANCIAL-RULES.md` — regras R-*/fórmulas F-01 a F-13, arredondamento, períodos, exemplos numéricos de referência
* [x] `DASHBOARD.md` — filtros, KPIs, gráficos, dashboard por empresa
* [x] `TEST-PLAN.md` — níveis de teste, cenários FIN-01 a FIN-22 e demais casos

### Testes

Não aplicável (fase somente de documentação). Os valores esperados dos cenários financeiros em `TEST-PLAN.md` foram conferidos manualmente a partir de `FINANCIAL-RULES.md` seção 7.

### Decisões

Ver "Decisões técnicas" abaixo.

---

# FASE 1 — BANCO, AUTENTICAÇÃO E CADASTROS

**Status:** CONCLUÍDA (2026-10-02)

### Banco

* [x] PostgreSQL
* [x] Docker (`backend/Dockerfile`, `docker-compose.yml` validado com `docker compose config`; build da imagem não executado — sem daemon Docker no ambiente da sessão)
* [x] migrations
* [x] modelos
* [x] relacionamentos
* [x] constraints
* [x] índices

### Autenticação

* [x] usuários
* [x] login
* [x] logout
* [x] sessões/tokens
* [x] papel único ADMIN (`require_admin`)
* [x] auditoria

### Cadastros

#### Empresas (empreiteiras)

* [x] criar
* [x] editar
* [x] ativar
* [x] desativar
* [x] pesquisar
* [x] filtrar

#### Clientes avulsos (independentes)

* [x] criar
* [x] editar
* [x] ativar
* [x] desativar
* [x] pesquisar
* [x] filtrar

#### Categorias

* [x] criar
* [x] editar
* [x] ativar
* [x] desativar
* [x] pesquisar

### Arquivos importantes

* `backend/app/models/` — modelos (users, user_sessions, companies, customers, cost_categories, sales, costs, audit_logs)
* `backend/alembic/versions/0001_initial_schema.py`, `0002_seed_cost_categories.py`
* `backend/app/core/` — config, db, clock, security (Argon2id, JWT+sessão, limite de login), permissions (`require_admin`), errors, logging
* `backend/app/services/` — auth, user, registry (empresas/clientes/categorias), audit, validators (CPF/CNPJ)
* `backend/app/api/v1/routes/` — health, auth, users, registry, audit
* `backend/app/cli.py` — `python -m app.cli create-admin`
* `.env.example`, `docker-compose.yml`, `backend/Dockerfile`

### Testes

`cd backend && pytest` — 45 testes (migrations up/down/up + modelos = migrations, autenticação, usuários, cadastros, erros, paginação, auditoria). Todos passando. `ruff check .` e `mypy app` sem problemas.

---

# FASE 2 — VENDAS, CUSTOS E MOTOR FINANCEIRO

**Status:** CONCLUÍDA (2026-10-02)

### Vendas

* [x] comprador único (empresa OU cliente avulso)
* [x] preço unitário
* [x] quantidade
* [x] data escolhida pelo ADMIN (padrão hoje, nunca futura)
* [x] subtotal
* [x] validações
* [x] edição
* [x] auditoria

### Custos

* [x] valor
* [x] categoria
* [x] tipo
* [x] data
* [x] validações
* [x] auditoria

### Tipos de custo

* [x] `CUSTO_DIARIO`
* [x] `CUSTO_FIXO`

### Categorias

#### Diários

* [x] Ingredientes
* [x] Embalagens
* [x] Entregas
* [x] Equipamentos
* [x] Gasolina

#### Fixos

* [x] Salários
* [x] Aluguel
* [x] Água
* [x] Energia elétrica
* [x] Gás

---

# MOTOR FINANCEIRO

### Regras

* [x] receita
* [x] custos totais
* [x] lucro líquido
* [x] custo médio por marmita
* [x] divisão por zero
* [x] período inclusivo
* [x] lucro líquido geral (empresas + clientes + todos os custos)
* [x] faturamento por empresa/cliente
* [x] custos acumulados

### Fórmulas

`RECEITA = soma dos subtotais`

`CUSTOS_TOTAIS = custos fixos + custos diários`

`LUCRO_LIQUIDO = receita - custos totais`

`CUSTO_MEDIO_POR_MARMITA = custos totais / quantidade de marmitas`

### Testes

* [x] dia
* [x] semana
* [x] mês
* [x] período personalizado
* [x] empresa
* [x] várias empresas
* [x] sem vendas
* [x] sem custos
* [x] sem vendas e sem custos
* [x] divisão por zero
* [x] somente custos fixos
* [x] somente custos diários
* [x] vendas sem custos
* [x] custos sem vendas
* [x] Σ faturamento por comprador = receita
* [x] último acumulado de custos = custos totais

Todos os cenários FIN-01 a FIN-29 do `TEST-PLAN.md` estão cobertos (unitário + integração), mais teste de propriedade (Hypothesis, 200 exemplos).

### Arquivos importantes

* `backend/app/services/financial_engine.py` — fórmulas puras (F-01 a F-18, acumulados, divisão segura, ROUND_HALF_UP)
* `backend/app/services/periods.py` — hoje/semana/mês/mês anterior/personalizado, período anterior, limite de 366 dias
* `backend/app/repositories/financial_repo.py` — agregações SQL (somas por tipo, por dia, por comprador)
* `backend/app/services/financial_service.py` — resumo geral, série diária, faturamento por comprador, detalhe de empresa/cliente (base do dashboard da Fase 3)
* `backend/app/services/entries_service.py` — vendas e custos (validações, data escolhida pelo ADMIN, auditoria, acumulado)
* `backend/app/api/v1/routes/entries.py` — `/sales`, `/costs` (com `running_total` e `totals`), `/costs/summary`

### Testes

`cd backend && pytest` — **161 testes, todos passando** (47 unitários + 114 de integração com PostgreSQL). `ruff check .` e `mypy app` sem problemas.


---

# FASE 3 — API

**Status:** CONCLUÍDA (2026-10-02) — backend; telas na Fase 4

### Endpoints

* [x] autenticação
* [x] empresas
* [x] clientes
* [x] categorias
* [x] vendas
* [x] custos
* [x] histórico
* [x] dashboard

### Dashboard

* [x] resumo financeiro
* [x] vendas diárias
* [x] faturamento por comprador (`/dashboard/by-buyer`)
* [x] quantidade diária
* [x] custos diários
* [x] lucro diário
* [x] histórico por empresa
* [x] dashboard por cliente avulso

### Recursos

* [x] filtros
* [x] paginação
* [x] ordenação
* [x] tratamento de erros
* [x] autorização
* [x] OpenAPI
* [x] testes de integração

### Arquivos importantes

* `backend/app/api/v1/routes/reports.py` — `/history` e `/dashboard/*` (summary, daily, by-buyer, sales-by-company-daily, companies/{id}, customers/{id})
* `backend/app/services/history_service.py` — histórico unificado (UNION de vendas e custos) com totais
* `backend/app/schemas/reports.py` — formatos de resposta
* `backend/tests/integration/test_reports.py` — 28 testes HTTP (DSH-*, HIS-*)

### Testes

`cd backend && pytest` — **189 testes, todos passando**. `ruff` e `mypy` OK.

---

# FASE 4 — FRONTEND

**Status:** CONCLUÍDA (2026-10-02)

### Rotas

* [x] `/login`
* [x] `/cadastros/empresas`
* [x] `/cadastros/clientes`
* [x] `/cadastros/categorias`
* [x] `/lancamentos/vendas`
* [x] `/lancamentos/custos`
* [x] `/historico`
* [x] `/dashboard` (geral, `?empresa=`, `?cliente=`)
* [x] `/usuarios` (adicional: usuários ADMIN e troca de senha)

### Funcionalidades

* [x] login
* [x] empresas
* [x] clientes
* [x] categorias
* [x] vendas
* [x] custos
* [x] histórico
* [x] dashboard
* [x] dashboard por empresa
* [x] dashboard por cliente avulso
* [x] vendas: tipo de comprador, data editável (padrão hoje), preço sugerido pela última venda do comprador
* [x] custos: totais do mês sempre visíveis + coluna Acumulado
* [x] histórico: filtros na URL, totais para fechamento quinzenal/mensal

### Arquivos importantes

* `frontend/src/app/` (rotas, menu, login), `frontend/src/api/` (cliente HTTP, tipos), `frontend/src/features/*` (telas)
* `frontend/src/components/charts.tsx` — gráficos com paleta validada e "Ver tabela"
* `frontend/Dockerfile`, `frontend/nginx.conf`, serviço `frontend` no `docker-compose.yml` (porta 8080)

### Testes

* `cd frontend && npm run test` — 18 testes (formatação, cliente da API, rotas protegidas, vendas, custos, dashboard). Todos passando.
* `npm run typecheck`, `npm run lint`, `npm run build` — OK.
* `npm run e2e` — 4 fluxos Playwright (cadastro → vendas → histórico → dashboard; novo tipo de custo → acumulado; venda esquecida com data de ontem + empresa desativada; logout) contra o sistema completo. Todos passando.
* Conferência visual por capturas de tela com dados fictícios (setembro: receita R$ 89.026,50; custos R$ 52.828,39; lucro R$ 36.198,11).


---

# HISTÓRICO

_API concluída na Fase 3 (`GET /history`); tela na Fase 4._

### Filtros

* [x] empresa
* [x] cliente
* [x] data inicial
* [x] data final
* [x] tipo

### Vendas

* [x] data
* [x] empresa
* [x] cliente
* [x] quantidade
* [x] preço
* [x] subtotal

### Custos

* [x] data
* [x] categoria
* [x] tipo
* [x] valor

### Recursos

* [x] paginação
* [x] ordenação
* [x] filtros

---

# DASHBOARD

### Indicadores

* [x] Receita Total
* [x] Custos Fixos
* [x] Custos Diários
* [x] Custos Totais
* [x] Lucro Líquido
* [x] Quantidade de Marmitas
* [x] Custo Médio por Marmita

### Gráficos

* [x] receita diária
* [x] quantidade diária
* [x] receita por empresa
* [x] receita total
* [x] custos diários
* [x] lucro diário
* [x] histórico de vendas por empresa

### Filtros

* [x] hoje
* [x] semana
* [x] mês
* [x] período personalizado
* [x] empresa

---

# DASHBOARD POR EMPRESA

**Status:** CONCLUÍDO

* [x] selecionar empresa
* [x] receita
* [x] quantidade
* [x] ticket médio
* [x] histórico diário
* [x] clientes — substituído: clientes avulsos não pertencem a empresas (decisão de 2026-10-02); há dashboard próprio por cliente
* [x] vendas
* [x] evolução do período

---

# FASE 5 — AUDITORIA E PRODUÇÃO

**Status:** CONCLUÍDA (2026-10-02) — exceto validação do build Docker no notebook (ver Problemas conhecidos)

### Auditoria

* [x] banco
* [x] API
* [x] frontend
* [x] autenticação
* [x] autorização
* [x] filtros
* [x] datas
* [x] valores monetários
* [x] arredondamento
* [x] concorrência
* [x] auditoria
* [x] performance

### Produção

* [x] Dockerfiles (backend, frontend/Nginx) — build a validar no notebook
* [x] configuração de produção
* [x] migrations
* [x] `.env.example`
* [x] health checks
* [x] logs
* [x] backup
* [x] documentação de instalação
* [x] documentação de deploy

Relatório completo: **`AUDITORIA.md`**. Documentos: `README.md`, `INSTALL.md`, `OPERACAO.md`, `GUIA-DO-ADMIN.md`. Scripts: `ops/`.


---

# DECISÕES TÉCNICAS

As decisões arquiteturais completas estão em `ARCHITECTURE.md` seção 5. Abaixo, as decisões que afetam regras de negócio.

Decisões validadas com o negócio em 2026-10-02 (revisão da Fase 0):

### 2026-10-02 — Empresas e clientes avulsos são entidades independentes

**Problema:** relação entre empresas e clientes não definida no MASTER-PROMPT.
**Decisão (validada):** empresas = empreiteiras (principais compradoras, maior volume, faturamento quinzenal/mensal); clientes = compradores avulsos, sem vínculo com empresas (ex.: trabalhador da mesma obra que paga mensalmente). Cada venda tem **um único comprador**: empresa **ou** cliente (`sales.buyer_type` + `CHECK`).
**Impacto:** substitui a exigência "venda com empresa e cliente" do MASTER-PROMPT §6/§9; `billing_cycle` nos dois cadastros; dashboard por empresa não lista "clientes da empresa" (não há vínculo) — em vez disso existe dashboard por cliente avulso. Ver `DATABASE.md` 3.3, 3.4, 3.6.

### 2026-10-02 — Lucro líquido somente geral; faturamento por empresa (corrigido)

**Problema:** a revisão anterior previa lucro por empresa via rateio de custos.
**Decisão (correção do negócio):** os custos são gerais do restaurante; **não há rateio nem lucro por comprador**. Lucro líquido só no nível geral (empresas + clientes + todos os custos). Por empresa/cliente apenas **faturamento** (receita, marmitas, vendas, ticket médio, preço médio, participação, variação).
**Impacto:** `FINANCIAL-RULES.md` seção 6 (R-FAT-*, F-12 a F-18); `/dashboard/by-buyer` sem custo/lucro.

### 2026-10-02 — Custos acumulados

**Decisão (validada):** a cada novo custo, o total vai somando. Listagem de custos com coluna `running_total` (acumulado cronológico), totais do mês corrente sempre visíveis na tela de custos (`/costs/summary`) e séries `cumulative_costs`/`cumulative_net_profit` no dashboard (R-CUS-7, R-CUS-8).

### 2026-10-02 — Data de início e data de pagamento nos cadastros

**Decisão (validada):** empresas e clientes avulsos têm `start_date` (início do fornecimento) e `payment_date` (data de pagamento combinada), ambas opcionais e informadas pelo ADMIN. Campos informativos (não geram cobrança automática).

### 2026-10-02 — Uso em 1 a 2 notebooks

**Decisão:** implantação local simples (um notebook com Docker Compose; o outro acessa pela rede local). Metas de performance proporcionais. Ver `ARCHITECTURE.md` D-11.

### 2026-10-02 — Categorias de custo administráveis

**Decisão (validada):** aba de cadastro onde o ADMIN cria novos tipos de custo (ex.: Embalagens, Ingredientes), cada um classificado como diário ou fixo.

### 2026-10-02 — Reconhecimento de custos na data do lançamento

**Decisão (validada):** custo reconhecido integralmente em `cost_date`, sem rateio entre dias (R-CUS-5). Lucro negativo em um dia/semana é aceitável; o foco é o lucro líquido do mês com gráficos (período padrão `month`, atalho `last_month`, gráfico de lucro acumulado).

### 2026-10-02 — Papel único ADMIN e data escolhida pelo ADMIN

**Decisão (validada):** apenas o papel `ADMIN`, que lança todas as vendas e custos. A data de venda e de custo é escolhida pelo ADMIN (padrão: hoje do servidor, fuso `America/Sao_Paulo`), permitindo lançar o que foi esquecido; nunca futura; toda alteração auditada.
**Impacto:** substitui "data oficial vem do servidor" (MASTER-PROMPT §9) e a matriz de papéis/permissões; mantém-se `users.role` e `require_admin` para extensão futura. Ver `ARCHITECTURE.md` D-06 e `API.md` seção 2.

### 2026-10-02 — Data de pagamento e local/obra

**Decisão (validada):** a data de pagamento continua sendo uma data alterável pelo ADMIN (não um dia fixo do mês). Empresas também têm **local/obra**.

### 2026-10-02 — Recebimento e pagamento

**Pedido do negócio:** ao cadastrar e ao lançar venda, informar se o cliente pagou e se é retirada, entrega ou obra, para separar os clientes.
**Decisão:** cadastro (empresa e cliente) tem **recebimento padrão** (`RETIRADA`/`ENTREGA`/`OBRA`); cada venda tem **recebimento** (herdado do cadastro, alterável) e **pagamento** (`PENDENTE`/`PAGO`, botão "Marcar pago"). A situação de pagamento fica na venda (um cliente pode ter vendas pagas e pendentes). Receita conta todas as vendas; "A receber" é informativo (R-VEN-9 a R-VEN-11, F-19).

### 2026-10-02 — Instalação em um notebook só

**Pedido do negócio:** instalação e uso mexendo em apenas um notebook.
**Decisão:** modo padrão de um notebook — porta 8080 presa a `127.0.0.1` (`ACESSO_IP` no `.env`), sem configuração de rede/firewall; atalhos Windows `primeira-instalacao.bat`, `iniciar-marmitex.bat`, `parar-marmitex.bat`, `backup-agora.bat`; segundo notebook virou opcional (`INSTALL.md` §7). `.gitattributes` garante CRLF nos `.bat` e LF nos `.sh` usados pelos contêineres.

### 2026-10-02 — Períodos pré-definidos

**Decisão:** hoje; semana = segunda-feira corrente até hoje; mês = dia 1 até hoje (padrão); mês anterior = mês fechado; personalizado. Resolvidos no backend.

### Fora do escopo atual

Contas a receber / controle de pagamentos de empresas e clientes. O fechamento (total a cobrar no período) é obtido pelo Histórico com filtro de comprador e período.

---

# REGRAS FINANCEIRAS

As regras oficiais estão em `FINANCIAL-RULES.md`.

Resumo:

* receita é a soma dos subtotais;
* custos totais = custos fixos + custos diários;
* lucro líquido = receita − custos totais;
* custo médio = custos totais ÷ quantidade;
* divisão por zero deve ser tratada;
* períodos são inclusivos;
* cálculos críticos ficam no backend.

---

# SEGURANÇA

* [x] autenticação
* [x] autorização
* [x] proteção de endpoints
* [x] hash de senha
* [x] expiração de sessão
* [x] auditoria
* [x] `.env`
* [x] `.env.example`
* [x] nenhum secret no Git

---

# PROBLEMAS CONHECIDOS

### Build Docker não verificado

**Descrição:** o ambiente das sessões de desenvolvimento não possui daemon Docker; as imagens `backend` e `frontend` não foram construídas (o `docker compose config` é válido e tudo foi testado fora do Docker).
**Impacto:** pode exigir um pequeno ajuste na primeira instalação.
**Status:** aberto.
**Solução:** executar `docker compose up -d --build` no notebook e seguir `INSTALL.md` §5–6.

### Agendamento do backup (BusyBox `date -d`)

**Descrição:** horário fixo do backup depende do `date` do Alpine; não testado aqui.
**Impacto:** se falhar, o backup ocorre a cada 24 h desde o início (plano B automático).
**Status:** aberto — conferir `docker compose logs backup` na primeira semana.

Formato:

### Problema

**Descrição:**
...

**Impacto:**
...

**Status:**
...

**Solução:**
...

---

# RISCOS

* **disponibilidade:** o notebook precisa estar ligado (e, no modo opcional, para o segundo notebook acessar); backup local + cópia externa obrigatórios (Fase 5).
* **datas:** como o ADMIN escolhe a data, lançamentos em data errada são possíveis — mitigado por valor padrão = hoje, bloqueio de data futura e auditoria.
* **datas:** fuso horário incorreto no servidor geraria vendas no dia errado — mitigado por `APP_TIMEZONE` e teste FIN-20.
* **concorrência:** edições simultâneas — mitigado por `version` (409).
* **segurança:** token em `sessionStorage` é exposto em caso de XSS — mitigado por CSP e por não renderizar HTML de usuário.

Possíveis categorias:

* segurança;
* banco;
* concorrência;
* cálculos;
* arredondamento;
* datas;
* performance;
* disponibilidade.

---

# ÚLTIMAS ALTERAÇÕES

### 2026-10-02 — Modo de um notebook

* `ACESSO_IP` (padrão `127.0.0.1`) no `docker-compose.yml`/`.env.example`; atalhos `.bat`; `INSTALL.md` reescrito para um notebook; `.gitattributes`.
* Atalhos `.bat` não executados nesta sessão (ambiente Linux) — validar na instalação.

### 2026-10-02 — Fase 5

* Validação de segurança na inicialização em produção; `/api/docs` desligado em produção.
* Dependências atualizadas (React Router 7, Vite 8, Vitest 5; pip/setuptools na imagem) — 0 vulnerabilidades.
* Backup diário + restauração (`ops/`), healthchecks, rotação de logs no `docker-compose.yml`.
* Teste de concorrência real; teste de performance (~16 mil vendas, < 70 ms); otimização da série por empresa.
* Documentação: `README.md`, `INSTALL.md`, `OPERACAO.md`, `GUIA-DO-ADMIN.md`, `AUDITORIA.md`.
* Testes: backend 199, frontend 19, E2E 4 — todos passando.

### 2026-10-02 — Recebimento e pagamento

* Migration `0004_delivery_and_payment`; filtros por pagamento/recebimento em vendas, histórico e cadastros; "A receber" no dashboard geral, por comprador e no histórico; botão "Marcar pago".
* Testes: backend 193, frontend 19, E2E 4 — todos passando.

### 2026-10-02 — Fase 4

* Campo **local/obra** no cadastro de empresas (migration `0003_company_location`). Data de pagamento confirmada como data alterável pelo ADMIN.
* Frontend completo em português: login, cadastros, vendas, custos (acumulado), histórico, dashboard geral, por empresa e por cliente, usuários.
* API: `cumulative_revenue` na série diária; parâmetro `top` em `/dashboard/sales-by-company-daily`.
* Docker do frontend (Nginx) e serviço no `docker-compose.yml`.

### 2026-10-02 — Fase 3

* `/history` (vendas + custos, filtros, ordenação, paginação, totais para fechamento quinzenal/mensal).
* `/dashboard/summary`, `/daily`, `/by-buyer`, `/sales-by-company-daily`, `/companies/{id}`, `/customers/{id}`.
* Testes: 189 passando.

### 2026-10-02 — Fases 1 e 2

* Fase 1: backend FastAPI, modelos, migrations, autenticação (ADMIN), usuários, empresas, clientes avulsos (com data de início e de pagamento), categorias, auditoria, Docker.
* Fase 2: vendas (comprador único, data escolhida pelo ADMIN), custos (acumulado e resumo do mês), motor financeiro e serviço financeiro.
* Testes: 161 passando.

### 2026-10-02 — correção do negócio

* Custos gerais: removidos rateio e lucro por empresa; por empresa/cliente somente faturamento.
* Cadastros de empresas e clientes com data de início e data de pagamento.
* Custos acumulados (listagem, resumo do mês e séries do dashboard).
* Implantação para 1–2 notebooks.

### 2026-10-02 — revisão com o negócio

* Clientes avulsos independentes das empresas; venda com comprador único.
* Lucro líquido geral e por empresa/cliente com rateio de custos por marmita.
* Papel único ADMIN; data de venda/custo escolhida pelo ADMIN.
* Custos fixos na data do lançamento confirmados; foco no lucro mensal (período `last_month`, gráfico de lucro acumulado).
* Arquivos: todos os documentos de arquitetura e `PROJECT-STATE.md`.

### 2026-10-02

* Fase 0 concluída: documentação arquitetural criada.
* Arquivos: `ARCHITECTURE.md`, `DATABASE.md`, `API.md`, `FINANCIAL-RULES.md`, `DASHBOARD.md`, `TEST-PLAN.md`, `PROJECT-STATE.md`.
* Testes: não aplicável (sem código).
* Resultado: base documental pronta para a Fase 1.

Formato:

### [DATA]

* alteração;
* arquivos modificados;
* testes;
* resultado.

---

# TESTES DA ÚLTIMA SESSÃO

**Comando:**
`cd backend && pytest` (PostgreSQL 16 local; banco de teste `marmitex_test` recriado automaticamente; variável `TEST_DATABASE_URL`).

**Resultado:**
Backend: 199 passed (`ruff`, `mypy`, `pip-audit` OK). Frontend: 19 passed (Vitest), typecheck/lint/build OK, `npm audit` 0, 4 passed (Playwright E2E). `mypy app` OK. Teste manual com `uvicorn` + `python -m app.cli create-admin`: login, cadastro, venda, custo e resumo de custos funcionando.

**Falhas:**
Nenhuma. Observação: build da imagem Docker não executado nesta sessão (ambiente sem daemon Docker); `docker compose config` validado.

---

# PRÓXIMA SESSÃO DO CLAUDE CODE

Ao iniciar:

1. Ler `MASTER-PROMPT.md`.
2. Ler este arquivo.
3. Identificar a fase atual.
4. Verificar o código existente.
5. Implementar somente a próxima etapa.
6. Executar testes.
7. Corrigir falhas.
8. Atualizar este arquivo.
9. Informar o resultado resumidamente.

---

# LOG DE SESSÕES

## Sessão 1 — 2026-10-02

**Status:** Concluída.

* Lidos `MASTER-PROMPT.md` e `PROJECT-STATE.md`.
* Executada somente a Fase 0 (Arquitetura), conforme a regra principal de execução.
* Criados os 6 documentos de arquitetura.
* Registradas decisões e riscos.
* Revisão com o negócio aplicada (empresas × clientes avulsos, lucro por empresa, papel único ADMIN, data escolhida pelo ADMIN).
* Correção do negócio aplicada (somente faturamento por empresa; datas de início/pagamento; custos acumulados; 1–2 notebooks).
* Fase 1 e Fase 2 implementadas e testadas (161 testes).
* Fase 3 implementada (histórico e dashboard na API).
* Fase 4 implementada (frontend + E2E).
* Recebimento/pagamento implementados; Fase 5 concluída (auditoria, backup, documentação).
* Próxima sessão: instalação no notebook e ajustes pedidos pelo uso real.

---

# CRITÉRIO DE CONCLUSÃO

O projeto estará concluído quando todas as fases estiverem concluídas e os critérios do `MASTER-PROMPT.md` forem atendidos.

Situação em 2026-10-02 (critérios do `MASTER-PROMPT.md` §26):

* [x] banco funcionando
* [x] migrations funcionando (`0001`–`0004`, sobe/desce testado)
* [x] autenticação funcionando
* [x] cadastros funcionando
* [x] vendas funcionando
* [x] custos funcionando
* [x] cálculos financeiros testados
* [x] histórico funcionando
* [x] dashboard funcionando
* [x] dashboard por empresa funcionando
* [x] auditoria implementada
* [x] testes passando (backend 199, frontend 19, E2E 4)
* [x] documentação atualizada
* [x] produção documentada (`INSTALL.md`, `OPERACAO.md`)
* [x] `PROJECT-STATE.md` atualizado
* [ ] build Docker validado no notebook (primeira instalação)

# FIM
