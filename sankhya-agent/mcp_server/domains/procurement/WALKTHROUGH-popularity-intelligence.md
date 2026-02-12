# Walkthrough: Skill de Popularidade e Demanda Reprimida 📉

Esta skill permite ao Agente Super de Compras identificar "Vendas Perdidas" através da análise de orçamentos que não foram convertidos por falta de estoque.

## 🎯 Objetivo

Habilitar o agente a agir proativamente sobre itens com alta demanda mas baixo nível de serviço:

* "Quais produtos mais perdemos venda por falta de estoque este mês?"
* "Qual o valor financeiro total que deixamos de faturar no item X?"
* "Qual a quantidade mais comum (Moda) que os clientes pedem para este produto?" (Ajudando a definir o lote de compra).

## 🛠️ Componentes Técnicos

### 1. Queries de Base (`rules/`)

* `queries_popularity_summary.sql`: Realiza o cruzamento entre orçamentos (TOP 900/1000) e o histórico de estoque (`TBL_ESTOQUE_HISTORICO_PRODUTO`) na data da negociação.
* `queries_popularity_drilldown.sql`: Fornece a lista detalhada de orçamentos insuficientes para um produto, permitindo ver os clientes afetados.

### 2. Implementação no Serviço (`sankhya_adapter.py`)

* `get_popularity_analysis()`: Retorna o ranking dos top 100 itens com maior valor perdido.
* `get_popularity_drilldown()`: Permite investigar a fundo os orçamentos de um produto específico.

## 🚀 Como usar (Para o Agente)

### Exemplo: Priorização de Compra por Impacto Financeiro

O Agente pode rodar mensalmente:

```python
analise_perda = service.get_popularity_analysis(
    ini='01/02/2026', 
    fin='28/02/2026'
)
# O Agente foca nos itens onde o VALOR_TOTAL_PERDIDO é maior.
```

## 📝 Pontos de Inteligência

* **Moda da Qtd Negociada:** Diferente da média, a moda mostra qual a quantidade "padrão" que o cliente pede. Se a moda é 50 unidades, não adianta o comprador comprar de 10 em 10.
* **Estoque na Data:** A query é inteligente - ela não olha o estoque de hoje, mas sim se no dia que o vendedor fez o orçamento, o estoque era suficiente.

---
*Documento gerado para o Super Agente - Domínio de Compras.*
