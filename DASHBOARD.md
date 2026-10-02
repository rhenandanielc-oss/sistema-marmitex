# DASHBOARD.md

# Dashboard Financeiro

Rotas do frontend: `/dashboard` (geral), `/dashboard?empresa=<id>` (detalhado por empresa) e `/dashboard?cliente=<id>` (detalhado por cliente avulso). Acesso: ADMIN.

Objetivo principal: saber, **no fim do mês, o lucro líquido geral** (custos são gerais do restaurante) e **o faturamento de cada empresa e cliente**, com gráficos. Por isso o período padrão é `month` (mês corrente) e há atalho para `last_month` (mês anterior fechado).

Todos os valores exibidos vêm da API (`API.md`, seção 3.10). O frontend **não** calcula indicadores financeiros: ele apenas formata (moeda pt-BR, datas `dd/mm/aaaa`, separador de milhar) e desenha os gráficos.

---

## 1. Filtros

| Filtro | Comportamento |
|---|---|
| Hoje | `period=today` |
| Semana | `period=week` (segunda-feira da semana corrente até hoje) |
| Mês | `period=month` (dia 1 do mês corrente até hoje) — **padrão** |
| Mês anterior | `period=last_month` (mês fechado) |
| Período personalizado | `period=custom&start_date=...&end_date=...`; seletor valida início ≤ fim e máximo de 366 dias |
| Empresa | abre o dashboard detalhado da empresa (inclui inativas, pois há histórico) |
| Cliente avulso | abre o dashboard detalhado do cliente |
| Tipo de comprador | no ranking de faturamento: Todos / Empresas / Clientes avulsos |

* O período efetivo retornado pela API (`period.start_date`/`end_date`) é exibido no topo: "Período: 01/09/2026 a 30/09/2026".
* Os filtros ficam na URL (query string) para permitir compartilhar/recarregar a visão.
* Trocar um filtro refaz as consultas (React Query, chave inclui os filtros).

---

## 2. Indicadores gerais (cartões KPI)

O dashboard geral considera **tudo**: vendas para empresas, vendas para clientes avulsos e todos os custos do restaurante.

| Cartão | Campo da API | Fórmula (`FINANCIAL-RULES.md`) |
|---|---|---|
| Receita Total (com divisão Empresas / Clientes avulsos) | `revenue`, `revenue_by_buyer_type` | F-01 |
| Custos Fixos | `fixed_costs` | F-04 |
| Custos Diários | `daily_costs` | F-03 |
| Custos Totais | `total_costs` | F-05 |
| **Lucro Líquido Geral** (destaque) + margem % | `net_profit`, `net_margin_percent` | F-06, F-11 — vermelho quando negativo |
| Quantidade de Marmitas (com divisão Empresas / Clientes) | `quantity`, `quantity_by_buyer_type` | F-02 |
| Custo Médio por Marmita | `average_cost_per_meal` | F-07 — "—" quando `null` |
| A receber | `pending_revenue` | F-19 — vendas pendentes de pagamento (informativo; não altera receita/lucro), com link para o Histórico filtrado |

Lucro negativo em um dia ou semana (ex.: dia em que o aluguel foi lançado) é esperado e exibido normalmente.

---

## 3. Faturamento por empresa e cliente (ranking)

Tabela + gráfico de barras com o **faturamento** de cada empresa e de cada cliente avulso no período (`GET /dashboard/by-buyer`). Não há lucro por comprador: os custos são gerais (`FINANCIAL-RULES.md` R-FAT-1).

| Coluna | Campo |
|---|---|
| Comprador (com selo "Empresa" / "Cliente") | `buyer` |
| Faturamento | `revenue` |
| Marmitas | `quantity` |
| Vendas | `sales_count` |
| Ticket médio | `average_ticket` |
| Preço médio por marmita | `average_price_per_meal` |
| % do faturamento | `revenue_share_percent` |
| A receber | `pending_revenue` |

* Linhas de subtotal "Empresas" e "Clientes avulsos" (`subtotals`) e linha de total igual à Receita Total.
* Clicar em uma linha abre o dashboard detalhado do comprador.

---

## 4. Gráficos

| Gráfico | Tipo | Fonte |
|---|---|---|
| Receita diária | barras | `/dashboard/daily` → `revenue` |
| Quantidade diária de marmitas | barras | `/dashboard/daily` → `quantity` |
| Receita por empresa | barras horizontais (ordenadas desc.) + % de participação | `/dashboard/by-buyer` |
| Acumulado no período | três linhas no mesmo eixo (R$): receita, custos e lucro acumulados | `/dashboard/daily` → `cumulative_revenue`, `cumulative_costs`, `cumulative_net_profit` (calculados no backend) |
| Custos diários | barras empilhadas (diário × fixo) | `/dashboard/daily` → `daily_costs`, `fixed_costs` |
| Lucro diário | barras (verde ≥ 0, vermelho < 0) | `/dashboard/daily` → `net_profit` |
| Histórico de vendas por empresa | barras empilhadas por dia: 6 maiores empresas + "Outras empresas" + "Clientes avulsos" (máximo de 8 cores) | `/dashboard/sales-by-company-daily?top=6` |

Regras de apresentação:

* Eixo X com todos os dias do período (dias sem movimento = 0, nunca omitidos).
* Tooltip com valor formatado em R$ e data `dd/mm/aaaa`.
* Períodos longos (> 62 dias): rótulos do eixo X espaçados automaticamente.
* Estado vazio: "Nenhum lançamento no período" em vez de gráfico em branco.
* Cores fixas (paleta validada para daltonismo — `ARCHITECTURE.md` D-12): receita e quantidade azul, custos diários laranja, custos fixos violeta, lucro acumulado verde-água; lucro diário azul quando ≥ 0 e vermelho quando < 0.
* Todo gráfico tem **"Ver tabela"** com os mesmos valores (acessibilidade e conferência).
* Nunca dois eixos Y no mesmo gráfico; quantidade e receita ficam em gráficos separados.

---

## 5. Dashboard detalhado por empresa (e por cliente avulso)

Acesso: seletor "Ver empresa"/"Ver cliente" ou clique no ranking/gráfico. Fonte: `GET /dashboard/companies/{id}` ou `/dashboard/customers/{id}` com o período escolhido. Mostra apenas **faturamento**.

| Bloco | Campo |
|---|---|
| Dados do cadastro | ciclo de faturamento, data de início, data de pagamento |
| Faturamento | `revenue` |
| Quantidade de marmitas | `quantity` |
| Ticket médio (receita ÷ nº de vendas) | `average_ticket` |
| Preço médio por marmita | `average_price_per_meal` |
| Evolução vs. período anterior | `comparison.revenue_change_percent` (seta ↑/↓; "—" se `null`) |
| Histórico diário | gráfico de faturamento e quantidade por dia (`daily`) |
| Vendas | tabela das vendas recentes (`recent_sales`) com link "ver todas no Histórico" (abre `/historico?empresa=<id>&inicio=..&fim=..`) |
| Fechamento | total do período para cobrança — atalho para o Histórico filtrado pela quinzena/mês |

Empresa ou cliente inativo: exibido com o selo "Inativo"; dados históricos continuam visíveis.

---

## 6. Tela de custos (lançamentos)

Embora a análise principal seja o fechamento do mês, a tela `/lancamentos/custos` exibe sempre no topo os **totais do mês corrente até agora** (custos diários, fixos e totais — `GET /costs/summary`), que aumentam a cada novo custo registrado. A tabela de custos mostra a coluna **Acumulado** (`running_total`), somando lançamento a lançamento (`FINANCIAL-RULES.md` R-CUS-7/R-CUS-8).

---

## 7. Performance

* Consultas agregadas no PostgreSQL com índices por data (`DATABASE.md`).
* Uma requisição por bloco (summary, daily, by-buyer) em paralelo pelo React Query.
* Uso previsto: 1 a 2 notebooks. Meta: resposta < 500 ms com 2 anos de dados (~20 mil vendas) em um notebook comum.
* `staleTime` de 30 s no frontend; invalidação após qualquer lançamento.
