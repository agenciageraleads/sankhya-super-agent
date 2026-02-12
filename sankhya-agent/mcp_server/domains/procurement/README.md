# Domínio: Compras (Procurement)

Este domínio contém a inteligência do **Auxiliar de Compras** do Sankhya Super Agente.

## Estrutura de Pastas

* `rules/`: Contém as particularidades deste negócio.
  * `queries_abc.sql`: Query que extrai o giro e curva ABC das dashboards/telas.
  * `queries_popularity.sql`: Query que extrai orçamentos perdidos (demanda reprimida).
  * `business_rules.yaml`: Pesos de decisão, dias de estoque de segurança, etc.
* `workflows/`: Orquestração dos processos de compra.
  * `radar.py`: Motor de análise de estoque e sugestão de compra.
  * `quoter.py`: Automação de disparos via WhatsApp.
  * `negotiator.py`: Lógica de comparação de preços e contra-propostas.
* `services/`: Adaptadores de integração.
  * `sankhya_adapter.py`: Camada que executa as queries do `rules/`.
  * `evolution_service.py`: Integração com o WhatsApp.

## Como Personalizar para outro Negócio

1. Mantenha a lógica em `workflows/` e `services/` (Genérica).
2. Edite apenas os arquivos em `rules/` para apontar para as tabelas/views específicas do novo Sankhya.
3. Ajuste o `business_rules.yaml` conforme a política de estoque do novo cliente.
