# Plano de Implementação: Skill de Equilíbrio Financeiro em Compras ⚖️

Este plano detalha a criação de uma nova funcionalidade para permitir que o Agente Super de Compras balanceie as sugestões de compra com a disponibilidade financeira real (Caixa) e o compromisso de Contas a Pagar.

## 🎯 Objetivo

Habilitar o agente a responder perguntas como:

* "O valor da compra sugerida cabe no nosso fluxo de caixa para os próximos 15 dias?"
* "Qual o valor total que temos imobilizado em estoque hoje versus o que temos em banco?"
* "Podemos aumentar o lote de compra do item X dado que o saldo em conta está positivo?"

## 🛠️ Componentes Técnicos

### 1. Novas Queries SQL

* `queries_financial_cash_flow.sql`: Busca o saldo real consolidado de todas as contas bancárias ativas.
* `queries_financial_payable_summary.sql`: Resume os compromissos de Contas a Pagar (pendentes) para os próximos X dias.
* `queries_inventory_valuation.sql`: Calcula o valor total do estoque atual baseado no custo de reposição.

### 2. Implementação no `SankhyaProcurementService`

Adicionar o método `get_financial_procurement_balance`:

* Parâmetros: `dias_horizonte` (ex: 15, 30 dias para análise de pagamentos).
* Retorno: Um objeto consolidado contendo `saldo_caixa`, `total_contas_a_pagar`, `valor_estoque_total` e um `indice_liquidez_compras`.

### 3. Documentação

* Atualizar o `WALKTHROUGH-procurement-intelligence.md` (ou criar um novo específico para balanço financeiro).

## 📅 Cronograma

1. **Fase 1**: Criação das queries SQL baseadas nos logs de `TSICTA` e `TGFFIN`.
2. **Fase 2**: Implementação no `sankhya_adapter.py`.
3. **Fase 3**: Teste de integração (simulado via logs).

## ⚠️ Considerações de Segurança

* O acesso a dados financeiros (`TSICTA` e `TGFFIN`) deve ser restrito a perfis de coordenadores/compradores seniores.
* As queries não devem expor detalhes de salários ou dados sensíveis de parceiros específicos, apenas totais categóricos.
