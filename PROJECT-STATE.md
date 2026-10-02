# PROJECT-STATE.md

# Sistema de Gestão de Vendas B2B de Marmitex e Controle Financeiro

Este arquivo representa o estado atual do projeto.

O Claude Code deve atualizá-lo ao final de cada etapa significativa.

---

# STATUS GERAL

**Status:** EM ANDAMENTO

**Fase atual:** Fase 0 — Arquitetura (CONCLUÍDA). Próxima: Fase 1 — Banco, autenticação e cadastros.

**Última atualização:** 2026-10-02 (Sessão 1).

**Último commit:** `docs: phase 0 architecture documentation` (branch `claude/sistema-marmitex-b2b-j8apnv`).

**Próxima ação:** Iniciar a Fase 1: estrutura `backend/` (FastAPI + SQLAlchemy + Alembic), `docker-compose.yml` com PostgreSQL 16, `.env.example`, migrations `0001_initial_schema` e `0002_seed_cost_categories` conforme `DATABASE.md`, usuários/autenticação/permissões conforme `API.md` seções 2 e 3.2–3.3, e CRUD de empresas, clientes e categorias (seções 3.4–3.6) com testes de integração.

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

**Status:** PENDENTE

### Banco

* [ ] PostgreSQL
* [ ] Docker
* [ ] migrations
* [ ] modelos
* [ ] relacionamentos
* [ ] constraints
* [ ] índices

### Autenticação

* [ ] usuários
* [ ] login
* [ ] logout
* [ ] sessões/tokens
* [ ] papéis
* [ ] permissões
* [ ] auditoria

### Cadastros

#### Empresas

* [ ] criar
* [ ] editar
* [ ] ativar
* [ ] desativar
* [ ] pesquisar
* [ ] filtrar

#### Clientes

* [ ] criar
* [ ] editar
* [ ] ativar
* [ ] desativar
* [ ] pesquisar
* [ ] filtrar

#### Categorias

* [ ] criar
* [ ] editar
* [ ] ativar
* [ ] desativar
* [ ] pesquisar

### Testes

Pendente.

---

# FASE 2 — VENDAS, CUSTOS E MOTOR FINANCEIRO

**Status:** PENDENTE

### Vendas

* [ ] empresa
* [ ] cliente
* [ ] preço unitário
* [ ] quantidade
* [ ] data do servidor
* [ ] subtotal
* [ ] validações
* [ ] edição
* [ ] auditoria

### Custos

* [ ] valor
* [ ] categoria
* [ ] tipo
* [ ] data
* [ ] validações
* [ ] auditoria

### Tipos de custo

* [ ] `CUSTO_DIARIO`
* [ ] `CUSTO_FIXO`

### Categorias

#### Diários

* [ ] Ingredientes
* [ ] Embalagens
* [ ] Entregas
* [ ] Equipamentos
* [ ] Gasolina

#### Fixos

* [ ] Salários
* [ ] Aluguel
* [ ] Água
* [ ] Energia elétrica
* [ ] Gás

---

# MOTOR FINANCEIRO

### Regras

* [ ] receita
* [ ] custos totais
* [ ] lucro líquido
* [ ] custo médio por marmita
* [ ] divisão por zero
* [ ] período inclusivo
* [ ] filtro por empresa

### Fórmulas

`RECEITA = soma dos subtotais`

`CUSTOS_TOTAIS = custos fixos + custos diários`

`LUCRO_LIQUIDO = receita - custos totais`

`CUSTO_MEDIO_POR_MARMITA = custos totais / quantidade de marmitas`

### Testes

* [ ] dia
* [ ] semana
* [ ] mês
* [ ] período personalizado
* [ ] empresa
* [ ] várias empresas
* [ ] sem vendas
* [ ] sem custos
* [ ] sem vendas e sem custos
* [ ] divisão por zero
* [ ] somente custos fixos
* [ ] somente custos diários
* [ ] vendas sem custos
* [ ] custos sem vendas

---

# FASE 3 — API

**Status:** PENDENTE

### Endpoints

* [ ] autenticação
* [ ] empresas
* [ ] clientes
* [ ] categorias
* [ ] vendas
* [ ] custos
* [ ] histórico
* [ ] dashboard

### Dashboard

* [ ] resumo financeiro
* [ ] vendas diárias
* [ ] vendas por empresa
* [ ] quantidade diária
* [ ] custos diários
* [ ] lucro diário
* [ ] histórico por empresa

### Recursos

* [ ] filtros
* [ ] paginação
* [ ] ordenação
* [ ] tratamento de erros
* [ ] autorização
* [ ] OpenAPI
* [ ] testes de integração

---

# FASE 4 — FRONTEND

**Status:** PENDENTE

### Rotas

* [ ] `/login`
* [ ] `/cadastros/empresas`
* [ ] `/cadastros/clientes`
* [ ] `/cadastros/categorias`
* [ ] `/lancamentos/vendas`
* [ ] `/lancamentos/custos`
* [ ] `/historico`
* [ ] `/dashboard`

### Funcionalidades

* [ ] login
* [ ] empresas
* [ ] clientes
* [ ] categorias
* [ ] vendas
* [ ] custos
* [ ] histórico
* [ ] dashboard
* [ ] dashboard por empresa

---

# HISTÓRICO

### Filtros

* [ ] empresa
* [ ] cliente
* [ ] data inicial
* [ ] data final
* [ ] tipo

### Vendas

* [ ] data
* [ ] empresa
* [ ] cliente
* [ ] quantidade
* [ ] preço
* [ ] subtotal

### Custos

* [ ] data
* [ ] categoria
* [ ] tipo
* [ ] valor

### Recursos

* [ ] paginação
* [ ] ordenação
* [ ] filtros

---

# DASHBOARD

### Indicadores

* [ ] Receita Total
* [ ] Custos Fixos
* [ ] Custos Diários
* [ ] Custos Totais
* [ ] Lucro Líquido
* [ ] Quantidade de Marmitas
* [ ] Custo Médio por Marmita

### Gráficos

* [ ] receita diária
* [ ] quantidade diária
* [ ] receita por empresa
* [ ] receita total
* [ ] custos diários
* [ ] lucro diário
* [ ] histórico de vendas por empresa

### Filtros

* [ ] hoje
* [ ] semana
* [ ] mês
* [ ] período personalizado
* [ ] empresa

---

# DASHBOARD POR EMPRESA

**Status:** PENDENTE

* [ ] selecionar empresa
* [ ] receita
* [ ] quantidade
* [ ] ticket médio
* [ ] histórico diário
* [ ] clientes
* [ ] vendas
* [ ] evolução do período

---

# FASE 5 — AUDITORIA E PRODUÇÃO

**Status:** PENDENTE

### Auditoria

* [ ] banco
* [ ] API
* [ ] frontend
* [ ] autenticação
* [ ] autorização
* [ ] filtros
* [ ] datas
* [ ] valores monetários
* [ ] arredondamento
* [ ] concorrência
* [ ] auditoria
* [ ] performance

### Produção

* [ ] Dockerfiles
* [ ] configuração de produção
* [ ] migrations
* [ ] `.env.example`
* [ ] health checks
* [ ] logs
* [ ] backup
* [ ] documentação de instalação
* [ ] documentação de deploy

---

# DECISÕES TÉCNICAS

As decisões arquiteturais completas estão em `ARCHITECTURE.md` seção 5. Abaixo, as decisões que afetam regras de negócio.

### 2026-10-02 — Cliente pertence a uma empresa

**Problema:** o MASTER-PROMPT cita empresas e clientes sem definir a relação.
**Opções:** (a) clientes independentes; (b) cliente vinculado a uma empresa.
**Decisão:** (b) — `customers.company_id` obrigatório; a venda exige que o cliente pertença à empresa (FK composta).
**Motivo:** modelo B2B: a empresa contrata, o cliente é o colaborador/setor que recebe.
**Impacto:** seletor de cliente no lançamento é filtrado pela empresa.

### 2026-10-02 — Custos com filtro de empresa (rateio por marmita)

**Problema:** custos não pertencem a empresas, mas o dashboard aceita filtro de empresa.
**Opções:** (a) ignorar custos no filtro; (b) mostrar custos globais e lucro global; (c) ratear custos proporcionalmente à quantidade de marmitas; (d) ratear pela receita.
**Decisão:** (c), exibindo também os custos globais. Lucro Líquido oficial continua sendo global; por empresa exibe-se "Lucro estimado (rateio por marmita)".
**Motivo:** coerente com o indicador "custo médio por marmita"; evita mostrar lucro enganoso.
**Impacto:** regras R-EMP-1 a R-EMP-6 e fórmulas F-11 a F-13 em `FINANCIAL-RULES.md`. **Pendente de validação pelo negócio.**

### 2026-10-02 — Reconhecimento de custos na data do lançamento

**Problema:** custos fixos mensais (ex.: aluguel) poderiam ser rateados por dia.
**Decisão:** custo reconhecido integralmente em `cost_date`, sem rateio entre dias (R-CUS-5).
**Motivo:** fórmula do MASTER-PROMPT (`CUSTOS_TOTAIS = fixos + diários` no período) e simplicidade.
**Impacto:** visão diária/semanal pode mostrar lucro negativo no dia do lançamento de um custo fixo. **Pendente de validação pelo negócio.**

### 2026-10-02 — Datas de lançamento

**Decisão:** venda sempre com data do servidor (corrigível só por ADMIN, com auditoria); custo usa hoje por padrão, aceita data passada (GERENTE/ADMIN), nunca futura. Fuso `America/Sao_Paulo` configurável.

### 2026-10-02 — Períodos pré-definidos

**Decisão:** semana = segunda-feira corrente até hoje; mês = dia 1 até hoje; resolvidos no backend.

### 2026-10-02 — Papéis

**Decisão:** ADMIN, GERENTE, OPERADOR com matriz de permissões em `API.md` seção 2.

Formato:

### [DATA] — [DECISÃO]

**Problema:**
...

**Opções:**
...

**Decisão:**
...

**Motivo:**
...

**Impacto:**
...

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

* [ ] autenticação
* [ ] autorização
* [ ] proteção de endpoints
* [ ] hash de senha
* [ ] expiração de sessão
* [ ] auditoria
* [ ] `.env`
* [ ] `.env.example`
* [ ] nenhum secret no Git

---

# PROBLEMAS CONHECIDOS

Nenhum problema registrado.

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

* **cálculos:** decisões de rateio (R-EMP-3) e reconhecimento de custos (R-CUS-5) ainda não validadas pelo negócio — mudanças exigem atualizar `FINANCIAL-RULES.md` e os testes FIN-*.
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
Nenhum (Fase 0 é somente documentação).

**Resultado:**
Não aplicável.

**Falhas:**
Nenhuma.

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
* Próxima sessão: Fase 1.

---

# CRITÉRIO DE CONCLUSÃO

O projeto estará concluído quando todas as fases estiverem concluídas e os critérios do `MASTER-PROMPT.md` forem atendidos.

# FIM
