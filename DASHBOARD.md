# DASHBOARD.md

# Dashboard Financeiro

Rota do frontend: `/dashboard` (geral) e `/dashboard?empresa=<id>` (detalhado por empresa).
Permissão: `dashboard:read` (ADMIN e GERENTE).

Todos os valores exibidos vêm da API (`API.md`, seção 3.10). O frontend **não** calcula indicadores financeiros: ele apenas formata (moeda pt-BR, datas `dd/mm/aaaa`, separador de milhar) e desenha os gráficos.

---

## 1. Filtros

| Filtro | Comportamento |
|---|---|
| Hoje | `period=today` |
| Semana | `period=week` (segunda-feira da semana corrente até hoje) |
| Mês | `period=month` (dia 1 do mês corrente até hoje) — **padrão** |
| Período personalizado | `period=custom&start_date=...&end_date=...`; seletor de datas valida início ≤ fim e máximo de 366 dias |
| Empresa | seleção múltipla de empresas (inclui inativas, pois há histórico); vazio = todas |

* O período efetivo retornado pela API (`period.start_date`/`end_date`) é exibido no topo: "Período: 01/09/2026 a 30/09/2026".
* Os filtros ficam na URL (query string) para permitir compartilhar/recarregar a visão.
* Trocar um filtro refaz as consultas (React Query, chave inclui os filtros).

---

## 2. Indicadores (cartões KPI)

| Cartão | Campo da API | Fórmula (`FINANCIAL-RULES.md`) |
|---|---|---|
| Receita Total | `revenue` | F-01 |
| Custos Fixos | `fixed_costs` | F-04 |
| Custos Diários | `daily_costs` | F-03 |
| Custos Totais | `total_costs` | F-05 |
| Lucro Líquido | `net_profit` | F-06 — vermelho quando negativo |
| Quantidade de Marmitas | `quantity` | F-02 |
| Custo Médio por Marmita | `average_cost_per_meal` | F-07 — "—" quando `null` |

Com filtro de empresa:

* Receita e Quantidade referem-se às empresas selecionadas.
* Custos Fixos/Diários/Totais e Custo Médio mostram os **valores globais** com o selo "global".
* O cartão Lucro Líquido é substituído por **"Lucro estimado (rateio por marmita)"** (`estimated_profit`), acompanhado de "Custo alocado" (`allocated_costs`) e um ícone de ajuda explicando o rateio (R-EMP-3/R-EMP-4).
* Se `allocation_available = false`, exibe "—" e "sem marmitas no período para ratear".

---

## 3. Gráficos

| Gráfico | Tipo | Fonte |
|---|---|---|
| Receita diária | barras | `/dashboard/daily` → `revenue` |
| Quantidade diária de marmitas | barras | `/dashboard/daily` → `quantity` |
| Receita por empresa | barras horizontais (ordenadas desc.) + % de participação | `/dashboard/revenue-by-company` |
| Receita total (acumulada no período) | linha acumulada | `/dashboard/daily` → `revenue`, acumulada **apenas para desenho** (a soma final é igual a `summary.revenue`, garantido pela R-IND-5) |
| Custos diários | barras empilhadas (diário × fixo) | `/dashboard/daily` → `daily_costs`, `fixed_costs` |
| Lucro diário | barras (verde ≥ 0, vermelho < 0) | `/dashboard/daily` → `profit` |
| Histórico de vendas por empresa | linhas, uma por empresa (top 10 + "Outras") | `/dashboard/sales-by-company-daily` |

Regras de apresentação:

* Eixo X com todos os dias do período (dias sem movimento = 0, nunca omitidos).
* Tooltip com valor formatado em R$ e data `dd/mm/aaaa`.
* Períodos longos (> 62 dias): rótulos do eixo X espaçados automaticamente.
* Estado vazio: "Nenhum lançamento no período" em vez de gráfico em branco.
* Cores consistentes: receita (azul), custos (laranja/âmbar), lucro (verde/vermelho), quantidade (cinza-azulado).
* Com filtro de empresa, o gráfico de lucro diário exibe "Lucro estimado (rateio diário)" e a nota da R-EMP-6.

---

## 4. Dashboard detalhado por empresa

Acesso: selecionar uma empresa no seletor "Ver empresa" ou clicar em uma barra do gráfico "Receita por empresa". Fonte: `GET /dashboard/companies/{id}` com o período escolhido.

Conteúdo:

| Bloco | Campo |
|---|---|
| Receita | `revenue` |
| Quantidade de marmitas | `quantity` |
| Ticket médio (receita ÷ nº de vendas) | `average_ticket` |
| Preço médio por marmita | `average_price_per_meal` |
| Custo alocado / Lucro estimado | `allocated_costs`, `estimated_profit` |
| Evolução vs. período anterior | `comparison.revenue_change_percent` (seta ↑/↓; "—" se `null`) |
| Histórico diário | gráfico de receita e quantidade por dia (`daily`) |
| Clientes | tabela: cliente, receita, quantidade, nº de vendas (`customers`), ordenável no cliente |
| Vendas | tabela das vendas recentes (`recent_sales`) com link "ver todas no Histórico" (abre `/historico?empresa=<id>&inicio=..&fim=..`) |

Empresa inativa: exibida com o selo "Inativa"; dados históricos continuam visíveis.

---

## 5. Performance

* Consultas agregadas no PostgreSQL com índices por data (`DATABASE.md`).
* Uma requisição por bloco (summary, daily, by-company) em paralelo pelo React Query.
* Meta: resposta < 500 ms para 1 ano de dados com ~100 mil vendas (verificado na Fase 5).
* `staleTime` de 30 s no frontend; invalidação após qualquer lançamento.
