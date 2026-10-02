# API.md

# Contrato da API — REST/JSON

* Base: `/api/v1`
* Documentação OpenAPI gerada pelo FastAPI: `/api/docs` (Swagger UI), `/api/redoc`, `/api/openapi.json`.
* Formato: JSON UTF-8. Datas `YYYY-MM-DD`; carimbos de data/hora ISO 8601 em UTC; dinheiro como string decimal (`"18.50"`).
* Autenticação: header `Authorization: Bearer <token>` em todas as rotas, exceto `POST /auth/login` e `/health/*`.

---

## 1. Convenções

### 1.1 Paginação

Parâmetros: `page` (≥ 1, padrão 1) e `page_size` (1–100, padrão 20).

```json
{
  "items": [ ... ],
  "total": 134,
  "page": 2,
  "page_size": 20,
  "pages": 7
}
```

### 1.2 Ordenação

Parâmetros: `sort` (campo permitido na rota) e `order` (`asc` | `desc`). Campo fora da lista permitida → `422`. Ordenação sempre recebe `id` como desempate para paginação estável.

### 1.3 Filtros comuns

| Parâmetro | Uso |
|---|---|
| `q` | busca textual (case-insensitive, `ILIKE`) em nome/nome fantasia/CNPJ/telefone/local conforme a rota |
| `active` | `true` / `false` / omitido (todos) |
| `start_date`, `end_date` | intervalo fechado (ver `FINANCIAL-RULES.md`, R-PER-1) |
| `buyer_type` | `COMPANY` (empresas) / `CUSTOMER` (clientes avulsos) / omitido (todos) |
| `company_id`, `customer_id` | filtro por comprador; podem ser repetidos (`company_id=1&company_id=2`) onde indicado |

### 1.4 Erros padronizados

Todas as respostas de erro seguem o formato:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados inválidos.",
    "details": [
      { "field": "quantity", "message": "Deve ser maior que zero." }
    ],
    "request_id": "c0a8012e-..."
  }
}
```

| HTTP | `code` | Quando |
|---|---|---|
| 400 | `BAD_REQUEST` | requisição malformada |
| 401 | `UNAUTHENTICATED` | sem token, token inválido/expirado, sessão revogada |
| 401 | `INVALID_CREDENTIALS` | login inválido (mensagem genérica) |
| 403 | `FORBIDDEN` | usuário sem o papel exigido |
| 404 | `NOT_FOUND` | recurso inexistente (ou excluído logicamente) |
| 409 | `CONFLICT` | duplicidade (nome, CNPJ, e-mail) ou regra de integridade |
| 409 | `VERSION_CONFLICT` | `version` divergente (edição concorrente) |
| 422 | `VALIDATION_ERROR` | validação de campos e regras de negócio (ex.: empresa inativa, data futura) |
| 429 | `TOO_MANY_REQUESTS` | limite de tentativas de login |
| 500 | `INTERNAL_ERROR` | erro inesperado (sem detalhes internos na resposta) |

Mensagens em português.

### 1.5 Concorrência

`PATCH` de entidades editáveis exige o campo `version` no corpo. Se a versão no banco for diferente → `409 VERSION_CONFLICT`. A resposta de sucesso devolve a nova `version`.

---

## 2. Autorização

Papel único: **`ADMIN`**. Todo usuário ativo e autenticado é ADMIN e tem acesso a todas as rotas protegidas (cadastros, lançamentos com escolha de data, edição/exclusão, histórico, dashboard, usuários e auditoria).

* Implementação: dependência `require_admin` (`backend/app/core/permissions.py`) em todos os routers protegidos. Ela verifica sessão válida, usuário ativo e `role = 'ADMIN'`.
* O `403 FORBIDDEN` existe para quando outros papéis forem criados no futuro; hoje, na prática, a resposta para acesso indevido é `401`.
* `GET /auth/me` retorna `role` para o frontend.

---

## 3. Endpoints

### 3.1 Saúde

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health/live` | `200 {"status":"ok"}` se o processo responde |
| GET | `/health/ready` | `200` se o banco responde a `SELECT 1`; senão `503` |

### 3.2 Autenticação

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/login` | `{email, password}` → `{access_token, token_type:"bearer", expires_at, user}` |
| POST | `/auth/logout` | revoga a sessão atual → `204` |
| GET | `/auth/me` | usuário atual (`id`, `name`, `email`, `role`) |
| POST | `/auth/change-password` | `{current_password, new_password}` → `204`; revoga as outras sessões |

Login: auditado (`LOGIN_SUCCESS` / `LOGIN_FAILED`), limitado a 5 falhas por e-mail+IP em 15 min (`429`).

### 3.3 Usuários (ADMIN)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/users` | lista paginada; filtros `q`, `active`; ordenação `name`, `email`, `created_at` |
| POST | `/users` | `{name, email, password}` (papel sempre `ADMIN`) |
| GET | `/users/{id}` | detalhe |
| PATCH | `/users/{id}` | `{name?, email?, version}` |
| POST | `/users/{id}/activate` · `/users/{id}/deactivate` | desativar revoga sessões; o usuário não pode desativar a si mesmo nem o último ADMIN ativo |
| POST | `/users/{id}/reset-password` | `{new_password}` |

### 3.4 Empresas (empreiteiras)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/companies` | paginada; filtros `q` (nome, nome fantasia, CNPJ), `active`, `billing_cycle`; ordenação `name`, `created_at` |
| POST | `/companies` | `{name, trade_name?, cnpj?, contact_name?, phone?, email?, billing_cycle (QUINZENAL\|MENSAL), start_date?, payment_date?, notes?}` → `201` |
| GET | `/companies/{id}` | detalhe |
| PATCH | `/companies/{id}` | campos parciais + `version` |
| POST | `/companies/{id}/activate` · `/companies/{id}/deactivate` | `{version}` → entidade atualizada |

Validações: nome obrigatório (2–150), único (case-insensitive); CNPJ com 14 dígitos e dígitos verificadores válidos, único; e-mail válido; `start_date` (data de início do fornecimento) e `payment_date` (data de pagamento combinada) opcionais, informadas pelo ADMIN.

### 3.5 Clientes avulsos

Independentes das empresas.

| Método | Rota | Descrição |
|---|---|---|
| GET | `/customers` | paginada; filtros `q` (nome, telefone, local), `active`, `billing_cycle`; ordenação `name`, `created_at` |
| POST | `/customers` | `{name, phone?, document?, location?, billing_cycle (A_VISTA\|SEMANAL\|QUINZENAL\|MENSAL), start_date?, payment_date?, notes?}` → `201` |
| GET | `/customers/{id}` | detalhe |
| PATCH | `/customers/{id}` | campos parciais + `version` |
| POST | `/customers/{id}/activate` · `/customers/{id}/deactivate` | `{version}` |

Validações: nome obrigatório (2–150); CPF com dígitos verificadores válidos e único, se informado; `start_date` e `payment_date` opcionais.

### 3.6 Categorias de custo (tipos de custo)

Aba onde o ADMIN cadastra novos tipos de custo (ex.: "Embalagens", "Ingredientes").

| Método | Rota | Descrição |
|---|---|---|
| GET | `/cost-categories` | paginada; filtros `q`, `active`, `cost_type`; ordenação `name`, `cost_type` |
| POST | `/cost-categories` | `{name, cost_type}` |
| PATCH | `/cost-categories/{id}` | `{name?, cost_type?, version}` — alterar `cost_type` com custos existentes → `409` |
| POST | `/cost-categories/{id}/activate` · `/cost-categories/{id}/deactivate` | `{version}` |

### 3.7 Vendas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/sales` | paginada; filtros `start_date`, `end_date`, `buyer_type`, `company_id`, `customer_id`; ordenação `sale_date`, `subtotal`, `quantity`, `buyer` (padrão `sale_date desc`) |
| POST | `/sales` | `{buyer_type, company_id?, customer_id?, unit_price, quantity, sale_date?, notes?}` → `201` |
| GET | `/sales/{id}` | detalhe |
| PATCH | `/sales/{id}` | `{buyer_type?, company_id?, customer_id?, unit_price?, quantity?, sale_date?, notes?, version}` |
| DELETE | `/sales/{id}` | exclusão lógica → `204` |

Regras (`FINANCIAL-RULES.md` seção 3):

* `buyer_type = COMPANY` exige `company_id` e proíbe `customer_id`; `CUSTOMER` o inverso → senão `422`.
* `sale_date` opcional: omitida = hoje do servidor; futura → `422`.
* `subtotal` enviado → `422` (é sempre calculado pelo servidor).

Resposta `SaleRead`:

```json
{
  "id": 10,
  "sale_date": "2026-09-01",
  "buyer_type": "COMPANY",
  "buyer": { "type": "COMPANY", "id": 1, "name": "Empresa A" },
  "unit_price": "18.50",
  "quantity": 40,
  "subtotal": "740.00",
  "notes": null,
  "version": 1,
  "created_at": "2026-09-01T14:03:11Z",
  "created_by": { "id": 2, "name": "Maria" }
}
```

### 3.8 Custos

| Método | Rota | Descrição |
|---|---|---|
| GET | `/costs` | paginada; filtros `start_date`, `end_date`, `cost_type`, `category_id`; ordenação `cost_date`, `amount`, `category` (padrão `cost_date desc`). Cada item traz `running_total` (acumulado, R-CUS-7) e a resposta traz `totals` |
| GET | `/costs/summary` | totais do período (padrão: mês corrente até hoje): `{period, daily_costs, fixed_costs, total_costs, count}` — exibido na tela de custos e atualizado a cada novo registro (R-CUS-8) |
| POST | `/costs` | `{category_id, cost_type, amount, cost_date?, description?}` → `201` |
| GET | `/costs/{id}` | detalhe |
| PATCH | `/costs/{id}` | campos parciais + `version` |
| DELETE | `/costs/{id}` | exclusão lógica → `204` |

Regras: `FINANCIAL-RULES.md` seção 4.

Resposta de `GET /costs`:

```json
{
  "items": [
    { "id": 3, "cost_date": "2026-09-30", "category": { "id": 2, "name": "Embalagens" }, "cost_type": "CUSTO_DIARIO",
      "amount": "33.33", "running_total": "733.33", "description": null, "version": 1 }
  ],
  "total": 3, "page": 1, "page_size": 20, "pages": 1,
  "totals": { "daily_costs": "433.33", "fixed_costs": "300.00", "total_costs": "733.33", "count": 3 }
}
```

`running_total` é sempre calculado em ordem cronológica crescente (`cost_date`, `id`) sobre todo o filtro aplicado, independentemente da ordenação/paginação exibida.

### 3.9 Histórico

| Método | Rota | Descrição |
|---|---|---|
| GET | `/history` | consulta unificada de lançamentos |

Parâmetros: `type` (`SALE` \| `COST` \| `ALL`, padrão `ALL`), `start_date`, `end_date`, `buyer_type`, `company_id`, `customer_id`, `cost_type`, `category_id`, `page`, `page_size`, `sort` (`date`, `amount`), `order`.

* Com `buyer_type`, `company_id` ou `customer_id`, custos não se aplicam (não são vinculados a comprador) e o resultado contém somente vendas.
* Item:

```json
{
  "kind": "SALE",
  "id": 10,
  "date": "2026-09-01",
  "amount": "740.00",
  "sale": { "buyer": { "type": "COMPANY", "id": 1, "name": "Empresa A" }, "quantity": 40, "unit_price": "18.50", "subtotal": "740.00" },
  "cost": null
}
```

```json
{
  "kind": "COST",
  "id": 3,
  "date": "2026-09-05",
  "amount": "300.00",
  "sale": null,
  "cost": { "category": { "id": 7, "name": "Aluguel" }, "cost_type": "CUSTO_FIXO", "amount": "300.00" }
}
```

* A resposta inclui também `totals` do filtro aplicado (`sales_total`, `sales_quantity`, `sales_count`, `costs_total`), calculados no backend. Filtrando um comprador e um período (ex.: quinzena), `totals.sales_total` é o valor a cobrar no fechamento.
* Também disponíveis `/sales` e `/costs` para listagens específicas.

### 3.10 Dashboard

Parâmetros comuns de período: `period` (`today` \| `week` \| `month` \| `last_month` \| `custom`, padrão `month`); com `custom`, `start_date` e `end_date` são obrigatórios. A resposta sempre ecoa o período resolvido:

```json
"period": { "preset": "month", "start_date": "2026-09-01", "end_date": "2026-09-30", "days": 30 }
```

| Método | Rota | Descrição |
|---|---|---|
| GET | `/dashboard/summary` | indicadores gerais (empresas + clientes avulsos + todos os custos) |
| GET | `/dashboard/daily` | série diária geral (receita, quantidade, custos diários, fixos, totais, custos acumulados, lucro) |
| GET | `/dashboard/by-buyer` | **faturamento por comprador** (ranking de empresas e clientes) |
| GET | `/dashboard/sales-by-company-daily` | série diária de receita por empresa (histórico de vendas por empresa) |
| GET | `/dashboard/companies/{id}` | dashboard detalhado de uma empresa |
| GET | `/dashboard/customers/{id}` | dashboard detalhado de um cliente avulso (mesma estrutura) |

`GET /dashboard/summary`:

```json
{
  "period": { ... },
  "revenue": "1535.00",
  "revenue_by_buyer_type": { "COMPANY": "1425.00", "CUSTOMER": "110.00" },
  "quantity": 80,
  "quantity_by_buyer_type": { "COMPANY": 75, "CUSTOMER": 5 },
  "sales_count": 4,
  "daily_costs": "433.33",
  "fixed_costs": "300.00",
  "total_costs": "733.33",
  "net_profit": "801.67",
  "net_margin_percent": "52.23",
  "average_cost_per_meal": "9.17",
  "average_ticket": "383.75",
  "average_price_per_meal": "19.19"
}
```

`GET /dashboard/daily`:

```json
{
  "period": { ... },
  "items": [
    { "date": "2026-09-01", "revenue": "740.00", "quantity": 40, "daily_costs": "400.00",
      "fixed_costs": "0.00", "total_costs": "400.00", "cumulative_costs": "400.00", "net_profit": "340.00",
      "cumulative_net_profit": "340.00", "average_cost_per_meal": "10.00" }
  ]
}
```

`GET /dashboard/by-buyer` — parâmetros extras: `buyer_type` (filtra a lista), `sort` (`revenue`, `quantity`, `sales_count`; padrão `revenue desc`). Somente faturamento: custos são gerais e não são atribuídos a compradores (`FINANCIAL-RULES.md` seção 6).

```json
{
  "period": { ... },
  "revenue": "1535.00",
  "items": [
    { "buyer": { "type": "COMPANY", "id": 1, "name": "Empresa A" }, "revenue": "925.00", "quantity": 50, "sales_count": 2,
      "average_ticket": "462.50", "average_price_per_meal": "18.50", "revenue_share_percent": "60.26" },
    { "buyer": { "type": "COMPANY", "id": 2, "name": "Empresa B" }, "revenue": "500.00", "quantity": 25, "sales_count": 1,
      "average_ticket": "500.00", "average_price_per_meal": "20.00", "revenue_share_percent": "32.57" },
    { "buyer": { "type": "CUSTOMER", "id": 1, "name": "Cliente X" }, "revenue": "110.00", "quantity": 5, "sales_count": 1,
      "average_ticket": "110.00", "average_price_per_meal": "22.00", "revenue_share_percent": "7.17" }
  ],
  "subtotals": {
    "COMPANY":  { "revenue": "1425.00", "quantity": 75, "sales_count": 3 },
    "CUSTOMER": { "revenue": "110.00",  "quantity": 5,  "sales_count": 1 }
  }
}
```

`revenue_share_percent` = receita do comprador ÷ receita total × 100, arredondado; `null` se a receita total for zero.

`GET /dashboard/sales-by-company-daily`: `{ companies: [{id, name}], items: [{date, values: {"<company_id>": "<revenue>"}, customers_total: "<revenue>"}] }` — limitado às 10 empresas de maior receita no período + "Outras empresas" + "Clientes avulsos".

`GET /dashboard/companies/{id}` (e `/dashboard/customers/{id}`):

```json
{
  "period": { ... },
  "buyer": { "type": "COMPANY", "id": 1, "name": "Empresa A", "is_active": true, "billing_cycle": "MENSAL",
             "start_date": "2026-03-01", "payment_date": "2026-10-05" },
  "revenue": "925.00",
  "quantity": 50,
  "sales_count": 2,
  "average_ticket": "462.50",
  "average_price_per_meal": "18.50",
  "daily": [ { "date": "...", "revenue": "...", "quantity": 0, "sales_count": 0 } ],
  "recent_sales": [ /* últimas 20 vendas no período, SaleRead */ ],
  "comparison": { "previous_period": { "start_date": "...", "end_date": "..." }, "revenue": "...", "quantity": 0, "revenue_change_percent": "12.50" }
}
```

`comparison` compara com o período imediatamente anterior de mesma duração (evolução no período). `revenue_change_percent` é `null` se a receita anterior for zero.

### 3.11 Auditoria (ADMIN)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/audit-logs` | paginada; filtros `user_id`, `entity_type`, `entity_id`, `action`, `start_date`, `end_date`; ordenação `occurred_at` |

---

## 4. Testes de integração

Cada rota possui testes cobrindo: sucesso, validação (`422`), não autenticado (`401`), não encontrado (`404`) e, quando aplicável, conflito (`409`). Ver `TEST-PLAN.md`.
