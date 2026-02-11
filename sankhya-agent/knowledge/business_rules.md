# Regras de Negócio — Portal Distribuidora / B&B

## Configurações da Instância Sankhya

| Parâmetro | Valor | Descrição |
|---|---|---|
| CODEMP | 1 | Empresa padrão |
| CODLOCAL | 10010000 | Depósito principal (estoque) |
| CODLOCAL_EXCLUIR | 10090000 | Local de descarte/exclusão |
| TOP_ENTRADA | 221 | TOP de entrada no estoque |
| TOP_SAIDA | 1221 | TOP de saída do estoque |

## Regras Críticas

### Vendas

- **Não vender para CPF sem Inscrição Estadual** em operações interestaduais.
- Pedidos acima do limite de crédito do parceiro devem ser aprovados pelo gerente comercial.
- Todas as vendas devem ter TOP corretamente configurada para tributação.

### Estoque

- O custo de reposição (CUSREP) é calculado pela última entrada no `TGFCUS`.
- Produtos com `ATIVO='S'` e `USOPROD='R'` (revenda) são os que aparecem nas operações comerciais.
- Controle de lote via campo `CONTROLE` na `TGFEST`.

### Financeiro

- Boletos gerados automaticamente para vendas a prazo.
- Conciliação bancária via `TGFMBC`.

### Usuários e Permissões

- Cada operação registra o `CODUSU` (código do usuário) para auditoria.
- Perfis de acesso controlam quais TOPs cada usuário pode utilizar.
