# TEST-PLAN.md

# Plano de Testes

Objetivo: garantir que cadastros, lançamentos, autenticação e, principalmente, os cálculos financeiros (lucro líquido geral, faturamento por comprador e custos acumulados) estejam corretos e permaneçam corretos a cada mudança.

---

## 1. Níveis de teste

| Nível | Ferramenta | Escopo | Banco |
|---|---|---|---|
| Unitário backend | pytest | `financial_engine`, `periods`, validadores (CNPJ, CPF, dinheiro) | não usa |
| Integração backend | pytest + TestClient | rotas da API + serviços + repositórios + migrations | PostgreSQL de teste |
| Migrations | pytest / script | `upgrade head` → `downgrade base` → `upgrade head` | PostgreSQL de teste |
| Unitário frontend | Vitest + Testing Library | componentes, formatação pt-BR, formulários, rotas protegidas | API simulada (mock de `fetch`, `src/test/utils.tsx`) |
| E2E | Playwright | fluxos principais no navegador | stack completa via Docker Compose |

Banco de teste: banco `marmitex_test` separado; migrations aplicadas uma vez por sessão; cada teste roda em transação revertida ao final. Relógio do negócio fixado via `core/clock.py` (hoje = 2026-09-30, quarta-feira) para testes determinísticos.

Comandos (definidos na Fase 1):

```bash
# backend
cd backend && pytest                      # todos
cd backend && pytest tests/unit           # só unitários
cd backend && ruff check . && mypy app

# frontend
cd frontend && npm run test               # Vitest
cd frontend && npm run lint && npm run typecheck
cd frontend && npm run e2e                # Playwright (backend + `npm run preview` rodando)
# variáveis do E2E: E2E_BASE_URL (padrão http://localhost:4173), E2E_EMAIL, E2E_PASSWORD,
# PLAYWRIGHT_CHROMIUM_PATH (opcional, caminho de um Chromium já instalado)
```

Meta de cobertura: ≥ 90% em `financial_engine.py` e `periods.py` (100% dos ramos de divisão por zero); ≥ 80% no backend como um todo.

---

## 2. Motor financeiro — cenários obrigatórios

Base de dados de referência: `FINANCIAL-RULES.md`, seção 7 (Empresas A e B, Cliente avulso X). Os cenários são testados **duas vezes**: (a) unitário, chamando o motor com agregados; (b) integração, inserindo vendas/custos e chamando `/dashboard/summary`, `/dashboard/daily` e `/dashboard/by-buyer`.

| # | Cenário | Entrada | Resultado esperado |
|---|---|---|---|
| FIN-01 | Um dia | `custom` 30/09–30/09 | RECEITA 185.00; QTD 10; CT 33.33; LUCRO 151.67; CMM 3.33 |
| FIN-02 | Semana | `week` (28/09–30/09) | RECEITA 185.00; CT 33.33; LUCRO 151.67 |
| FIN-03 | Mês (geral, tudo incluso) | `month` (01/09–30/09) | RECEITA 1535.00 (Empresas 1425.00, Clientes 110.00); QTD 80 (75/5); CD 433.33; CF 300.00; CT 733.33; LUCRO 801.67; MARGEM 52.23; CMM 9.17; TM 383.75; PM 19.19 |
| FIN-04 | Período personalizado | 01/09–15/09 | RECEITA 1240.00; QTD 65; CT 700.00; LUCRO 540.00; CMM 10.77 |
| FIN-05 | Período inclusivo nas bordas | 01/09–30/09 vs. 02/09–29/09 | RECEITA 1535.00 vs. 610.00 |
| FIN-06 | Empresa | Empresa A, mês | faturamento 925.00; QTD 50; NV 2; TM 462.50; PM 18.50; participação 60.26; sem campos de custo/lucro |
| FIN-07 | Várias empresas / faturamento por comprador | `by-buyer`, mês | A 925.00 (60.26%); B 500.00 (32.57%); Cliente X 110.00 (7.17%); subtotal Empresas 1425.00 / 75; Clientes 110.00 / 5; Σ = RECEITA |
| FIN-08 | Sem vendas | 05/09–05/09 | RECEITA 0.00; QTD 0; CT 300.00; LUCRO −300.00; CMM null; TM null; MARGEM null |
| FIN-09 | Sem custos | 15/09–15/09 | RECEITA 500.00; CT 0.00; LUCRO 500.00; CMM 0.00 |
| FIN-10 | Sem vendas e sem custos | 02/09–04/09 | totais 0.00; CMM/TM/MARGEM null; série diária com 3 dias zerados; ranking vazio |
| FIN-11 | Divisão por zero | QTD = 0, NV = 0, RECEITA = 0 em todas as médias, margens, `revenue_share_percent` e `revenue_change_percent` | nenhum erro; campos `null` |
| FIN-12 | Somente custos fixos | Aluguel 300.00 + venda B (500.00, 25) | CF 300.00; CD 0.00; CT 300.00; CMM 12.00; LUCRO 200.00 |
| FIN-13 | Somente custos diários | Ingredientes 400.00 + venda A (740.00, 40) | CD 400.00; CF 0.00; CT 400.00; CMM 10.00; LUCRO 340.00 |
| FIN-14 | Vendas sem custos | período maior só com vendas | LUCRO = RECEITA |
| FIN-15 | Custos sem vendas | período maior só com custos | LUCRO = −CT; CMM null |
| FIN-16 | Arredondamento de médias | CT 10.00/QTD 3; CT 10.00/QTD 6; CT 0.05/QTD 2 | 3.33; 1.67; 0.03 (ROUND_HALF_UP) |
| FIN-17 | Subtotal exato | 18.50 × 40; 0.01 × 10000; 9999.99 × 10000 | 740.00; 100.00; 99999900.00 |
| FIN-18 | Exclusão lógica | venda/custo excluído | não entra em nenhum total nem no acumulado |
| FIN-19 | Consistência da série | qualquer período | Σ diária de receita, quantidade, CD, CF = totais do resumo |
| FIN-20 | Fuso horário | relógio às 23:30 de 30/09 em São Paulo (02:30 UTC de 01/10), venda sem data | `sale_date = 2026-09-30` |
| FIN-21 | Lucro negativo | custos > receita | LUCRO negativo exato |
| FIN-22 | Precisão | 1.000 vendas de 0.01 | RECEITA 10.00 exato |
| FIN-23 | Custos acumulados | listagem de custos do mês | `running_total` 400.00 → 700.00 → 733.33; último = CT; igual com ordenação desc e em qualquer página |
| FIN-24 | Só clientes avulsos | apenas vendas para clientes | subtotal Empresas zerado; RECEITA = subtotal Clientes |
| FIN-25 | Lançamento retroativo | ADMIN lança em 30/09 um custo/venda com data 10/09 | entra no dia 10/09 (série e totais do período que contém 10/09) |
| FIN-26 | Mês anterior | `last_month` com hoje 30/09 | período 01/08–31/08 |
| FIN-27 | Faturamento estável ao filtrar | faturamento da Empresa A em `by-buyer`, `by-buyer?buyer_type=COMPANY` e `/dashboard/companies/1` | mesmo valor |
| FIN-28 | Série acumulada | `/dashboard/daily`, mês | `cumulative_costs` do último dia = 733.33; `cumulative_net_profit` do último dia = 801.67 |
| FIN-29 | Resumo de custos do mês | `/costs/summary` após cada novo custo | total aumenta exatamente pelo valor do novo custo |

Conferência de FIN-04: vendas 01/09 (740.00, 40) e 15/09 (500.00, 25) → 1240.00 e 65; custos 400.00 + 300.00 = 700.00; CMM = 700.00 ÷ 65 = 10.769… → 10.77.

Teste de propriedade (Hypothesis): para listas aleatórias de vendas/custos/compradores, verificar `LUCRO = RECEITA − CT`, `CT = CF + CD`, `Σ RECEITA_i = RECEITA`, Σ diária = total, último acumulado = total, e que nenhuma combinação gera exceção de divisão.

---

## 3. Vendas

| # | Caso | Esperado |
|---|---|---|
| VEN-01 | Criar venda para empresa sem data | 201; `sale_date` = hoje do servidor; subtotal calculado; auditoria `CREATE` |
| VEN-02 | Criar venda para cliente avulso com data passada escolhida | 201 com a data informada |
| VEN-03 | Data futura | 422 |
| VEN-04 | Cliente envia `subtotal` | 422 |
| VEN-05 | `buyer_type=COMPANY` sem `company_id`, com `customer_id`, ou ambos preenchidos | 422 (e o `CHECK` do banco também bloqueia) |
| VEN-06 | Preço 0, negativo, 3 casas decimais, > 9999.99 | 422 |
| VEN-07 | Quantidade 0, negativa, fracionária, > 10000 | 422 |
| VEN-08 | Empresa/cliente inexistente ou inativo | 422 no campo correspondente |
| VEN-09 | Editar preço/quantidade/data | subtotal recalculado; `version` incrementada; auditoria com antes/depois |
| VEN-10 | Editar com `version` antiga | 409 `VERSION_CONFLICT` |
| VEN-11 | Trocar comprador de empresa para cliente | 200; constraint respeitada |
| VEN-12 | Excluir venda | 204; some de listagens e totais; auditoria `DELETE` |
| VEN-13 | Manter comprador desativado após a venda ao editar só a quantidade | 200 (R-VEN-7) |

### Recebimento e pagamento (`test_delivery_payment.py`)

| # | Caso | Esperado |
|---|---|---|
| PAG-01 | Cadastro com recebimento padrão; filtro `delivery_type` | empresa padrão OBRA, cliente padrão RETIRADA; listas filtráveis |
| PAG-02 | Venda sem `delivery_type` | herda o padrão do comprador; pode ser sobrescrito |
| PAG-03 | Marcar venda como paga | `payment_status = PAGO`, subtotal inalterado, auditoria antes/depois |
| PAG-04 | Totais | receita conta pagas + pendentes; `pending_revenue`/`sales_pending_total` = só pendentes; filtros por pagamento e recebimento |

## 4. Custos

| # | Caso | Esperado |
|---|---|---|
| CUS-01 | Criar custo sem data | 201; `cost_date` = hoje |
| CUS-02 | Criar custo com data passada | 201 |
| CUS-03 | Data futura | 422 |
| CUS-04 | Valor 0, negativo, 3 casas | 422 |
| CUS-05 | Categoria inexistente / inativa | 422 |
| CUS-06 | Tipo diferente do tipo da categoria / tipo inválido | 422 |
| CUS-07 | Editar e excluir com auditoria e `version` | igual vendas |
| CUS-08 | Nova categoria cadastrada pelo ADMIN (ex.: "Descartáveis", diário) | disponível imediatamente no lançamento |

## 5. Cadastros

| # | Caso | Esperado |
|---|---|---|
| CAD-01 | Criar/editar empresa válida com `billing_cycle`, `start_date`, `payment_date` | 201/200; auditoria |
| CAD-02 | Nome duplicado (case-insensitive) / CNPJ duplicado | 409 |
| CAD-03 | CNPJ com dígito verificador inválido; `billing_cycle` inválido | 422 |
| CAD-04 | Desativar/ativar empresa | some/volta em `?active=true` (lista do lançamento) |
| CAD-05 | Pesquisa `q` por nome, nome fantasia e CNPJ | resultados corretos, paginados |
| CAD-06 | Criar cliente avulso sem nenhuma empresa cadastrada | 201 (independente) |
| CAD-07 | Dois clientes com o mesmo nome | permitido; CPF duplicado → 409; CPF inválido → 422 |
| CAD-08 | Pesquisa de clientes por nome, telefone e local | ok |
| CAD-09 | Categoria: criar, editar, ativar, desativar, pesquisar | ok |
| CAD-10 | Alterar `cost_type` de categoria com custos | 409 |
| CAD-11 | Seed: 10 categorias padrão com tipos corretos | presentes após migrations |

## 6. Autenticação e auditoria

| # | Caso | Esperado |
|---|---|---|
| AUT-01 | Login válido | 200 com token; `LOGIN_SUCCESS` auditado; `last_login_at` atualizado |
| AUT-02 | Senha errada / e-mail inexistente | 401 com a **mesma** mensagem; `LOGIN_FAILED` |
| AUT-03 | 6ª falha em 15 min | 429 |
| AUT-04 | Usuário inativo | 401 |
| AUT-05 | Token expirado / assinatura inválida / ausente | 401 |
| AUT-06 | Logout e reutilização do token | 204, depois 401 |
| AUT-07 | Desativar usuário revoga sessões | próximo request 401 |
| AUT-08 | Todas as rotas protegidas sem token | 401 (teste parametrizado sobre todas as rotas do OpenAPI, exceto login e health) |
| AUT-09 | Desativar a si mesmo / o último ADMIN ativo | 409 |
| AUT-10 | Senha armazenada | hash Argon2id; nunca aparece em respostas, logs ou auditoria |
| AUD-01 | Toda criação/edição/ativação/desativação/exclusão | 1 registro de auditoria com usuário, entidade, antes/depois |
| AUD-02 | Falha da operação | nenhuma auditoria gravada (mesma transação) |
| AUD-03 | `/audit-logs` | filtros e paginação |

## 7. API — recursos transversais

| # | Caso | Esperado |
|---|---|---|
| API-01 | Paginação: `page_size` 0 ou 101 | 422; `pages`/`total` corretos |
| API-02 | Ordenação: campo não permitido | 422; ordenação estável com desempate por `id` |
| API-03 | Formato de erro | todas as respostas de erro seguem `{error:{code,message,details,request_id}}` |
| API-04 | Dinheiro em JSON | sempre string com 2 casas |
| API-05 | OpenAPI | `/api/openapi.json` válido e contém todas as rotas |
| API-06 | Health | `live` 200; `ready` 200 com banco e 503 sem banco |
| HIS-01 | Histórico `type=ALL` | vendas e custos intercalados por data |
| HIS-02 | Filtros `buyer_type`/empresa/cliente | só vendas do comprador |
| HIS-03 | Filtros de data inclusivos e `totals` (fechamento quinzenal/mensal) | corretos |
| DSH-01 | `period` inválido; `custom` sem datas; início > fim; > 366 dias na série | 422 |
| DSH-02 | `/dashboard/companies/{id}` e `/dashboard/customers/{id}` | faturamento, qtd, ticket, vendas recentes, comparação; sem custo/lucro |
| DSH-03 | `by-buyer` | ordenado por faturamento; `revenue_share_percent` soma ≈ 100 (tolerância de arredondamento) |

## 8. Frontend

| # | Caso |
|---|---|
| FE-01 | Rotas protegidas redirecionam para `/login` sem sessão; após login voltam à rota pedida |
| FE-02 | Lançamento de venda: escolher "Empresa" ou "Cliente avulso" troca o seletor; data pré-preenchida com hoje e editável; data futura bloqueada |
| FE-03 | Formulários exibem erros por campo vindos de `error.details` |
| FE-04 | Selects de lançamento só listam empresas/clientes/categorias ativos |
| FE-05 | Formatação: `"1234.5"` → `R$ 1.234,50`; `"2026-09-01"` → `01/09/2026`; `null` → "—" |
| FE-06 | Nenhum cálculo financeiro no frontend (revisão de código + teste: valores exibidos = valores da API simulada) |
| FE-07 | Dashboard: filtros na URL; estados vazio/carregando/erro; ranking de faturamento por empresa |
| FE-09 | Tela de custos: totais do mês e coluna Acumulado atualizam após novo custo |
| FE-10 | Venda: recebimento preenchido pelo cadastro do comprador; opção Pago/Pendente enviada à API |
| FE-08 | Conflito de versão (409) mostra mensagem e recarrega o registro |

## 9. E2E (Playwright)

1. Login → criar empresa → criar cliente avulso → lançar venda para cada um → marcar venda como paga → ver no histórico → ver no dashboard (receita geral e por tipo).
2. Cadastrar nova categoria de custo → lançar custo diário e fixo → tela de custos soma o acumulado → dashboard mostra custos, lucro geral, faturamento por empresa e custo médio iguais aos da API.
3. Lançar venda esquecida com data de ontem → aparece no dia correto do gráfico.
4. Desativar empresa → ela não aparece em novo lançamento, mas continua no histórico e no dashboard.
5. Logout → token invalidado; acesso direto a `/dashboard` redireciona para `/login`.

## 10. Não funcionais (Fase 5)

* Performance (uso em 1–2 notebooks): seed com 20 mil vendas em 2 anos; `/dashboard/summary`, `/dashboard/daily` (366 dias) e `/dashboard/by-buyer` < 500 ms.
* Concorrência: duas edições simultâneas da mesma venda → uma 200 e uma 409.
* Segurança: varredura de secrets no repositório; dependências sem vulnerabilidades críticas conhecidas; cabeçalhos de segurança presentes.
* Backup: gerar dump, restaurar em banco limpo e conferir totais do dashboard.

## 11. Regra de execução

* Antes de cada commit de fase: executar todos os testes do backend e do frontend.
* Testes falhando bloqueiam a conclusão da fase.
* Resultado (comando, total, falhas) registrado em `PROJECT-STATE.md`, seção "Testes da última sessão".
