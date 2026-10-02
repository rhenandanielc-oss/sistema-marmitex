# FINANCIAL-RULES.md

# Regras Financeiras Oficiais

Este documento é a **fonte oficial** das regras financeiras. Nenhuma regra pode ser alterada no código sem que este arquivo seja atualizado no mesmo commit, com registro em "Histórico de alterações".

Implementação: `backend/app/services/financial_engine.py` (funções puras) + agregações SQL em `backend/app/repositories/`. O frontend **não** recalcula nenhum valor desta lista.

---

## 0. Conceitos

| Termo | Significado |
|---|---|
| **Empresa** | empreiteira; principal compradora, maior volume, faturamento quinzenal/mensal |
| **Cliente avulso** | pessoa que compra por conta própria, independente das empresas (ex.: trabalhador da obra que paga mensalmente) |
| **Comprador** | quem recebe a venda: uma empresa **ou** um cliente avulso (nunca os dois) |
| **Custo** | despesa do restaurante (ingredientes, embalagens, aluguel...), não vinculada a comprador |
| **Categoria de custo** | tipo de custo cadastrável pelo ADMIN (ex.: "Embalagens"), classificado como diário ou fixo |

---

## 1. Representação de valores

| Item | Regra |
|---|---|
| Moeda | Real (BRL), 2 casas decimais |
| Tipo no Python | `decimal.Decimal` — `float` é proibido em valores monetários |
| Tipo no banco | `NUMERIC(12,2)` (lançamentos) / `NUMERIC(14,2)` (subtotal) |
| Tipo no JSON | string decimal com ponto: `"1234.50"` |
| Entrada | aceita string ou número com no máximo 2 casas decimais; mais casas → erro `422` (não arredonda silenciosamente) |
| Arredondamento | `ROUND_HALF_UP` para 2 casas, **somente** no resultado final de divisões (médias, percentuais). Somas e multiplicações por inteiro são exatas. O rateio de custos usa o método do maior resto (seção 6) para fechar exatamente no centavo |
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
| `month` (mês) — **padrão** | dia 1 do mês corrente | hoje |
| `last_month` (mês anterior) | dia 1 do mês anterior | último dia do mês anterior |
| `custom` (personalizado) | informada | informada |

* **R-PER-5** — Período máximo para séries diárias: 366 dias (proteção de performance). Resumos sem série não têm esse limite.
* **R-PER-6** — Uma venda pertence ao dia de `sale_date`; um custo pertence ao dia de `cost_date`.

---

## 3. Venda

* **R-VEN-1** — `SUBTOTAL = PRECO_UNITARIO × QUANTIDADE`, calculado no backend. Valor enviado para `subtotal` é rejeitado.
* **R-VEN-2** — `0 < PRECO_UNITARIO ≤ 9999.99`, com no máximo 2 casas decimais.
* **R-VEN-3** — `QUANTIDADE` inteira, `1 ≤ QUANTIDADE ≤ 10000`.
* **R-VEN-4** — Data: o ADMIN escolhe a data da venda (para lançar vendas esquecidas). Se omitida, o servidor usa hoje. Nunca pode ser futura. Toda alteração de data é auditada.
* **R-VEN-5** — Comprador: exatamente um entre empresa e cliente avulso. O comprador deve existir e estar ativo.
* **R-VEN-6** — Na edição, o subtotal é recalculado.
* **R-VEN-7** — Ao editar uma venda existente, é permitido manter um comprador que tenha sido desativado depois da venda; trocar para outro comprador exige que o novo esteja ativo.
* **R-VEN-8** — Vendas excluídas logicamente (`deleted_at` preenchido) não entram em nenhum cálculo.

## 4. Custo

* **R-CUS-1** — `0 < VALOR ≤ 9999999.99`, com no máximo 2 casas decimais.
* **R-CUS-2** — A categoria deve existir e estar ativa (em edição, pode-se manter a categoria atual mesmo se desativada depois). Novas categorias são cadastradas pelo ADMIN.
* **R-CUS-3** — Tipo ∈ {`CUSTO_DIARIO`, `CUSTO_FIXO`} e deve ser igual ao tipo da categoria.
* **R-CUS-4** — Data: o ADMIN escolhe; se omitida, o servidor usa hoje. Nunca futura.
* **R-CUS-5** — Custos são reconhecidos **integralmente na data `cost_date`** (sem rateio entre dias). Ex.: aluguel de R$ 3.000,00 com data 05/09 aparece inteiro no dia 05/09, na semana e no mês que contêm esse dia. O lucro de um dia ou semana pode ficar negativo; a visão principal é o **mês fechado** (validado com o negócio em 2026-10-02).
* **R-CUS-6** — Custos excluídos logicamente não entram em nenhum cálculo.

---

## 5. Indicadores gerais

Para um período `P`, considerando **todas** as vendas (empresas + clientes avulsos) e **todos** os custos do restaurante:

| Código | Indicador | Fórmula |
|---|---|---|
| **F-01** | Receita Total | `RECEITA = Σ subtotal` das vendas em `P` |
| **F-02** | Quantidade de Marmitas | `QTD = Σ quantity` das vendas em `P` |
| **F-03** | Custos Diários | `CD = Σ amount` dos custos `CUSTO_DIARIO` em `P` |
| **F-04** | Custos Fixos | `CF = Σ amount` dos custos `CUSTO_FIXO` em `P` |
| **F-05** | Custos Totais | `CT = CF + CD` |
| **F-06** | **Lucro Líquido Geral** | `LUCRO = RECEITA − CT` (pode ser negativo) |
| **F-07** | Custo Médio por Marmita | `CMM = CT ÷ QTD`, arredondado; **`null` quando `QTD = 0`** |
| **F-08** | Número de Vendas | `NV = quantidade de lançamentos de venda` em `P` |
| **F-09** | Ticket Médio | `TM = RECEITA ÷ NV`, arredondado; **`null` quando `NV = 0`** |
| **F-10** | Preço Médio por Marmita | `PM = RECEITA ÷ QTD`, arredondado; **`null` quando `QTD = 0`** |
| **F-11** | Margem Líquida (%) | `MARGEM = LUCRO ÷ RECEITA × 100`, arredondada; **`null` quando `RECEITA = 0`** |

Receita e quantidade também são apresentadas separadas por tipo de comprador (`Empresas` e `Clientes avulsos`), cuja soma é igual ao total.

Regras gerais:

* **R-IND-1** — Somas sem registros resultam em `0.00` (nunca `null`).
* **R-IND-2** — **Nunca dividir por zero.** Toda divisão verifica o divisor; se zero, o indicador é `null` e a interface exibe "—" com a dica "sem marmitas no período" / "sem vendas no período".
* **R-IND-3** — Arredondamento apenas no resultado final das divisões. Lucro e totais são exatos.
* **R-IND-4** — Séries diárias aplicam as mesmas fórmulas a cada dia isoladamente. Dias sem movimento aparecem com zeros (e `null` para médias).
* **R-IND-5** — A soma dos valores diários de receita, quantidade e custos é igual ao total do período (propriedade testada).

---

## 6. Lucro líquido por comprador (empresa e cliente avulso)

Custos são do restaurante e não pertencem a nenhum comprador. Para obter o lucro líquido de **cada empresa** (e de cada cliente avulso), os custos totais do período são **rateados proporcionalmente à quantidade de marmitas** compradas.

* **R-RAT-1** — Base do rateio: todos os compradores com vendas em `P` (empresas **e** clientes avulsos), cada um com sua quantidade `QTD_i`. `Σ QTD_i = QTD`.
* **R-RAT-2** — **F-12 — Custo alocado**: `CUSTO_ALOCADO_i = CT × QTD_i ÷ QTD`, calculado em centavos pelo **método do maior resto**:
  1. calcular a cota exata em centavos de cada comprador;
  2. atribuir a parte inteira (piso) de cada cota;
  3. distribuir os centavos restantes, um a um, aos compradores com maior parte fracionária (desempate: empresas antes de clientes, depois menor `id`).

  Assim `Σ CUSTO_ALOCADO_i = CT` **exatamente**, sem sobra ou falta de centavos.
* **R-RAT-3** — **F-13 — Lucro líquido do comprador**: `LUCRO_i = RECEITA_i − CUSTO_ALOCADO_i`.
* **R-RAT-4** — **F-14 — Margem do comprador**: `LUCRO_i ÷ RECEITA_i × 100`, arredondada; `null` se `RECEITA_i = 0`.
* **R-RAT-5** — Consistência: `Σ LUCRO_i = LUCRO` (lucro líquido geral, F-06). Testado em todos os cenários.
* **R-RAT-6** — Se `QTD = 0` (período sem vendas), não há como ratear: nenhum comprador recebe custo, `allocation_available = false` e todo o `CT` aparece como **custos não alocados**. Nesse caso `LUCRO = −CT`.
* **R-RAT-7** — O rateio é sempre calculado sobre **todos** os compradores do período e só depois filtrado. Ou seja, o lucro de uma empresa é o mesmo no dashboard geral, no ranking e no dashboard da empresa.
* **R-RAT-8** — Subtotal "Clientes avulsos": soma de receita, quantidade, custo alocado e lucro de todos os clientes avulsos.
* **R-RAT-9** — Na série diária de um comprador, o rateio é feito **dia a dia** com o mesmo método (`CT_dia` entre os compradores do dia). Custos de dias sem nenhuma venda não são alocados naquele dia, então a soma diária pode diferir do valor do período; o valor oficial do período é sempre o do resumo (F-12/F-13), e a interface informa isso no gráfico.

---

## 7. Exemplos de referência (usados nos testes)

Período 01/09/2026 a 30/09/2026.

Vendas:

| Data | Comprador | Tipo | Preço | Qtd | Subtotal |
|---|---|---|---|---|---|
| 01/09 | Empresa A (id 1) | COMPANY | 18.50 | 40 | 740.00 |
| 15/09 | Empresa B (id 2) | COMPANY | 20.00 | 25 | 500.00 |
| 20/09 | Cliente X (id 1) | CUSTOMER | 22.00 | 5 | 110.00 |
| 30/09 | Empresa A (id 1) | COMPANY | 18.50 | 10 | 185.00 |

Custos:

| Data | Categoria | Tipo | Valor |
|---|---|---|---|
| 01/09 | Ingredientes | CUSTO_DIARIO | 400.00 |
| 05/09 | Aluguel | CUSTO_FIXO | 300.00 |
| 30/09 | Embalagens | CUSTO_DIARIO | 33.33 |

Resultado geral:

* RECEITA = 740.00 + 500.00 + 110.00 + 185.00 = **1535.00** (Empresas 1425.00; Clientes avulsos 110.00)
* QTD = **80** (Empresas 75; Clientes avulsos 5)
* CD = 433.33; CF = 300.00; CT = **733.33**
* LUCRO = 1535.00 − 733.33 = **801.67**
* CMM = 733.33 ÷ 80 = 9.166625 → **9.17**
* NV = 4; TM = 1535.00 ÷ 4 = **383.75**
* PM = 1535.00 ÷ 80 = 19.1875 → **19.19**
* MARGEM = 801.67 ÷ 1535.00 × 100 = 52.226… → **52.23**

Rateio (CT = 73333 centavos, QTD = 80):

| Comprador | QTD_i | Cota exata (centavos) | Piso | Resto | +1? | Custo alocado | Receita | Lucro |
|---|---|---|---|---|---|---|---|---|
| Empresa A | 50 | 45833.125 | 45833 | 0.125 | | **458.33** | 925.00 | **466.67** |
| Empresa B | 25 | 22916.5625 | 22916 | 0.5625 | ✔ | **229.17** | 500.00 | **270.83** |
| Cliente X | 5 | 4583.3125 | 4583 | 0.3125 | | **45.83** | 110.00 | **64.17** |
| **Total** | 80 | | 73332 | | 1 | **733.33** | 1535.00 | **801.67** |

Empresa A: TM_A = 925.00 ÷ 2 = 462.50; PM_A = 18.50; margem = 466.67 ÷ 925.00 × 100 = 50.45.

Período inclusivo: 30/09 a 30/09 → RECEITA = 185.00, QTD = 10, CT = 33.33, LUCRO = 151.67, CMM = 3.33; Empresa A recebe 33.33 de custo e lucra 151.67.

Sem vendas e sem custos (02/09 a 04/09): RECEITA = 0.00, CT = 0.00, LUCRO = 0.00, CMM = `null`, TM = `null`, MARGEM = `null`.

Custos sem vendas (05/09 a 05/09): RECEITA = 0.00, CT = 300.00, LUCRO = −300.00, CMM = `null`, `allocation_available = false`, custos não alocados = 300.00.

---

## 8. Histórico de alterações

| Data | Alteração | Autor |
|---|---|---|
| 2026-10-02 | Versão inicial das regras (Fase 0) | Claude Code |
| 2026-10-02 | Revisão com o negócio: clientes avulsos independentes das empresas; venda com comprador único; lucro líquido geral (empresas + clientes) e por comprador via rateio por marmita com maior resto (seção 6); data de venda/custo escolhida pelo ADMIN; período `last_month`; margem líquida; R-CUS-5 validada | Claude Code |
