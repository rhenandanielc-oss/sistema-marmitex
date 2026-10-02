# GUIA-DO-ADMIN.md

# Guia de uso — Sistema Marmitex B2B

Para quem usa o sistema no dia a dia. Para abrir: dois cliques em **`iniciar-marmitex.bat`** (ou no atalho "Marmitex" da área de trabalho), ou acesse **http://localhost:8080** no navegador.

---

## 1. Primeiros passos (uma vez)

1. **Tipos de custo** (menu *Cadastros → Tipos de custo*): já vêm cadastrados Ingredientes, Embalagens, Entregas, Equipamentos, Gasolina (diários) e Salários, Aluguel, Água, Energia elétrica, Gás (fixos). Crie outros se precisar (ex.: "Descartáveis").
2. **Empresas** (*Cadastros → Empresas*): cadastre cada empreiteira — nome, local/obra, **recebimento padrão** (normalmente *Obra*), ciclo (quinzenal/mensal), data de início e data de pagamento.
3. **Clientes avulsos** (*Cadastros → Clientes avulsos*): pessoas que compram por conta própria — nome, telefone, local, **recebimento padrão** (*Retirada*, *Entrega* ou *Obra*), ciclo e datas.
4. **Usuários** (*Administração → Usuários*): se outra pessoa for usar, crie um login para ela (não compartilhe o seu).

---

## 2. Rotina diária

### Lançar vendas (*Lançamentos → Vendas*)

1. Escolha **Empresa (empreiteira)** ou **Cliente avulso**.
2. Selecione o comprador. O **preço** é sugerido pela última venda dele e o **recebimento** vem do cadastro — ambos podem ser alterados.
3. Informe a **quantidade** de marmitas.
4. **Data**: já vem com hoje. Esqueceu de lançar ontem? Troque a data (não aceita data futura).
5. **Pagamento**: *Pendente* (padrão) ou *Pago*.
6. Clique **Registrar venda**. O sistema calcula o subtotal e mostra uma confirmação.

Na lista abaixo do formulário:

* **Marcar pago** — quando o cliente pagar (ou *Desfazer pago*).
* **Editar** / **Excluir** — corrige ou remove um lançamento (fica registrado na auditoria).
* Filtros por período, tipo de comprador, pagamento e recebimento; os totais (marmitas, total e **a receber**) acompanham o filtro.

### Lançar custos (*Lançamentos → Custos*)

1. Escolha o **tipo de custo**, informe o **valor**, a **data** (padrão hoje; pode ser uma data passada) e uma descrição opcional.
2. **Registrar custo**.

No topo da tela ficam sempre os **custos do mês até agora** (diários, fixos e total), que aumentam a cada lançamento. A coluna **Acumulado** mostra a soma lançamento a lançamento.

---

## 3. Fechamento e cobrança (quinzenal/mensal)

*Banco de dados → Histórico*:

1. Em **Empresa** (ou **Cliente avulso**) escolha o comprador.
2. Ajuste **Data inicial** e **Data final** para a quinzena ou o mês.
3. O cartão **Total de vendas** é o valor do período; **A receber** mostra o que ainda está pendente.
4. Para ver só o que falta receber de todos: **Pagamento → Pendentes**.

Atalho: no Dashboard da empresa, clique em **"Fechamento do período no Histórico"**.

---

## 4. Dashboard (resultado)

*Visão geral → Dashboard*. Escolha o período: **Hoje, Semana, Mês, Mês anterior** ou **Personalizado**.

| Indicador | Significado |
|---|---|
| **Lucro líquido** | Receita − todos os custos (fixos + diários) do período. É o número principal do fim do mês. |
| Receita total | Soma de todas as vendas (empresas + clientes), pagas ou não. |
| Custos fixos / diários / totais | Soma dos custos lançados no período. |
| Quantidade de marmitas | Total vendido no período. |
| Custo médio por marmita | Custos totais ÷ marmitas. |
| **A receber** | Vendas ainda pendentes de pagamento (não altera o lucro). |
| Ticket médio | Receita ÷ número de vendas. |

Gráficos: acumulado do período (receita, custos e lucro somando dia a dia), receita e marmitas por dia, custos diários × fixos, lucro diário, receita por empresa e vendas por empresa ao longo dos dias. Todo gráfico tem **"Ver tabela"** com os números.

* **Mês anterior** mostra o mês fechado — o melhor para conferir o resultado final.
* Em dias de custo fixo alto (aluguel, salários) o lucro do dia fica negativo; isso é normal. O que importa é o acumulado do mês.

### Dashboard de uma empresa ou cliente

Use **Ver empresa…** / **Ver cliente avulso…** no topo, ou clique no nome na tabela de faturamento. Mostra **somente faturamento** (receita, marmitas, ticket, a receber, comparação com o período anterior e últimas vendas) — os custos são do restaurante como um todo e entram apenas no lucro geral.

---

## 5. Cadastros: ativar e desativar

* **Desativar** uma empresa/cliente/tipo de custo tira-o das listas de novos lançamentos, mas **mantém todo o histórico** e os valores no dashboard.
* Nada é apagado de verdade: vendas e custos excluídos saem dos cálculos, mas continuam registrados na auditoria.

---

## 6. Cuidados

* Confira a **data** antes de registrar vendas/custos esquecidos.
* Se aparecer "o registro foi alterado por outra pessoa", alguém editou o mesmo item no outro notebook: a tela recarrega — confira e faça a alteração de novo.
* Copie a pasta de **backups** para um pendrive ou para a nuvem toda semana (`OPERACAO.md`).
