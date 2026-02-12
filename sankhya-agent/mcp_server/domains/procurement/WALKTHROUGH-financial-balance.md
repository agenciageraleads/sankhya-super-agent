# Walkthrough: Skill de Equilíbrio Financeiro em Compras ⚖️

Esta skill permite ao Agente Super de Compras cruzar os dados de necessidade de compra (Giro) com a realidade financeira do caixa e dos compromissos a pagar.

## 🎯 Objetivo

Evitar compras que causem ruptura de caixa ou identificar oportunidades de compra em lote quando há sobra de recursos:

* "Temos saldo em caixa suficiente para cobrir as sugestões de compra desta semana?"
* "Qual nossa folga operacional (Caixa - Contas a Pagar Curto Prazo)?"
* "Qual o valor total hoje imobilizado em estoque?"

## 🛠️ Componentes Técnicos

### 1. Queries SQL Especializadas

* **Valorização de Estoque (`queries_inventory_valuation.sql`)**: Usa o custo de reposição (`CUSREP`) mais recente para calcular o valor real de mercado do que está na prateleira.
* **Fluxo de Caixa (`queries_financial_cash_flow.sql`)**: Consolida saldos de contas bancárias e caixas internos.
* **Contas a Pagar (`queries_financial_payable_summary.sql`)**: Categoriza títulos pendentes em 'Atrasados', 'No Prazo' e 'Futuros'.

### 2. Lógica de Negócio (Adaptador)

O método `get_financial_procurement_balance` no `SankhyaProcurementService` realiza o cruzamento estratégico:

1. Busca total a **Pagar** vs total a **Receber** no horizonte de X dias.
2. Busca **Valor Total de Estoque** imobilizado.
3. Calcula a **Média de Venda Mensal** dos últimos 3 meses.
4. Gera o **Índice de Pressão sobre o Caixa** (Pagar/Receber) e a **Cobertura de Estoque** (Estoque/Venda Média).

## 💡 Exemplos de Uso pelo Agente

### Cenário A: Identificação de Estoque Inflado

**Usuário:** "Podemos manter o padrão de 45 dias de estocagem para o próximo mês?"
**Agente:** (Executa a skill) "Atualmente nosso índice Pagar vs Receber está em 1.4, significando que estamos comprando 40% mais do que recebendo. Além disso, nossa cobertura de estoque total está em 4.2 meses. Manter 45 dias de estocagem agora pode inflar ainda mais o estoque e secar o caixa. Recomendo reduzir para 30 dias nos itens de curva B e C."

### Cenário B: Alerta de Liquidez

**Agente:** "Notei que a Proporção de Estoque no Ativo Operacional subiu para 85%. Isso indica que grande parte do seu caixa foi transformado em estoque nos últimos 60 dias. Sugiro focar em ações de venda para recuperar a liquidez antes de novas compras massivas."

## 📈 Pontos de Inteligência

* **Folga Operacional:** Indica a saúde imediata para novas compras.
* **Razão Estoque/Caixa:** Ajuda a medir a liquidez. Um índice muito alto pode indicar excesso de estoque (dinheiro parado).
