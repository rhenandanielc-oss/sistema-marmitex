# FINANCIAL-RULES.md

# Regras Financeiras Oficiais

Este documento é a **fonte oficial** das regras financeiras. Nenhuma regra pode ser alterada no código sem que este arquivo seja atualizado no mesmo commit, com registro em "Histórico de alterações".

Implementação: `backend/app/services/financial_engine.py` (funções puras) + agregações SQL em `backend/app/repositories/`. O frontend **não** recalcula nenhum valor desta lista.

---

## 1. Representação de valores

| Item | Regra |
|---|---|
| Moeda | Real (BRL), 2 casas decimais |
| Tipo no Python | `decimal.Decimal` — `float` é proibido em valores monetários |
| Tipo no banco | `NUMERIC(12,2)` (lançamentos) / `NUMERIC(14,2)` (subtotal) |
| Tipo no JSON | string decimal com ponto: `"1234.50"` |
| Entrada | aceita string ou número com no máximo 2 casas decimais; mais casas → erro `422` (não arredonda silenciosamente) |
| Arredondamento | `ROUND_HALF_UP` para 2 casas, **somente** no resultado final de divisões (médias). Somas e multiplicações por inteiro são exatas e não arredondam |
| Quantidade | inteiro (marmitas) |

---

## 2. Período

* **R-PER-1** — Todo período é um intervalo **fechado** `[data_inicial, data_final]`: ambos os dias estão incluídos. Ex.: `01/09/2026` a `30/09/2026` inclui os dias 1 e 30.
* **R-PER-2** — `data_inicial ≤ data_final`; caso contrário, erro `422`.
* **R-PER-3** — "Hoje" é a data atual no fuso `APP_TIMEZONE` (padrão `America/Sao_Paulo`), determinada pelo servidor.
* **R-PER-4** — Períodos pré-definidos (resolvidos no backend):

| Período | Data inicial | Data final |
|---|---|---|
| `today` (hoje) | hoje | hoje |
| `week` (semana) | segunda-feira da semana corrente | hoje |
| `month` (mês) | dia 1 do mês corrente | hoje |
| `custom` (personalizado) | informada | informada |

* **R-PER-5** — Período máximo para séries diárias: 366 dias (proteção de performance). Resumos sem série não têm esse limite.
* **R-PER-6** — Uma venda pertence ao dia de `sale_date`; um custo pertence ao dia de `cost_date`.

---

## 3. Venda

* **R-VEN-1** — `SUBTOTAL = PRECO_UNITARIO × QUANTIDADE`, calculado no backend. Valor enviado pelo cliente para `subtotal` é ignorado.
* **R-VEN-2** — `0 < PRECO_UNITARIO ≤ 9999.99`, com no máximo 2 casas decimais.
* **R-VEN-3** — `QUANTIDADE` inteira, `1 ≤ QUANTIDADE ≤ 10000`.
* **R-VEN-4** — A data oficial da venda (`sale_date`) é a data de hoje do servidor no momento da criação. O cliente não envia data.
* **R-VEN-5** — Empresa e cliente devem existir, estar ativos e o cliente deve pertencer à empresa.
* **R-VEN-6** — Na edição, o subtotal é recalculado. A data só pode ser corrigida por `ADMIN`, nunca para o futuro, com auditoria.
* **R-VEN-7** — Ao editar uma venda existente, é permitido manter empresa/cliente que tenham sido desativados depois da venda; trocar para outra empresa/cliente exige que o novo esteja ativo.
* **R-VEN-8** — Vendas excluídas logicamente (`deleted_at` preenchido) não entram em nenhum cálculo.

## 4. Custo

* **R-CUS-1** — `0 < VALOR ≤ 9999999.99`, com no máximo 2 casas decimais.
* **R-CUS-2** — A categoria deve existir e estar ativa (em edição, pode-se manter a categoria atual mesmo se desativada depois).
* **R-CUS-3** — Tipo ∈ {`CUSTO_DIARIO`, `CUSTO_FIXO`} e deve ser igual ao tipo da categoria.
* **R-CUS-4** — Data: se omitida, o servidor usa hoje. Pode ser informada uma data passada (ex.: aluguel do mês lançado depois). Nunca futura.
* **R-CUS-5** — Custos são reconhecidos **integralmente na data `cost_date`** (sem rateio entre dias). Ex.: aluguel de R$ 3.000,00 com data 05/09 aparece inteiro no dia 05/09, na semana e no mês que contêm esse dia.
* **R-CUS-6** — Custos excluídos logicamente não entram em nenhum cálculo.

---

## 5. Indicadores

Para um período `P` (e opcionalmente uma empresa `E`):

| Código | Indicador | Fórmula |
|---|---|---|
| **F-01** | Receita Total | `RECEITA = Σ subtotal` das vendas em `P` (de `E`, se filtrado) |
| **F-02** | Quantidade de Marmitas | `QTD = Σ quantity` das vendas em `P` (de `E`, se filtrado) |
| **F-03** | Custos Diários | `CD = Σ amount` dos custos `CUSTO_DIARIO` em `P` |
| **F-04** | Custos Fixos | `CF = Σ amount` dos custos `CUSTO_FIXO` em `P` |
| **F-05** | Custos Totais | `CT = CF + CD` |
| **F-06** | Lucro Líquido | `LUCRO = RECEITA − CT` (pode ser negativo) |
| **F-07** | Custo Médio por Marmita | `CMM = CT ÷ QTD`, arredondado; **`null` quando `QTD = 0`** |
| **F-08** | Número de Vendas | `NV = quantidade de lançamentos de venda` em `P` |
| **F-09** | Ticket Médio | `TM = RECEITA ÷ NV`, arredondado; **`null` quando `NV = 0`** |
| **F-10** | Preço Médio por Marmita | `PM = RECEITA ÷ QTD`, arredondado; **`null` quando `QTD = 0`** |

Regras gerais:

* **R-IND-1** — Somas sem registros resultam em `0.00` (nunca `null`).
* **R-IND-2** — **Nunca dividir por zero.** Toda divisão verifica o divisor; se zero, o indicador é `null` e a interface exibe "—" com a dica "sem marmitas no período" / "sem vendas no período".
* **R-IND-3** — Arredondamento apenas no resultado final das divisões (F-07, F-09, F-10, F-12). Lucro e totais são exatos.
* **R-IND-4** — Séries diárias aplicam as mesmas fórmulas a cada dia isoladamente. Dias sem movimento aparecem com zeros (e `null` para médias).
* **R-IND-5** — A soma dos valores diários de receita, quantidade e custos é igual ao total do período (propriedade testada).

---

## 6. Filtro por empresa e custos

Custos não estão vinculados a empresas. Por isso, quando o filtro de empresa é aplicado:

* **R-EMP-1** — Receita, quantidade, número de vendas, ticket médio e preço médio são calculados **somente com as vendas da empresa**.
* **R-EMP-2** — Os custos do período continuam sendo os **custos globais** (F-03, F-04, F-05 sem filtro) e são retornados em um bloco separado identificado como `global_costs`.
* **R-EMP-3** — O custo atribuído à empresa é obtido por **rateio proporcional à quantidade de marmitas**:

  * **F-11** — `CUSTO_ALOCADO_EMPRESA = CT_global × (QTD_empresa ÷ QTD_global)`, arredondado ao final; se `QTD_global = 0`, o custo alocado é `0.00` e é sinalizado `allocation_available = false`.
  * **F-12** — `CMM_global = CT_global ÷ QTD_global` (o custo médio por marmita é o mesmo para todas as empresas).
  * **F-13** — `LUCRO_ESTIMADO_EMPRESA = RECEITA_empresa − CUSTO_ALOCADO_EMPRESA`.

* **R-EMP-4** — O lucro por empresa é rotulado na interface como **"Lucro estimado (rateio por marmita)"**, nunca como lucro líquido. O **Lucro Líquido** oficial (F-06) é sempre global.
* **R-EMP-5** — Filtro com várias empresas: a receita/quantidade é a soma das empresas selecionadas; o custo alocado é a soma dos custos alocados de cada uma (equivalente a `CT × QTD_sel ÷ QTD_global`, calculado sobre a soma para evitar acúmulo de arredondamento).
* **R-EMP-6** — Na série diária com filtro de empresa, o rateio é feito **dia a dia** (`CT_dia × QTD_empresa_dia ÷ QTD_global_dia`). Por isso a soma dos custos alocados diários pode diferir do custo alocado do período (custos de dias sem vendas não são alocados no dia). O valor oficial do período é sempre o do resumo (F-11), e a interface informa isso no gráfico.

> **Decisão pendente de validação pelo negócio:** o rateio proporcional à quantidade (R-EMP-3) foi adotado por ser simples e coerente com o "custo médio por marmita". Alternativas: ratear pela receita, ou não exibir lucro por empresa. Ver `PROJECT-STATE.md`, seção "Decisões técnicas".

---

## 7. Exemplos de referência (usados nos testes)

Período 01/09/2026 a 30/09/2026.

Vendas:

| Data | Empresa | Preço | Qtd | Subtotal |
|---|---|---|---|---|
| 01/09 | A | 18.50 | 40 | 740.00 |
| 15/09 | B | 20.00 | 25 | 500.00 |
| 30/09 | A | 18.50 | 10 | 185.00 |

Custos:

| Data | Categoria | Tipo | Valor |
|---|---|---|---|
| 01/09 | Ingredientes | CUSTO_DIARIO | 400.00 |
| 05/09 | Aluguel | CUSTO_FIXO | 300.00 |
| 30/09 | Embalagens | CUSTO_DIARIO | 33.33 |

Resultado global:

* RECEITA = 740.00 + 500.00 + 185.00 = **1425.00**
* QTD = 75
* CD = 433.33; CF = 300.00; CT = **733.33**
* LUCRO = 1425.00 − 733.33 = **691.67**
* CMM = 733.33 ÷ 75 = 9.777733… → **9.78**
* NV = 3; TM = 1425.00 ÷ 3 = **475.00**
* PM = 1425.00 ÷ 75 = **19.00**

Empresa A:

* RECEITA_A = 925.00; QTD_A = 50; NV_A = 2; TM_A = 462.50; PM_A = 18.50
* CUSTO_ALOCADO_A = 733.33 × 50 ÷ 75 = 488.886666… → **488.89**
* LUCRO_ESTIMADO_A = 925.00 − 488.89 = **436.11**

Período inclusivo: 30/09 a 30/09 → RECEITA = 185.00, QTD = 10, CT = 33.33, LUCRO = 151.67, CMM = 3.33.

Sem vendas e sem custos (ex.: 02/09 a 04/09): RECEITA = 0.00, CT = 0.00, LUCRO = 0.00, CMM = `null`, TM = `null`.

Custos sem vendas (05/09 a 05/09): RECEITA = 0.00, CT = 300.00, LUCRO = −300.00, CMM = `null`.

---

## 8. Histórico de alterações

| Data | Alteração | Autor |
|---|---|---|
| 2026-10-02 | Versão inicial das regras (Fase 0) | Claude Code |
