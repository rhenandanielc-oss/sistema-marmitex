# MASTER-PROMPT.md

# Sistema de Gestão de Vendas B2B de Marmitex e Controle Financeiro

## 1. Objetivo

Construir um sistema web profissional para gerenciamento de vendas B2B de marmitex e controle financeiro.

O sistema deverá controlar:

* empresas contratantes;
* clientes;
* categorias de custos;
* vendas;
* custos;
* histórico;
* dashboard financeiro;
* lucro;
* custo médio por marmita.

O projeto deverá ser desenvolvido de forma incremental, segura, testável e preparada para produção.

O repositório é a fonte de verdade do projeto.

---

# 2. Regra principal de execução

Antes de executar alterações:

1. Ler `MASTER-PROMPT.md`.
2. Ler `PROJECT-STATE.md`.
3. Ler somente a documentação e código necessários à etapa atual.
4. Identificar a próxima fase pendente.
5. Implementar somente essa fase.
6. Executar testes.
7. Corrigir problemas.
8. Atualizar `PROJECT-STATE.md`.
9. Não reimplementar funcionalidades já concluídas.
10. Não alterar regras financeiras sem documentar.

---

# 3. Áreas do sistema

O sistema deverá possuir quatro áreas principais:

## Cadastros

* empresas contratantes;
* clientes;
* categorias de custos.

## Lançamentos

* vendas;
* custos.

## Banco de Dados / Histórico

* consultas;
* filtros;
* paginação;
* histórico.

## Dashboard

* receitas;
* custos;
* lucro;
* quantidade de marmitas;
* custo médio;
* histórico por empresa;
* evolução por período.

---

# 4. Stack

## Frontend

* React
* TypeScript
* Vite
* Tailwind CSS
* React Router
* React Query

## Backend

* Python
* FastAPI

## Banco

* PostgreSQL

## Infraestrutura

* Docker
* Git
* GitHub

---

# 5. Documentação obrigatória

Criar e manter:

* `ARCHITECTURE.md`
* `DATABASE.md`
* `API.md`
* `FINANCIAL-RULES.md`
* `DASHBOARD.md`
* `TEST-PLAN.md`
* `PROJECT-STATE.md`

A documentação deve refletir o código real.

---

# 6. Banco de dados

Entidades principais:

* usuários;
* empresas;
* clientes;
* vendas;
* custos;
* categorias de custos;
* auditoria.

### Venda

Deve possuir pelo menos:

* empresa;
* cliente;
* data;
* preço unitário;
* quantidade;
* subtotal.

O subtotal deve ser calculado no backend:

`subtotal = preço_unitário × quantidade`

### Custo

Deve possuir:

* valor;
* categoria;
* tipo;
* data.

Tipos:

* `CUSTO_DIARIO`
* `CUSTO_FIXO`

---

# 7. Categorias de custos

## Custos diários

* Ingredientes
* Embalagens
* Entregas
* Equipamentos
* Gasolina

## Custos fixos

* Salários
* Aluguel
* Água
* Energia elétrica
* Gás

As categorias devem ser administráveis pelo sistema.

---

# 8. Cadastros

## Empresas

Permitir:

* criar;
* editar;
* ativar;
* desativar;
* pesquisar;
* filtrar;
* validar.

## Clientes

Permitir:

* criar;
* editar;
* ativar;
* desativar;
* pesquisar;
* filtrar;
* validar.

## Categorias

Permitir:

* criar;
* editar;
* ativar;
* desativar;
* pesquisar.

Empresas e clientes inativos não devem aparecer em novos lançamentos.

---

# 9. Vendas

Permitir lançamento de:

* empresa;
* cliente;
* preço unitário;
* quantidade.

A data oficial deve vir do servidor.

Calcular automaticamente:

`subtotal = unit_price × quantity`

O backend deve validar:

* empresa;
* cliente;
* preço;
* quantidade;
* data;
* empresa ativa;
* cliente ativo.

Permitir edição somente conforme as permissões.

Operações relevantes devem possuir auditoria.

---

# 10. Custos

Permitir:

* valor;
* categoria;
* tipo;
* data.

A data deve ser determinada pelo servidor quando o lançamento representar a data atual.

Validar:

* valor positivo;
* categoria existente;
* categoria ativa;
* tipo válido.

---

# 11. Regras financeiras

As regras devem estar documentadas em `FINANCIAL-RULES.md`.

## Receita

`RECEITA = soma dos subtotais das vendas`

## Custos totais

`CUSTOS_TOTAIS = custos fixos + custos diários`

## Lucro líquido

`LUCRO_LIQUIDO = RECEITA - CUSTOS_TOTAIS`

## Custo médio por marmita

`CUSTO_MEDIO_POR_MARMITA = CUSTOS_TOTAIS / QUANTIDADE_DE_MARMITAS`

Nunca realizar divisão por zero.

Todos os períodos devem ser inclusivos.

Exemplo:

`01/09/2026 até 30/09/2026`

inclui os dois dias.

Os cálculos devem acontecer no backend.

O frontend apenas apresenta os valores retornados.

---

# 12. Cenários financeiros obrigatórios

Testar:

* um dia;
* semana;
* mês;
* período personalizado;
* empresa;
* várias empresas;
* sem vendas;
* sem custos;
* sem vendas e sem custos;
* divisão por zero;
* custos somente fixos;
* custos somente diários;
* vendas sem custos;
* custos sem vendas.

---

# 13. API

Criar endpoints para:

* autenticação;
* empresas;
* clientes;
* categorias;
* vendas;
* custos;
* histórico;
* dashboard.

Dashboard deverá fornecer dados para:

* resumo financeiro;
* vendas diárias;
* vendas por empresa;
* quantidade diária de marmitas;
* custos diários;
* lucro diário;
* histórico de empresa.

Permitir filtros por:

* período;
* empresa.

A API deve possuir:

* validação;
* paginação;
* filtros;
* ordenação;
* erros padronizados;
* autenticação;
* autorização;
* documentação OpenAPI;
* testes de integração.

---

# 14. Frontend

Rotas:

* `/login`
* `/cadastros/empresas`
* `/cadastros/clientes`
* `/cadastros/categorias`
* `/lancamentos/vendas`
* `/lancamentos/custos`
* `/historico`
* `/dashboard`

Interface em português.

Priorizar:

* simplicidade;
* clareza;
* rapidez;
* desktop/notebook;
* validação;
* feedback ao usuário.

---

# 15. Histórico

Filtros:

* empresa;
* cliente;
* data inicial;
* data final;
* tipo.

Vendas devem mostrar:

* data;
* empresa;
* cliente;
* quantidade;
* preço;
* subtotal.

Custos devem mostrar:

* data;
* categoria;
* tipo;
* valor.

Implementar:

* paginação;
* ordenação;
* filtros;
* visualização consistente.

---

# 16. Dashboard

Indicadores:

* Receita Total;
* Custos Fixos;
* Custos Diários;
* Custos Totais;
* Lucro Líquido;
* Quantidade de Marmitas;
* Custo Médio por Marmita.

Gráficos:

* receita diária;
* quantidade diária;
* receita por empresa;
* receita total;
* custos diários;
* lucro diário;
* histórico de vendas por empresa.

Filtros:

* hoje;
* semana;
* mês;
* período personalizado;
* empresa.

Nenhum cálculo financeiro crítico deve ser duplicado no frontend.

---

# 17. Dashboard detalhado por empresa

Permitir selecionar uma empresa.

Mostrar:

* receita;
* quantidade de marmitas;
* ticket médio;
* histórico diário;
* clientes;
* vendas;
* evolução no período.

O período deve ser configurável.

Os valores devem vir do backend.

---

# 18. Autenticação e autorização

Implementar:

* usuários;
* login;
* logout;
* sessão/token;
* papéis;
* permissões;
* proteção de endpoints;
* auditoria.

Rotas administrativas devem ser protegidas.

---

# 19. Segurança

Nunca colocar no Git:

* senhas;
* tokens;
* API keys;
* credenciais;
* chaves privadas;
* dados reais de clientes.

Utilizar `.env`.

Criar `.env.example`.

---

# 20. Auditoria

Registrar ações relevantes, incluindo quando aplicável:

* login;
* criação;
* edição;
* exclusão lógica;
* alteração de vendas;
* alteração de custos;
* alterações administrativas.

---

# 21. Auditoria técnica

Antes da produção revisar:

* banco;
* API;
* frontend;
* autenticação;
* autorização;
* filtros;
* datas;
* valores monetários;
* arredondamento;
* concorrência;
* auditoria;
* performance.

Executar todos os testes.

Não alterar regras financeiras sem atualizar `FINANCIAL-RULES.md`.

---

# 22. Produção

Preparar:

* Dockerfiles;
* configuração de produção;
* migrations;
* `.env.example`;
* health checks;
* logs;
* backup;
* documentação de instalação;
* documentação de deploy.

---

# 23. Git

Criar commits por etapa significativa.

Exemplos:

`feat: create database models`

`feat: implement authentication`

`feat: implement sales`

`feat: implement cost management`

`feat: implement financial engine`

`feat: implement dashboard`

`test: add financial calculation tests`

`fix: prevent invalid financial calculation`

Nunca realizar commit de secrets.

---

# 24. PROJECT-STATE.md

Atualizar após cada etapa:

* status;
* funcionalidades concluídas;
* arquivos importantes;
* testes;
* problemas;
* decisões;
* próxima etapa.

Esse arquivo deve permitir continuar o projeto em uma nova sessão sem reenviar os prompts antigos.

---

# 25. Fases

## Fase 0 — Arquitetura

Criar:

* `ARCHITECTURE.md`
* `DATABASE.md`
* `API.md`
* `FINANCIAL-RULES.md`
* `DASHBOARD.md`
* `TEST-PLAN.md`

Ainda não implementar a aplicação completa.

---

## Fase 1 — Banco, autenticação e cadastros

Implementar:

* PostgreSQL;
* Docker;
* migrations;
* modelos;
* usuários;
* autenticação;
* autorização;
* empresas;
* clientes;
* categorias.

---

## Fase 2 — Vendas, custos e motor financeiro

Implementar:

* vendas;
* custos;
* cálculos;
* receita;
* custos;
* lucro;
* custo médio;
* filtros de período;
* empresa.

Criar testes extensivos.

---

## Fase 3 — API

Implementar:

* endpoints;
* filtros;
* paginação;
* ordenação;
* dashboard;
* histórico;
* OpenAPI;
* integração.

---

## Fase 4 — Frontend

Implementar:

* login;
* cadastros;
* vendas;
* custos;
* histórico;
* dashboard;
* dashboard por empresa.

---

## Fase 5 — Auditoria e produção

Executar:

* auditoria;
* testes;
* segurança;
* performance;
* Docker;
* backup;
* deploy;
* documentação.

---

# 26. Critério de conclusão

O projeto somente estará concluído quando:

* banco estiver funcionando;
* migrations estiverem funcionando;
* autenticação estiver funcionando;
* cadastros estiverem funcionando;
* vendas estiverem funcionando;
* custos estiverem funcionando;
* cálculos financeiros estiverem testados;
* histórico estiver funcionando;
* dashboard estiver funcionando;
* dashboard por empresa estiver funcionando;
* auditoria estiver implementada;
* testes estiverem passando;
* documentação estiver atualizada;
* produção estiver documentada;
* `PROJECT-STATE.md` estiver atualizado.

# FIM
