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
| `q` | busca textual (case-insensitive, `ILIKE`) em nome/nome fantasia/CNPJ/e-mail conforme a rota |
| `active` | `true` / `false` / omitido (todos) |
| `start_date`, `end_date` | intervalo fechado (ver `FINANCIAL-RULES.md`, R-PER-1) |
| `company_id` | filtro por empresa; pode ser repetido (`company_id=1&company_id=2`) onde indicado |

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
| 403 | `FORBIDDEN` | sem permissão |
| 404 | `NOT_FOUND` | recurso inexistente (ou excluído logicamente) |
| 409 | `CONFLICT` | duplicidade (nome, CNPJ, e-mail) ou regra de integridade |
| 409 | `VERSION_CONFLICT` | `version` divergente (edição concorrente) |
| 422 | `VALIDATION_ERROR` | validação de campos e regras de negócio (ex.: empresa inativa) |
| 429 | `TOO_MANY_REQUESTS` | limite de tentativas de login |
| 500 | `INTERNAL_ERROR` | erro inesperado (sem detalhes internos na resposta) |

Mensagens em português.

### 1.5 Concorrência

`PATCH` de entidades editáveis exige o campo `version` no corpo. Se a versão no banco for diferente → `409 VERSION_CONFLICT`. A resposta de sucesso devolve a nova `version`.

---

## 2. Autorização

### 2.1 Permissões

| Permissão | ADMIN | GERENTE | OPERADOR |
|---|:-:|:-:|:-:|
| `users:manage` | ✔ | | |
| `audit:read` | ✔ | | |
| `companies:read` | ✔ | ✔ | ✔ (somente ativas) |
| `companies:write` (criar/editar/ativar/desativar) | ✔ | ✔ | |
| `customers:read` | ✔ | ✔ | ✔ (somente ativos) |
| `customers:write` | ✔ | ✔ | ✔ (criar apenas) |
| `categories:read` | ✔ | ✔ | ✔ (somente ativas) |
| `categories:write` | ✔ | ✔ | |
| `sales:create` | ✔ | ✔ | ✔ |
| `sales:update` / `sales:delete` | ✔ | ✔ | próprias e do dia atual |
| `sales:update_date` | ✔ | | |
| `costs:create` | ✔ | ✔ | ✔ (somente data de hoje) |
| `costs:update` / `costs:delete` | ✔ | ✔ | próprios e do dia atual |
| `history:read` | ✔ | ✔ | somente dia atual |
| `dashboard:read` | ✔ | ✔ | |

A matriz fica em `backend/app/core/permissions.py` e é retornada em `GET /auth/me` para o frontend ajustar a interface.

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
| GET | `/auth/me` | usuário atual + `permissions: string[]` |
| POST | `/auth/change-password` | `{current_password, new_password}` → `204`; revoga as outras sessões |

Login: auditado (`LOGIN_SUCCESS` / `LOGIN_FAILED`), limitado a 5 falhas por e-mail+IP em 15 min (`429`).

### 3.3 Usuários (`users:manage`)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/users` | lista paginada; filtros `q`, `active`, `role`; ordenação `name`, `email`, `created_at` |
| POST | `/users` | `{name, email, password, role}` |
| GET | `/users/{id}` | detalhe |
| PATCH | `/users/{id}` | `{name?, role?, version}` |
| POST | `/users/{id}/activate` · `/users/{id}/deactivate` | desativar revoga sessões; o admin não pode desativar a si mesmo |
| POST | `/users/{id}/reset-password` | `{new_password}` |

### 3.4 Empresas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/companies` | paginada; filtros `q` (nome, nome fantasia, CNPJ), `active`; ordenação `name`, `created_at` |
| POST | `/companies` | `{name, trade_name?, cnpj?, contact_name?, phone?, email?, notes?}` → `201` |
| GET | `/companies/{id}` | detalhe |
| PATCH | `/companies/{id}` | campos parciais + `version` |
| POST | `/companies/{id}/activate` · `/companies/{id}/deactivate` | `{version}` → entidade atualizada |

Validações: nome obrigatório (2–150), único (case-insensitive); CNPJ com 14 dígitos e dígitos verificadores válidos, único; e-mail válido.

### 3.5 Clientes

| Método | Rota | Descrição |
|---|---|---|
| GET | `/customers` | paginada; filtros `q`, `active`, `company_id`; `for_entry=true` retorna só clientes ativos de empresas ativas; ordenação `name`, `company`, `created_at` |
| POST | `/customers` | `{company_id, name, document?, phone?, email?, notes?}` — empresa deve estar ativa |
| GET | `/customers/{id}` | detalhe (inclui `company: {id, name}`) |
| PATCH | `/customers/{id}` | campos parciais + `version` |
| POST | `/customers/{id}/activate` · `/customers/{id}/deactivate` | `{version}` |

### 3.6 Categorias de custo

| Método | Rota | Descrição |
|---|---|---|
| GET | `/cost-categories` | paginada; filtros `q`, `active`, `cost_type`; ordenação `name`, `cost_type` |
| POST | `/cost-categories` | `{name, cost_type}` |
| PATCH | `/cost-categories/{id}` | `{name?, cost_type?, version}` — alterar `cost_type` com custos existentes → `409` |
| POST | `/cost-categories/{id}/activate` · `/cost-categories/{id}/deactivate` | `{version}` |

### 3.7 Vendas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/sales` | paginada; filtros `start_date`, `end_date`, `company_id`, `customer_id`; ordenação `sale_date`, `subtotal`, `quantity`, `company`, `customer` (padrão `sale_date desc`) |
| POST | `/sales` | `{company_id, customer_id, unit_price, quantity, notes?}` → `201` |
| GET | `/sales/{id}` | detalhe |
| PATCH | `/sales/{id}` | `{company_id?, customer_id?, unit_price?, quantity?, notes?, sale_date? (ADMIN), version}` |
| DELETE | `/sales/{id}` | exclusão lógica → `204` |

Resposta `SaleRead`:

```json
{
  "id": 10,
  "sale_date": "2026-09-01",
  "company": { "id": 1, "name": "Empresa A" },
  "customer": { "id": 7, "name": "Setor Produção" },
  "unit_price": "18.50",
  "quantity": 40,
  "subtotal": "740.00",
  "notes": null,
  "version": 1,
  "created_at": "2026-09-01T14:03:11Z",
  "created_by": { "id": 2, "name": "Maria" }
}
```

Regras: `FINANCIAL-RULES.md` seção 3. Campos `sale_date` e `subtotal` enviados na criação são rejeitados (`422`) para deixar explícito que são do servidor.

### 3.8 Custos

| Método | Rota | Descrição |
|---|---|---|
| GET | `/costs` | paginada; filtros `start_date`, `end_date`, `cost_type`, `category_id`; ordenação `cost_date`, `amount`, `category` |
| POST | `/costs` | `{category_id, cost_type, amount, cost_date?, description?}` → `201` |
| GET | `/costs/{id}` | detalhe |
| PATCH | `/costs/{id}` | campos parciais + `version` |
| DELETE | `/costs/{id}` | exclusão lógica → `204` |

Regras: `FINANCIAL-RULES.md` seção 4.

### 3.9 Histórico

| Método | Rota | Descrição |
|---|---|---|
| GET | `/history` | consulta unificada de lançamentos |

Parâmetros: `type` (`SALE` \| `COST` \| `ALL`, padrão `ALL`), `start_date`, `end_date`, `company_id`, `customer_id`, `cost_type`, `category_id`, `page`, `page_size`, `sort` (`date`, `amount`), `order`.

* Com `company_id` ou `customer_id`, custos não se aplicam (não são vinculados a empresa) e o resultado contém somente vendas.
* Item:

```json
{
  "kind": "SALE",
  "id": 10,
  "date": "2026-09-01",
  "amount": "740.00",
  "sale": { "company": {...}, "customer": {...}, "quantity": 40, "unit_price": "18.50", "subtotal": "740.00" },
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

* A resposta inclui também `totals` do filtro aplicado (`sales_total`, `sales_quantity`, `costs_total`), calculados no backend.
* Também disponíveis `/sales` e `/costs` para listagens específicas.

### 3.10 Dashboard (`dashboard:read`)

Parâmetros comuns de período: `period` (`today` \| `week` \| `month` \| `custom`, padrão `month`); com `custom`, `start_date` e `end_date` são obrigatórios. `company_id` opcional e repetível. A resposta sempre ecoa o período resolvido:

```json
"period": { "preset": "month", "start_date": "2026-09-01", "end_date": "2026-09-30", "days": 30 }
```

| Método | Rota | Descrição |
|---|---|---|
| GET | `/dashboard/summary` | indicadores do período |
| GET | `/dashboard/daily` | série diária (receita, quantidade, custos diários, custos fixos, custos totais, lucro) |
| GET | `/dashboard/revenue-by-company` | receita, quantidade e participação por empresa |
| GET | `/dashboard/sales-by-company-daily` | série diária de receita por empresa (histórico de vendas por empresa) |
| GET | `/dashboard/companies/{id}` | dashboard detalhado de uma empresa |

`GET /dashboard/summary` (sem filtro de empresa):

```json
{
  "period": { ... },
  "company_ids": [],
  "revenue": "1425.00",
  "quantity": 75,
  "sales_count": 3,
  "daily_costs": "433.33",
  "fixed_costs": "300.00",
  "total_costs": "733.33",
  "net_profit": "691.67",
  "average_cost_per_meal": "9.78",
  "average_ticket": "475.00",
  "average_price_per_meal": "19.00"
}
```

Com filtro de empresa, acrescenta (ver `FINANCIAL-RULES.md` seção 6):

```json
{
  "revenue": "925.00",
  "quantity": 50,
  "global_costs": { "daily_costs": "433.33", "fixed_costs": "300.00", "total_costs": "733.33", "quantity": 75, "average_cost_per_meal": "9.78" },
  "allocated_costs": "488.89",
  "estimated_profit": "436.11",
  "allocation_available": true,
  "net_profit": null
}
```

`GET /dashboard/daily`:

```json
{
  "period": { ... },
  "items": [
    { "date": "2026-09-01", "revenue": "740.00", "quantity": 40, "daily_costs": "400.00",
      "fixed_costs": "0.00", "total_costs": "400.00", "profit": "340.00", "average_cost_per_meal": "10.00" }
  ]
}
```

Com filtro de empresa, os custos de cada dia são os alocados ao dia (rateio sobre o dia) e o campo `profit` vira `estimated_profit`.

`GET /dashboard/revenue-by-company`: `items: [{company: {id, name}, revenue, quantity, sales_count, share_percent}]`, ordenado por receita desc. `share_percent` = receita da empresa ÷ receita total × 100, arredondado em 2 casas; `null` se a receita total for zero.

`GET /dashboard/sales-by-company-daily`: `{ companies: [{id, name}], items: [{date, values: {"<company_id>": "<revenue>"}}] }` — limitado às 10 empresas de maior receita no período + "Outras".

`GET /dashboard/companies/{id}`:

```json
{
  "period": { ... },
  "company": { "id": 1, "name": "Empresa A", "is_active": true },
  "revenue": "925.00",
  "quantity": 50,
  "sales_count": 2,
  "average_ticket": "462.50",
  "average_price_per_meal": "18.50",
  "allocated_costs": "488.89",
  "estimated_profit": "436.11",
  "daily": [ { "date": "...", "revenue": "...", "quantity": 0, "sales_count": 0 } ],
  "customers": [ { "customer": { "id": 7, "name": "..." }, "revenue": "...", "quantity": 0, "sales_count": 0 } ],
  "recent_sales": [ /* últimas 20 vendas no período, SaleRead */ ],
  "comparison": { "previous_period": { "start_date": "...", "end_date": "..." }, "revenue": "...", "quantity": 0, "revenue_change_percent": "12.50" }
}
```

`comparison` compara com o período imediatamente anterior de mesma duração (evolução no período). `revenue_change_percent` é `null` se a receita anterior for zero.

### 3.11 Auditoria (`audit:read`)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/audit-logs` | paginada; filtros `user_id`, `entity_type`, `entity_id`, `action`, `start_date`, `end_date`; ordenação `occurred_at` |

---

## 4. Testes de integração

Cada rota possui testes cobrindo: sucesso, validação (`422`), não autenticado (`401`), sem permissão (`403`), não encontrado (`404`) e, quando aplicável, conflito (`409`). Ver `TEST-PLAN.md`.
