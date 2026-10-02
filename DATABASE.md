# DATABASE.md

# Modelo de Dados — PostgreSQL 16

Este documento define tabelas, colunas, constraints, índices e dados iniciais. As migrations Alembic (Fase 1) devem implementar exatamente este modelo; qualquer divergência deve ser corrigida aqui ou no código.

---

## 1. Convenções

* Nomes de tabelas e colunas em inglês, `snake_case`, tabelas no plural.
* Chave primária `id BIGINT GENERATED ALWAYS AS IDENTITY`.
* `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` e `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` em todas as tabelas de negócio (UTC).
* `created_by` / `updated_by` referenciam `users.id` onde aplicável.
* Dinheiro: `NUMERIC(12,2)`; nunca `REAL`/`DOUBLE PRECISION`/`MONEY`.
* Datas de negócio: `DATE` (fuso `APP_TIMEZONE` resolvido no backend).
* Enums como `VARCHAR` + `CHECK` (mais simples de migrar que `CREATE TYPE`).
* Concorrência otimista: `version INTEGER NOT NULL DEFAULT 1`, incrementada a cada `UPDATE`.
* Unicidade de nomes é case-insensitive via índice único em `lower(name)`.

---

## 2. Diagrama de relacionamentos

```
users 1───* user_sessions
users 1───* audit_logs

companies 1───* customers
companies 1───* sales
customers 1───* sales

cost_categories 1───* costs
```

---

## 3. Tabelas

### 3.1 `users`

| Coluna | Tipo | Regras |
|---|---|---|
| id | BIGINT PK | |
| name | VARCHAR(120) | NOT NULL |
| email | VARCHAR(254) | NOT NULL, único em `lower(email)` |
| password_hash | VARCHAR(255) | NOT NULL (Argon2id) |
| role | VARCHAR(20) | NOT NULL, `CHECK (role IN ('ADMIN','GERENTE','OPERADOR'))` |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| last_login_at | TIMESTAMPTZ | NULL |
| version | INTEGER | NOT NULL DEFAULT 1 |
| created_at / updated_at | TIMESTAMPTZ | |

### 3.2 `user_sessions`

| Coluna | Tipo | Regras |
|---|---|---|
| id | UUID PK | `gen_random_uuid()`; vai no claim `sid` do JWT |
| user_id | BIGINT FK → users | NOT NULL, `ON DELETE CASCADE` |
| created_at | TIMESTAMPTZ | NOT NULL |
| expires_at | TIMESTAMPTZ | NOT NULL |
| revoked_at | TIMESTAMPTZ | NULL = ativa |
| ip_address | VARCHAR(45) | NULL |
| user_agent | VARCHAR(255) | NULL |

Índice: `(user_id) WHERE revoked_at IS NULL`.

### 3.3 `companies` (empresas contratantes)

| Coluna | Tipo | Regras |
|---|---|---|
| id | BIGINT PK | |
| name | VARCHAR(150) | NOT NULL, `CHECK (length(trim(name)) >= 2)`, único em `lower(name)` |
| trade_name | VARCHAR(150) | NULL (nome fantasia) |
| cnpj | CHAR(14) | NULL, somente dígitos, único quando não nulo, dígitos verificadores validados no backend |
| contact_name | VARCHAR(120) | NULL |
| phone | VARCHAR(20) | NULL |
| email | VARCHAR(254) | NULL |
| notes | TEXT | NULL |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| version, created_at, updated_at, created_by, updated_by | | |

Índices: `UNIQUE (lower(name))`, `UNIQUE (cnpj) WHERE cnpj IS NOT NULL`, `(is_active)`.

### 3.4 `customers` (clientes)

Decisão: o cliente pertence a uma empresa contratante (ex.: colaborador ou setor da empresa que recebe a marmita). A venda exige que o cliente pertença à empresa informada.

| Coluna | Tipo | Regras |
|---|---|---|
| id | BIGINT PK | |
| company_id | BIGINT FK → companies | NOT NULL, `ON DELETE RESTRICT` |
| name | VARCHAR(150) | NOT NULL, `CHECK (length(trim(name)) >= 2)` |
| document | VARCHAR(14) | NULL (CPF/CNPJ somente dígitos, opcional) |
| phone | VARCHAR(20) | NULL |
| email | VARCHAR(254) | NULL |
| notes | TEXT | NULL |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| version, created_at, updated_at, created_by, updated_by | | |

Índices: `UNIQUE (company_id, lower(name))`, `(company_id, is_active)`.

Regra: desativar uma empresa **não** desativa automaticamente seus clientes, mas clientes de empresa inativa também não aparecem em novos lançamentos (o filtro de lançamento exige empresa ativa **e** cliente ativo).

### 3.5 `cost_categories` (categorias de custo)

| Coluna | Tipo | Regras |
|---|---|---|
| id | BIGINT PK | |
| name | VARCHAR(80) | NOT NULL, único em `lower(name)` |
| cost_type | VARCHAR(20) | NOT NULL, `CHECK (cost_type IN ('CUSTO_DIARIO','CUSTO_FIXO'))` |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| version, created_at, updated_at, created_by, updated_by | | |

Regra: `cost_type` não pode ser alterado se a categoria já possuir custos (não excluídos), pois mudaria a classificação de lançamentos passados. A API responde `409`.

### 3.6 `sales` (vendas)

| Coluna | Tipo | Regras |
|---|---|---|
| id | BIGINT PK | |
| company_id | BIGINT FK → companies | NOT NULL, `ON DELETE RESTRICT` |
| customer_id | BIGINT FK → customers | NOT NULL, `ON DELETE RESTRICT` |
| sale_date | DATE | NOT NULL — definida pelo servidor |
| unit_price | NUMERIC(12,2) | NOT NULL, `CHECK (unit_price > 0)` |
| quantity | INTEGER | NOT NULL, `CHECK (quantity > 0)` |
| subtotal | NUMERIC(14,2) | NOT NULL, `CHECK (subtotal = unit_price * quantity)` |
| notes | VARCHAR(500) | NULL |
| deleted_at | TIMESTAMPTZ | NULL = ativa |
| deleted_by | BIGINT FK → users | NULL |
| version, created_at, updated_at, created_by, updated_by | | |

* O `CHECK` de subtotal garante no banco a fórmula `subtotal = unit_price × quantity` (o backend calcula; o banco impede inconsistência).
* Limites de negócio validados no backend (ver `FINANCIAL-RULES.md`): `unit_price ≤ 9999.99`, `quantity ≤ 10000`.
* A consistência "cliente pertence à empresa" é validada no serviço. Opcionalmente reforçada por FK composta `(customer_id, company_id) → customers(id, company_id)` (requer `UNIQUE (id, company_id)` em `customers`) — **adotada**.

Índices:
* `(sale_date) WHERE deleted_at IS NULL`
* `(company_id, sale_date) WHERE deleted_at IS NULL`
* `(customer_id, sale_date) WHERE deleted_at IS NULL`

### 3.7 `costs` (custos)

| Coluna | Tipo | Regras |
|---|---|---|
| id | BIGINT PK | |
| category_id | BIGINT FK → cost_categories | NOT NULL, `ON DELETE RESTRICT` |
| cost_type | VARCHAR(20) | NOT NULL, `CHECK (cost_type IN ('CUSTO_DIARIO','CUSTO_FIXO'))` |
| cost_date | DATE | NOT NULL |
| amount | NUMERIC(12,2) | NOT NULL, `CHECK (amount > 0)` |
| description | VARCHAR(500) | NULL |
| deleted_at | TIMESTAMPTZ | NULL |
| deleted_by | BIGINT FK → users | NULL |
| version, created_at, updated_at, created_by, updated_by | | |

* `cost_type` deve ser igual ao `cost_type` da categoria no momento do lançamento (validado no serviço). Fica gravado no custo para que agregações por tipo não dependam de join e para preservar o histórico.
* Reforço no banco: FK composta `(category_id, cost_type) → cost_categories(id, cost_type)` com `UNIQUE (id, cost_type)` em `cost_categories` e `ON UPDATE RESTRICT` — **adotada**, combinada com a regra de não alterar o tipo de categoria com custos.
* `cost_date` não pode estar no futuro em relação ao "hoje" do servidor (validado no serviço).

Índices:
* `(cost_date) WHERE deleted_at IS NULL`
* `(cost_type, cost_date) WHERE deleted_at IS NULL`
* `(category_id, cost_date) WHERE deleted_at IS NULL`

### 3.8 `audit_logs` (auditoria)

| Coluna | Tipo | Regras |
|---|---|---|
| id | BIGINT PK | |
| occurred_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |
| user_id | BIGINT FK → users | NULL (ex.: tentativa de login com e-mail inexistente) |
| action | VARCHAR(40) | NOT NULL (ver lista abaixo) |
| entity_type | VARCHAR(40) | NOT NULL (`user`, `company`, `customer`, `cost_category`, `sale`, `cost`, `session`) |
| entity_id | VARCHAR(40) | NULL |
| before_data | JSONB | NULL — estado anterior (campos relevantes) |
| after_data | JSONB | NULL — estado posterior |
| ip_address | VARCHAR(45) | NULL |
| user_agent | VARCHAR(255) | NULL |
| request_id | VARCHAR(64) | NULL |

Ações: `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`, `CREATE`, `UPDATE`, `ACTIVATE`, `DEACTIVATE`, `DELETE` (lógica), `PASSWORD_CHANGE`, `ROLE_CHANGE`.

* Tabela **somente inserção**: a aplicação não expõe atualização nem exclusão. Em produção, o usuário de banco da aplicação recebe apenas `INSERT, SELECT` nela.
* Nunca gravar senha, hash ou token em `before_data`/`after_data`.

Índices: `(occurred_at DESC)`, `(entity_type, entity_id)`, `(user_id, occurred_at DESC)`.

---

## 4. Dados iniciais (seed via migration)

Categorias de custo, todas ativas:

| Nome | Tipo |
|---|---|
| Ingredientes | CUSTO_DIARIO |
| Embalagens | CUSTO_DIARIO |
| Entregas | CUSTO_DIARIO |
| Equipamentos | CUSTO_DIARIO |
| Gasolina | CUSTO_DIARIO |
| Salários | CUSTO_FIXO |
| Aluguel | CUSTO_FIXO |
| Água | CUSTO_FIXO |
| Energia elétrica | CUSTO_FIXO |
| Gás | CUSTO_FIXO |

O primeiro usuário `ADMIN` **não** é criado por migration (não há senha no Git). É criado pelo comando `python -m app.cli create-admin`, lendo `INITIAL_ADMIN_EMAIL`/`INITIAL_ADMIN_PASSWORD` do ambiente ou de prompt interativo.

---

## 5. Consultas agregadas de referência

Todas as consultas usam intervalo **fechado** `[start_date, end_date]` e ignoram registros com `deleted_at IS NOT NULL`.

```sql
-- Receita e quantidade no período (opcionalmente por empresa)
SELECT COALESCE(SUM(subtotal), 0) AS revenue,
       COALESCE(SUM(quantity), 0) AS quantity,
       COUNT(*)                   AS sales_count
FROM sales
WHERE deleted_at IS NULL
  AND sale_date BETWEEN :start_date AND :end_date
  AND (:company_id IS NULL OR company_id = :company_id);

-- Custos por tipo no período
SELECT cost_type, COALESCE(SUM(amount), 0) AS total
FROM costs
WHERE deleted_at IS NULL
  AND cost_date BETWEEN :start_date AND :end_date
GROUP BY cost_type;

-- Série diária completa (dias sem movimento = 0)
SELECT d::date AS day,
       COALESCE(s.revenue, 0), COALESCE(s.quantity, 0),
       COALESCE(c.daily, 0), COALESCE(c.fixed, 0)
FROM generate_series(:start_date, :end_date, interval '1 day') AS d
LEFT JOIN (SELECT sale_date, SUM(subtotal) revenue, SUM(quantity) quantity
           FROM sales WHERE deleted_at IS NULL AND sale_date BETWEEN :start_date AND :end_date
           GROUP BY sale_date) s ON s.sale_date = d::date
LEFT JOIN (SELECT cost_date,
                  SUM(amount) FILTER (WHERE cost_type = 'CUSTO_DIARIO') daily,
                  SUM(amount) FILTER (WHERE cost_type = 'CUSTO_FIXO')   fixed
           FROM costs WHERE deleted_at IS NULL AND cost_date BETWEEN :start_date AND :end_date
           GROUP BY cost_date) c ON c.cost_date = d::date
ORDER BY day;
```

---

## 6. Migrations

* Ferramenta: Alembic, diretório `backend/alembic/versions/`.
* Uma migration por mudança de esquema, com `upgrade()` e `downgrade()`.
* Migration inicial: `0001_initial_schema` (todas as tabelas, constraints e índices) e `0002_seed_cost_categories`.
* Teste obrigatório: `alembic upgrade head` → `alembic downgrade base` → `alembic upgrade head` em banco vazio.
* Nenhuma extensão é necessária: `gen_random_uuid()` é nativo no PostgreSQL ≥ 13.
