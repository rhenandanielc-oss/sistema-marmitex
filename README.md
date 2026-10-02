# Sistema Marmitex B2B

Gestão de vendas B2B de marmitex (empreiteiras e clientes avulsos) e controle financeiro: cadastros, vendas, custos, histórico, dashboard com lucro líquido, faturamento por empresa, recebimento (retirada/entrega/obra) e pagamentos pendentes.

Feito para uso local em **um notebook** (opcionalmente, acesso de um segundo notebook na mesma rede).

| Documento | Para quê |
|---|---|
| [`INSTALL.md`](INSTALL.md) | Instalar em um notebook (dois cliques no Windows); segundo notebook opcional |
| [`OPERACAO.md`](OPERACAO.md) | Backup, restauração, atualização, logs, problemas comuns |
| [`GUIA-DO-ADMIN.md`](GUIA-DO-ADMIN.md) | Como usar as telas no dia a dia |
| [`FINANCIAL-RULES.md`](FINANCIAL-RULES.md) | Regras e fórmulas financeiras oficiais |
| [`ARCHITECTURE.md`](ARCHITECTURE.md), [`DATABASE.md`](DATABASE.md), [`API.md`](API.md), [`DASHBOARD.md`](DASHBOARD.md) | Documentação técnica |
| [`TEST-PLAN.md`](TEST-PLAN.md), [`AUDITORIA.md`](AUDITORIA.md) | Plano de testes e auditoria técnica |
| [`PROJECT-STATE.md`](PROJECT-STATE.md) | Estado do projeto e decisões |

## Início rápido

Windows: instale o Docker Desktop, copie `.env.example` para `.env`, preencha as senhas (`INSTALL.md` seção 4) e dê dois cliques em **`primeira-instalacao.bat`**. No dia a dia: **`iniciar-marmitex.bat`**.

Terminal (qualquer sistema):

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
