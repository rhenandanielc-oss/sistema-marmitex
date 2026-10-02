# PROJECT-STATE.md

# Sistema de Gestão de Vendas B2B de Marmitex e Controle Financeiro

Este arquivo representa o estado atual do projeto.

O Claude Code deve atualizá-lo ao final de cada etapa significativa.

---

# STATUS GERAL

**Status:** EM ANDAMENTO

**Fase atual:** Fase 0 — Arquitetura (CONCLUÍDA). Próxima: Fase 1 — Banco, autenticação e cadastros.

**Última atualização:** 2026-10-02 (Sessão 1).

**Último commit:** `docs: revise phase 0 with business decisions` (branch `claude/sistema-marmitex-b2b-j8apnv`).

**Próxima ação:** Iniciar a Fase 1: estrutura `backend/` (FastAPI + SQLAlchemy + Alembic), `docker-compose.yml` com PostgreSQL 16, `.env.example`, migrations `0001_initial_schema` e `0002_seed_cost_categories` conforme `DATABASE.md`, usuários/autenticação (papel único ADMIN) conforme `API.md` seções 2 e 3.2–3.3, e CRUD de empresas, clientes avulsos e categorias (seções 3.4–3.6) com testes de integração.

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
* [ ] papel único ADMIN (`require_admin`)
* [ ] auditoria

### Cadastros

#### Empresas (empreiteiras)

* [ ] criar
* [ ] editar
* [ ] ativar
* [ ] desativar
* [ ] pesquisar
* [ ] filtrar

#### Clientes avulsos (independentes)

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

* [ ] comprador único (empresa OU cliente avulso)
* [ ] preço unitário
* [ ] quantidade
* [ ] data escolhida pelo ADMIN (padrão hoje, nunca futura)
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
* [ ] lucro líquido geral (empresas + clientes + todos os custos)
* [ ] faturamento por empresa/cliente
* [ ] custos acumulados

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
* [ ] Σ faturamento por comprador = receita
* [ ] último acumulado de custos = custos totais

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
* [ ] faturamento por comprador (`/dashboard/by-buyer`)
* [ ] quantidade diária
* [ ] custos diários
* [ ] lucro diário
* [ ] histórico por empresa
* [ ] dashboard por cliente avulso

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

* **disponibilidade:** o notebook servidor precisa estar ligado para o segundo notebook acessar; backup local + cópia externa obrigatórios (Fase 5).
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
* Revisão com o negócio aplicada (empresas × clientes avulsos, lucro por empresa, papel único ADMIN, data escolhida pelo ADMIN).
* Próxima sessão: Fase 1.

---

# CRITÉRIO DE CONCLUSÃO

O projeto estará concluído quando todas as fases estiverem concluídas e os critérios do `MASTER-PROMPT.md` forem atendidos.

# FIM
