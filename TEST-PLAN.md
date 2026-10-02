# TEST-PLAN.md

# Plano de Testes

Objetivo: garantir que cadastros, lançamentos, permissões e, principalmente, os cálculos financeiros estejam corretos e permaneçam corretos a cada mudança.

---

## 1. Níveis de teste

| Nível | Ferramenta | Escopo | Banco |
|---|---|---|---|
| Unitário backend | pytest | `financial_engine`, `periods`, validadores (CNPJ, dinheiro), permissões | não usa |
| Integração backend | pytest + TestClient | rotas da API + serviços + repositórios + migrations | PostgreSQL de teste |
| Migrations | pytest / script | `upgrade head` → `downgrade base` → `upgrade head` | PostgreSQL de teste |
| Unitário frontend | Vitest + Testing Library | componentes, formatação pt-BR, formulários, rotas protegidas | API simulada (MSW) |
| E2E | Playwright | fluxos principais no navegador | stack completa via Docker Compose |

Banco de teste: banco `marmitex_test` separado; migrations aplicadas uma vez por sessão; cada teste roda em transação revertida ao final. Relógio do negócio fixado via `core/clock.py` (ex.: hoje = 2026-09-30) para testes determinísticos.

Comandos (definidos na Fase 1):

```bash
# backend
cd backend && pytest                      # todos
cd backend && pytest tests/unit           # só unitários
cd backend && ruff check . && mypy app

# frontend
cd frontend && npm run test               # Vitest
cd frontend && npm run lint && npm run typecheck
cd frontend && npm run e2e                # Playwright
```

Meta de cobertura: ≥ 90% em `financial_engine.py` e `periods.py` (100% de ramos de divisão por zero); ≥ 80% no backend como um todo.

---

## 2. Motor financeiro — cenários obrigatórios

Base de dados de referência: `FINANCIAL-RULES.md`, seção 7. Hoje fixado em 30/09/2026. Os cenários são testados **duas vezes**: (a) unitário, chamando o motor com agregados; (b) integração, inserindo vendas/custos e chamando `GET /dashboard/summary` e `/dashboard/daily`.

| # | Cenário | Entrada | Resultado esperado |
|---|---|---|---|
| FIN-01 | Um dia | `period=custom` 30/09–30/09 | RECEITA 185.00; QTD 10; CT 33.33; LUCRO 151.67; CMM 3.33 |
| FIN-02 | Semana | `period=week` (hoje 30/09/2026, quarta → 28/09–30/09) | só vendas/custos de 28/09 a 30/09: RECEITA 185.00; CT 33.33 |
| FIN-03 | Mês | `period=month` (01/09–30/09) | RECEITA 1425.00; QTD 75; CD 433.33; CF 300.00; CT 733.33; LUCRO 691.67; CMM 9.78; TM 475.00 |
| FIN-04 | Período personalizado | 01/09–15/09 | RECEITA 1240.00; QTD 65; CT 700.00; LUCRO 540.00; CMM 10.77 |
| FIN-05 | Período inclusivo nas bordas | 01/09–30/09 inclui vendas de 01/09 e 30/09; 02/09–29/09 exclui ambas | RECEITA 1425.00 vs. 500.00 |
| FIN-06 | Empresa | empresa A, mês | RECEITA 925.00; QTD 50; TM 462.50; custo alocado 488.89; lucro estimado 436.11; `net_profit` null |
| FIN-07 | Várias empresas | A + B, mês | RECEITA 1425.00; QTD 75; custo alocado 733.33; lucro estimado 691.67 |
| FIN-08 | Sem vendas | só custos, 05/09–05/09 | RECEITA 0.00; QTD 0; CT 300.00; LUCRO −300.00; CMM null; TM null |
| FIN-09 | Sem custos | só vendas, 15/09–15/09 | RECEITA 500.00; CT 0.00; LUCRO 500.00; CMM 0.00 |
| FIN-10 | Sem vendas e sem custos | 02/09–04/09 | todos os totais 0.00; CMM null; TM null; série diária com 3 dias zerados |
| FIN-11 | Divisão por zero | QTD = 0 e NV = 0 em todas as médias, inclusive rateio por empresa e `share_percent` | nenhum erro; campos `null`; `allocation_available=false` |
| FIN-12 | Somente custos fixos | só Aluguel 300.00 + venda 15/09 (500.00, 25) | CF 300.00; CD 0.00; CT 300.00; CMM 12.00 |
| FIN-13 | Somente custos diários | só Ingredientes 400.00 + venda 01/09 (740.00, 40) | CD 400.00; CF 0.00; CT 400.00; CMM 10.00; LUCRO 340.00 |
| FIN-14 | Vendas sem custos | igual FIN-09 em período maior | LUCRO = RECEITA |
| FIN-15 | Custos sem vendas | igual FIN-08 em período maior | LUCRO = −CT; CMM null |
| FIN-16 | Arredondamento | CT 10.00, QTD 3 → 3.333… ; CT 10.00, QTD 6 → 1.6666… ; CT 0.05, QTD 2 → 0.025 | 3.33 ; 1.67 ; 0.03 (ROUND_HALF_UP) |
| FIN-17 | Subtotal exato | 18.50 × 40; 0.01 × 10000; 9999.99 × 10000 | 740.00; 100.00; 99999900.00 |
| FIN-18 | Exclusão lógica | venda/custo excluído | não entra em nenhum total |
| FIN-19 | Consistência da série | qualquer período | Σ diária de receita, quantidade, CD, CF = totais do resumo |
| FIN-20 | Fuso horário | relógio às 23:30 de 30/09 em São Paulo (02:30 UTC de 01/10) | venda registrada com `sale_date = 2026-09-30` |
| FIN-21 | Lucro negativo | custos > receita | LUCRO negativo exato, sem arredondamento |
| FIN-22 | Precisão | 1.000 vendas de 0.01 | RECEITA 10.00 exato (sem erro de ponto flutuante) |

Conferência de FIN-04: vendas 01/09 (740.00, 40) e 15/09 (500.00, 25) → 1240.00 e 65; custos 400.00 + 300.00 = 700.00; CMM = 700.00 ÷ 65 = 10.769… → 10.77.

Teste de propriedade (Hypothesis): para listas aleatórias de vendas/custos, verificar `LUCRO = RECEITA − CT`, `CT = CF + CD`, Σ diária = total, e que nenhuma combinação gera exceção de divisão.

---

## 3. Vendas

| # | Caso | Esperado |
|---|---|---|
| VEN-01 | Criar venda válida | 201; `sale_date` = hoje do servidor; subtotal calculado; auditoria `CREATE` |
| VEN-02 | Cliente envia `sale_date`/`subtotal` | 422 |
| VEN-03 | Preço 0, negativo, 3 casas decimais, > 9999.99 | 422 |
| VEN-04 | Quantidade 0, negativa, fracionária, > 10000 | 422 |
| VEN-05 | Empresa inexistente / inativa | 422 com campo `company_id` |
| VEN-06 | Cliente inexistente / inativo / de outra empresa | 422 com campo `customer_id` |
| VEN-07 | Editar preço/quantidade | subtotal recalculado; `version` incrementada; auditoria com antes/depois |
| VEN-08 | Editar com `version` antiga | 409 `VERSION_CONFLICT` |
| VEN-09 | OPERADOR edita venda de outro usuário ou de dia anterior | 403 |
| VEN-10 | GERENTE tenta alterar `sale_date` | 403; ADMIN consegue (não futura) |
| VEN-11 | Excluir venda | 204; some de listagens e totais; auditoria `DELETE` |
| VEN-12 | Manter empresa desativada após a venda ao editar só a quantidade | 200 (R-VEN-7) |

## 4. Custos

| # | Caso | Esperado |
|---|---|---|
| CUS-01 | Criar custo sem data | 201; `cost_date` = hoje |
| CUS-02 | Criar custo com data passada (GERENTE) | 201 |
| CUS-03 | Data futura | 422 |
| CUS-04 | OPERADOR com data diferente de hoje | 403 |
| CUS-05 | Valor 0, negativo, 3 casas | 422 |
| CUS-06 | Categoria inexistente / inativa | 422 |
| CUS-07 | Tipo diferente do tipo da categoria / tipo inválido | 422 |
| CUS-08 | Editar e excluir com auditoria e `version` | igual vendas |

## 5. Cadastros

| # | Caso | Esperado |
|---|---|---|
| CAD-01 | Criar/editar empresa válida | 201/200; auditoria |
| CAD-02 | Nome duplicado (case-insensitive) / CNPJ duplicado | 409 |
| CAD-03 | CNPJ com dígito verificador inválido | 422 |
| CAD-04 | Desativar/ativar empresa | some/volta em `?active=true` e em `customers?for_entry=true` |
| CAD-05 | Pesquisa `q` por nome, nome fantasia e CNPJ | resultados corretos, paginados |
| CAD-06 | Cliente em empresa inativa | criação 422 |
| CAD-07 | Nome de cliente duplicado na mesma empresa | 409; em empresas diferentes, permitido |
| CAD-08 | Categoria: criar, editar, ativar, desativar, pesquisar | ok |
| CAD-09 | Alterar `cost_type` de categoria com custos | 409 |
| CAD-10 | Seed: 10 categorias padrão com tipos corretos | presentes após migrations |

## 6. Autenticação, autorização e auditoria

| # | Caso | Esperado |
|---|---|---|
| AUT-01 | Login válido | 200 com token; `LOGIN_SUCCESS` auditado; `last_login_at` atualizado |
| AUT-02 | Senha errada / e-mail inexistente | 401 com a **mesma** mensagem; `LOGIN_FAILED` |
| AUT-03 | 6ª falha em 15 min | 429 |
| AUT-04 | Usuário inativo | 401 |
| AUT-05 | Token expirado / assinatura inválida / ausente | 401 |
| AUT-06 | Logout e reutilização do token | 204, depois 401 |
| AUT-07 | Desativar usuário revoga sessões | próximo request 401 |
| AUT-08 | Matriz de permissões | para cada rota × papel, 2xx ou 403 conforme `API.md` seção 2 (teste parametrizado) |
| AUT-09 | Senha armazenada | hash Argon2id; nunca aparece em respostas, logs ou auditoria |
| AUD-01 | Toda criação/edição/ativação/desativação/exclusão | gera 1 registro de auditoria com usuário, entidade, antes/depois |
| AUD-02 | Falha da operação | nenhuma auditoria gravada (mesma transação) |
| AUD-03 | `/audit-logs` | somente ADMIN; filtros e paginação |

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
| HIS-02 | Filtros empresa/cliente | só vendas |
| HIS-03 | Filtros de data inclusivos e `totals` | corretos |
| DSH-01 | `period` inválido; `custom` sem datas; início > fim; > 366 dias na série | 422 |
| DSH-02 | `/dashboard/companies/{id}` | receita, qtd, ticket, clientes, vendas recentes, comparação com período anterior |
| DSH-03 | `revenue-by-company` | ordenado, `share_percent` soma ≈ 100 (tolerância de arredondamento) |

## 8. Frontend

| # | Caso |
|---|---|
| FE-01 | Rotas protegidas redirecionam para `/login` sem sessão; após login voltam à rota pedida |
| FE-02 | Menu e botões respeitam `permissions` de `/auth/me` |
| FE-03 | Formulários exibem erros por campo vindos de `error.details` |
| FE-04 | Selects de lançamento só listam empresas/clientes/categorias ativos |
| FE-05 | Formatação: `"1234.5"` → `R$ 1.234,50`; `"2026-09-01"` → `01/09/2026`; `null` → "—" |
| FE-06 | Nenhum cálculo financeiro no frontend (revisão de código + teste: valores exibidos = valores da API simulada) |
| FE-07 | Dashboard: filtros na URL; estados vazio/carregando/erro |
| FE-08 | Conflito de versão (409) mostra mensagem e recarrega o registro |

## 9. E2E (Playwright)

1. Login como ADMIN → criar empresa → criar cliente → lançar venda → ver no histórico → ver no dashboard (receita e quantidade).
2. Lançar custo diário e fixo → dashboard mostra custos, lucro e custo médio iguais aos da API.
3. Desativar empresa → ela não aparece em novo lançamento, mas continua no histórico e no dashboard.
4. Login como OPERADOR → não vê Dashboard nem Usuários; acesso direto à URL é bloqueado.
5. Logout → token invalidado.

## 10. Não funcionais (Fase 5)

* Performance: seed com 100 mil vendas em 1 ano; `/dashboard/summary` e `/dashboard/daily` (366 dias) < 500 ms no p95.
* Concorrência: duas edições simultâneas da mesma venda → uma 200 e uma 409.
* Segurança: varredura de secrets no repositório; dependências sem vulnerabilidades críticas conhecidas; cabeçalhos de segurança presentes.
* Backup: gerar dump, restaurar em banco limpo e conferir totais do dashboard.

## 11. Regra de execução

* Antes de cada commit de fase: executar todos os testes do backend e do frontend.
* Testes falhando bloqueiam a conclusão da fase.
* Resultado (comando, total, falhas) registrado em `PROJECT-STATE.md`, seção "Testes da última sessão".
