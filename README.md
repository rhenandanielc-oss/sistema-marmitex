# Sistema Marmitex B2B

Gestão de vendas B2B de marmitex (empreiteiras e clientes avulsos) e controle financeiro: cadastros, vendas, custos, histórico, dashboard com lucro líquido, faturamento por empresa, recebimento (retirada/entrega/obra) e pagamentos pendentes.

Feito para uso local em 1–2 notebooks.

| Documento | Para quê |
|---|---|
| [`INSTALL.md`](INSTALL.md) | Instalar no notebook principal e acessar do segundo notebook |
| [`OPERACAO.md`](OPERACAO.md) | Backup, restauração, atualização, logs, problemas comuns |
| [`GUIA-DO-ADMIN.md`](GUIA-DO-ADMIN.md) | Como usar as telas no dia a dia |
| [`FINANCIAL-RULES.md`](FINANCIAL-RULES.md) | Regras e fórmulas financeiras oficiais |
| [`ARCHITECTURE.md`](ARCHITECTURE.md), [`DATABASE.md`](DATABASE.md), [`API.md`](API.md), [`DASHBOARD.md`](DASHBOARD.md) | Documentação técnica |
| [`TEST-PLAN.md`](TEST-PLAN.md), [`AUDITORIA.md`](AUDITORIA.md) | Plano de testes e auditoria técnica |
| [`PROJECT-STATE.md`](PROJECT-STATE.md) | Estado do projeto e decisões |

## Início rápido

```bash
cp .env.example .env          # preencha senhas e JWT_SECRET (INSTALL.md seção 4)
docker compose up -d --build
docker compose exec backend python -m app.cli create-admin
# abrir http://localhost:8080
```

## Desenvolvimento

```bash
# backend (Python 3.11+, PostgreSQL 16)
cd backend && pip install -e ".[dev]"
alembic upgrade head && uvicorn app.main:app --reload      # API em :8000, docs em /api/docs
pytest && ruff check . && mypy app

# frontend (Node 22)
cd frontend && npm ci
npm run dev                                                # :5173, proxy /api → :8000
npm run test && npm run lint && npm run typecheck && npm run build
npm run e2e                                                # com backend + `npm run preview` rodando
```

Stack: FastAPI · SQLAlchemy · Alembic · PostgreSQL · React · TypeScript · Vite · Tailwind · React Query · Recharts · Docker.
