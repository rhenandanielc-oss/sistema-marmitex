# DASHBOARD.md

# Dashboard Financeiro

Rotas do frontend: `/dashboard` (geral), `/dashboard?empresa=<id>` (detalhado por empresa) e `/dashboard?cliente=<id>` (detalhado por cliente avulso). Acesso: ADMIN.

Objetivo principal: saber, **no fim do mês, o lucro líquido geral e o lucro líquido de cada empresa**, com gráficos. Por isso o período padrão é `month` (mês corrente) e há atalho para `last_month` (mês anterior fechado).

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
| Tipo de comprador | no ranking de lucro: Todos / Empresas / Clientes avulsos |

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

Lucro negativo em um dia ou semana (ex.: dia em que o aluguel foi lançado) é esperado e exibido normalmente.

---

## 3. Lucro líquido por empresa (ranking)

Tabela + gráfico de barras com o resultado de **cada empresa** e de cada cliente avulso no período (`GET /dashboard/by-buyer`):

| Coluna | Campo |
|---|---|
| Comprador (com selo "Empresa" / "Cliente") | `buyer` |
| Receita | `revenue` |
| Marmitas | `quantity` |
| % da receita | `revenue_share_percent` |
| Custo alocado (rateio por marmita) | `allocated_costs` |
| **Lucro líquido** | `net_profit` |
| Margem % | `net_margin_percent` |

* Linhas de subtotal "Empresas" e "Clientes avulsos" (`subtotals`) e linha de total igual ao Lucro Líquido Geral.
* Ícone de ajuda explicando o rateio: "Os custos do restaurante são divididos pela quantidade de marmitas de cada comprador" (R-RAT-2).
* Se `allocation_available = false`: aviso "Sem marmitas no período — custos não alocados: R$ X".
* Clicar em uma linha abre o dashboard detalhado do comprador.

---

## 4. Gráficos

| Gráfico | Tipo | Fonte |
|---|---|---|
| Receita diária | barras | `/dashboard/daily` → `revenue` |
| Quantidade diária de marmitas | barras | `/dashboard/daily` → `quantity` |
| Receita por empresa | barras horizontais (ordenadas desc.) + % de participação | `/dashboard/by-buyer` |
| Lucro líquido por empresa | barras horizontais (verde ≥ 0, vermelho < 0) | `/dashboard/by-buyer` |
| Receita total (acumulada no período) | linha acumulada | `/dashboard/daily` → `revenue`, acumulada **apenas para desenho** (a soma final é igual a `summary.revenue`, garantido pela R-IND-5) |
| Lucro acumulado no mês | linha acumulada (mostra a evolução até o lucro final do mês) | `/dashboard/daily` → `net_profit`, acumulado apenas para desenho |
| Custos diários | barras empilhadas (diário × fixo) | `/dashboard/daily` → `daily_costs`, `fixed_costs` |
| Lucro diário | barras (verde ≥ 0, vermelho < 0) | `/dashboard/daily` → `net_profit` |
| Histórico de vendas por empresa | linhas, uma por empresa (top 10 + "Outras empresas" + "Clientes avulsos") | `/dashboard/sales-by-company-daily` |

Regras de apresentação:

* Eixo X com todos os dias do período (dias sem movimento = 0, nunca omitidos).
* Tooltip com valor formatado em R$ e data `dd/mm/aaaa`.
* Períodos longos (> 62 dias): rótulos do eixo X espaçados automaticamente.
* Estado vazio: "Nenhum lançamento no período" em vez de gráfico em branco.
* Cores consistentes: receita (azul), custos (laranja/âmbar), lucro (verde/vermelho), quantidade (cinza-azulado).

---

## 5. Dashboard detalhado por empresa (e por cliente avulso)

Acesso: seletor "Ver empresa"/"Ver cliente" ou clique no ranking/gráfico. Fonte: `GET /dashboard/companies/{id}` ou `/dashboard/customers/{id}` com o período escolhido.

| Bloco | Campo |
|---|---|
| Receita | `revenue` |
| Quantidade de marmitas | `quantity` |
| Ticket médio (receita ÷ nº de vendas) | `average_ticket` |
| Preço médio por marmita | `average_price_per_meal` |
| Custo alocado | `allocated_costs` |
| **Lucro líquido da empresa** + margem % | `net_profit`, `net_margin_percent` |
| Evolução vs. período anterior | `comparison` (receita, lucro, seta ↑/↓; "—" se `null`) |
| Histórico diário | gráfico de receita, quantidade e lucro por dia (`daily`), com a nota da R-RAT-9 |
| Vendas | tabela das vendas recentes (`recent_sales`) com link "ver todas no Histórico" (abre `/historico?empresa=<id>&inicio=..&fim=..`) |
| Fechamento | total do período para cobrança, conforme o ciclo (`billing_cycle`) — atalho para o Histórico filtrado pela quinzena/mês |

Empresa ou cliente inativo: exibido com o selo "Inativo"; dados históricos continuam visíveis.

---

## 6. Performance

* Consultas agregadas no PostgreSQL com índices por data (`DATABASE.md`).
* Uma requisição por bloco (summary, daily, by-buyer) em paralelo pelo React Query.
* Meta: resposta < 500 ms para 1 ano de dados com ~100 mil vendas (verificado na Fase 5).
* `staleTime` de 30 s no frontend; invalidação após qualquer lançamento.
