# Walkthrough: Skill de Inteligência de Fornecedores 🕵️‍♂️

Esta skill permite ao Agente Super de Compras mapear o histórico de compras e entender a relação entre Fornecedores, Grupos de Produtos e Itens específicos dentro do Sankhya.

## 🎯 Objetivo

Habilitar o agente a responder perguntas como:

* "De quem compramos o produto X no último ano?"
* "Quais grupos de produtos o fornecedor Y costuma nos vender?"
* "Qual o volume de compras (pedidos e valor) que temos com o parceiro Z?"

## 🛠️ Componentes Técnicos

### 1. Queries de Base (`rules/`)

A skill é alimentada por três consultas SQL otimizadas:

* `queries_suppliers_list.sql`: Localiza fornecedores com base em filtros de período, empresa, produto ou grupo.
* `queries_supplier_groups.sql`: Consolida o volume de compras por **Grupo de Produto** para um parceiro específico.
* `queries_supplier_products.sql`: Lista os **Detalhes dos Produtos** (Marca, Qtd, Valor) comprados de um parceiro.

### 2. Implementação no Serviço (`sankhya_adapter.py`)

Foram implementados dois métodos principais no `SankhyaProcurementService`:

* `get_suppliers_for_product()`: Retorna o ranking de fornecedores que atenderam determinada demanda.
* `get_supplier_purchase_summary()`: Retorna um raio-x completo do que um fornecedor nos vende.

## 🚀 Como usar (Para o Agente)

### Exemplo 1: Descobrir onde comprar um item

Ao identificar uma ruptura de estoque de um produto Curva A, o Agente pode chamar:

```python
fornecedores = service.get_suppliers_for_product(
    ini='01/01/2024', 
    fin='31/12/2024', 
    empresa='1', 
    codprod=123
)
```

### Exemplo 2: Preparar uma negociação

Antes de iniciar uma conversa via WhatsApp com um fornecedor, o Agente pode analisar o histórico:

```python
historico = service.get_supplier_purchase_summary(
    codparc=500, 
    ini='01/01/2024', 
    fin='31/12/2024', 
    empresa='1'
)
# historico['grupos'] -> Quais categorias ele domina
# historico['produtos'] -> Itens recorrentes
```

## 📝 Regras de Negócio Aplicadas

* **Filtro de Movimentação:** Apenas `TIPMOV = 'C'` (Compras) ou conforme configurado.
* **TOPs de Pedido:** Por padrão utiliza as TOPs `200` e `227` (configuráveis).
* **Parceiros:** Filtra apenas parceiros marcados como `FORNECEDOR = 'S'`.

---
*Documento gerado para o Super Agente - Domínio de Compras.*
