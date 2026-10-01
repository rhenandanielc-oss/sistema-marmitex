# PROJECT-STATE.md

# Sistema de Gestão de Vendas B2B de Marmitex e Controle Financeiro

Este arquivo representa o estado atual do projeto.

O Claude Code deve atualizá-lo ao final de cada etapa significativa.

---

# STATUS GERAL

**Status:** NÃO INICIADO

**Fase atual:** Fase 0 — Arquitetura

**Última atualização:** A preencher.

**Último commit:** A preencher.

**Próxima ação:** Criar a documentação arquitetural inicial.

---

# FASE 0 — ARQUITETURA

**Status:** PENDENTE

### Entregáveis

* [ ] `ARCHITECTURE.md`
* [ ] `DATABASE.md`
* [ ] `API.md`
* [ ] `FINANCIAL-RULES.md`
* [ ] `DASHBOARD.md`
* [ ] `TEST-PLAN.md`

### Testes

Ainda não executados.

### Decisões

Nenhuma.

---

# FASE 1 — BANCO, AUTENTICAÇÃO E CADASTROS

**Status:** PENDENTE

### Banco

* [ ] PostgreSQL
* [ ] Docker
* [ ] migrations
* [ ] modelos
* [ ] relacionamentos
* [ ] constraints
* [ ] índices

### Autenticação

* [ ] usuários
* [ ] login
* [ ] logout
* [ ] sessões/tokens
* [ ] papéis
* [ ] permissões
* [ ] auditoria

### Cadastros

#### Empresas

* [ ] criar
* [ ] editar
* [ ] ativar
* [ ] desativar
* [ ] pesquisar
* [ ] filtrar

#### Clientes

* [ ] criar
* [ ] editar
* [ ] ativar
* [ ] desativar
* [ ] pesquisar
* [ ] filtrar

#### Categorias

* [ ] criar
* [ ] editar
* [ ] ativar
* [ ] desativar
* [ ] pesquisar

### Testes

Pendente.

---

# FASE 2 — VENDAS, CUSTOS E MOTOR FINANCEIRO

**Status:** PENDENTE

### Vendas

* [ ] empresa
* [ ] cliente
* [ ] preço unitário
* [ ] quantidade
* [ ] data do servidor
* [ ] subtotal
* [ ] validações
* [ ] edição
* [ ] auditoria

### Custos

* [ ] valor
* [ ] categoria
* [ ] tipo
* [ ] data
* [ ] validações
* [ ] auditoria

### Tipos de custo

* [ ] `CUSTO_DIARIO`
* [ ] `CUSTO_FIXO`

### Categorias

#### Diários

* [ ] Ingredientes
* [ ] Embalagens
* [ ] Entregas
* [ ] Equipamentos
* [ ] Gasolina

#### Fixos

* [ ] Salários
* [ ] Aluguel
* [ ] Água
* [ ] Energia elétrica
* [ ] Gás

---

# MOTOR FINANCEIRO

### Regras

* [ ] receita
* [ ] custos totais
* [ ] lucro líquido
* [ ] custo médio por marmita
* [ ] divisão por zero
* [ ] período inclusivo
* [ ] filtro por empresa

### Fórmulas

`RECEITA = soma dos subtotais`

`CUSTOS_TOTAIS = custos fixos + custos diários`

`LUCRO_LIQUIDO = receita - custos totais`

`CUSTO_MEDIO_POR_MARMITA = custos totais / quantidade de marmitas`

### Testes

* [ ] dia
* [ ] semana
* [ ] mês
* [ ] período personalizado
* [ ] empresa
* [ ] várias empresas
* [ ] sem vendas
* [ ] sem custos
* [ ] sem vendas e sem custos
* [ ] divisão por zero
* [ ] somente custos fixos
* [ ] somente custos diários
* [ ] vendas sem custos
* [ ] custos sem vendas

---

# FASE 3 — API

**Status:** PENDENTE

### Endpoints

* [ ] autenticação
* [ ] empresas
* [ ] clientes
* [ ] categorias
* [ ] vendas
* [ ] custos
* [ ] histórico
* [ ] dashboard

### Dashboard

* [ ] resumo financeiro
* [ ] vendas diárias
* [ ] vendas por empresa
* [ ] quantidade diária
* [ ] custos diários
* [ ] lucro diário
* [ ] histórico por empresa

### Recursos

* [ ] filtros
* [ ] paginação
* [ ] ordenação
* [ ] tratamento de erros
* [ ] autorização
* [ ] OpenAPI
* [ ] testes de integração

---

# FASE 4 — FRONTEND

**Status:** PENDENTE

### Rotas

* [ ] `/login`
* [ ] `/cadastros/empresas`
* [ ] `/cadastros/clientes`
* [ ] `/cadastros/categorias`
* [ ] `/lancamentos/vendas`
* [ ] `/lancamentos/custos`
* [ ] `/historico`
* [ ] `/dashboard`

### Funcionalidades

* [ ] login
* [ ] empresas
* [ ] clientes
* [ ] categorias
* [ ] vendas
* [ ] custos
* [ ] histórico
* [ ] dashboard
* [ ] dashboard por empresa

---

# HISTÓRICO

### Filtros

* [ ] empresa
* [ ] cliente
* [ ] data inicial
* [ ] data final
* [ ] tipo

### Vendas

* [ ] data
* [ ] empresa
* [ ] cliente
* [ ] quantidade
* [ ] preço
* [ ] subtotal

### Custos

* [ ] data
* [ ] categoria
* [ ] tipo
* [ ] valor

### Recursos

* [ ] paginação
* [ ] ordenação
* [ ] filtros

---

# DASHBOARD

### Indicadores

* [ ] Receita Total
* [ ] Custos Fixos
* [ ] Custos Diários
* [ ] Custos Totais
* [ ] Lucro Líquido
* [ ] Quantidade de Marmitas
* [ ] Custo Médio por Marmita

### Gráficos

* [ ] receita diária
* [ ] quantidade diária
* [ ] receita por empresa
* [ ] receita total
* [ ] custos diários
* [ ] lucro diário
* [ ] histórico de vendas por empresa

### Filtros

* [ ] hoje
* [ ] semana
* [ ] mês
* [ ] período personalizado
* [ ] empresa

---

# DASHBOARD POR EMPRESA

**Status:** PENDENTE

* [ ] selecionar empresa
* [ ] receita
* [ ] quantidade
* [ ] ticket médio
* [ ] histórico diário
* [ ] clientes
* [ ] vendas
* [ ] evolução do período

---

# FASE 5 — AUDITORIA E PRODUÇÃO

**Status:** PENDENTE

### Auditoria

* [ ] banco
* [ ] API
* [ ] frontend
* [ ] autenticação
* [ ] autorização
* [ ] filtros
* [ ] datas
* [ ] valores monetários
* [ ] arredondamento
* [ ] concorrência
* [ ] auditoria
* [ ] performance

### Produção

* [ ] Dockerfiles
* [ ] configuração de produção
* [ ] migrations
* [ ] `.env.example`
* [ ] health checks
* [ ] logs
* [ ] backup
* [ ] documentação de instalação
* [ ] documentação de deploy

---

# DECISÕES TÉCNICAS

Nenhuma decisão registrada.

Formato:

### [DATA] — [DECISÃO]

**Problema:**
...

**Opções:**
...

**Decisão:**
...

**Motivo:**
...

**Impacto:**
...

---

# REGRAS FINANCEIRAS

As regras oficiais estão em `FINANCIAL-RULES.md`.

Resumo:

* receita é a soma dos subtotais;
* custos totais = custos fixos + custos diários;
* lucro líquido = receita − custos totais;
* custo médio = custos totais ÷ quantidade;
* divisão por zero deve ser tratada;
* períodos são inclusivos;
* cálculos críticos ficam no backend.

---

# SEGURANÇA

* [ ] autenticação
* [ ] autorização
* [ ] proteção de endpoints
* [ ] hash de senha
* [ ] expiração de sessão
* [ ] auditoria
* [ ] `.env`
* [ ] `.env.example`
* [ ] nenhum secret no Git

---

# PROBLEMAS CONHECIDOS

Nenhum problema registrado.

Formato:

### Problema

**Descrição:**
...

**Impacto:**
...

**Status:**
...

**Solução:**
...

---

# RISCOS

Nenhum risco registrado.

Possíveis categorias:

* segurança;
* banco;
* concorrência;
* cálculos;
* arredondamento;
* datas;
* performance;
* disponibilidade.

---

# ÚLTIMAS ALTERAÇÕES

Nenhuma.

Formato:

### [DATA]

* alteração;
* arquivos modificados;
* testes;
* resultado.

---

# TESTES DA ÚLTIMA SESSÃO

**Comando:**
A preencher.

**Resultado:**
A preencher.

**Falhas:**
A preencher.

---

# PRÓXIMA SESSÃO DO CLAUDE CODE

Ao iniciar:

1. Ler `MASTER-PROMPT.md`.
2. Ler este arquivo.
3. Identificar a fase atual.
4. Verificar o código existente.
5. Implementar somente a próxima etapa.
6. Executar testes.
7. Corrigir falhas.
8. Atualizar este arquivo.
9. Informar o resultado resumidamente.

---

# LOG DE SESSÕES

## Sessão 1

**Status:** Não iniciada.

---

# CRITÉRIO DE CONCLUSÃO

O projeto estará concluído quando todas as fases estiverem concluídas e os critérios do `MASTER-PROMPT.md` forem atendidos.

# FIM
