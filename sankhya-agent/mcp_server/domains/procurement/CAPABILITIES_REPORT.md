# 📊 Relatório de Capacidades: Role COMPRADOR

> **Data da Análise**: 13 de Fevereiro de 2026
> **Status Geral**: Fase 2 - 85% Concluído
> **Maturidade**: Analista de Compras em Tempo Real

---

## 🎯 Visão Executiva

O **Role COMPRADOR** do Sankhya Super Agent evoluiu de um chatbot básico para um **Analista de Compras Inteligente** capaz de:

- ✅ Identificar demanda reprimida e oportunidades perdidas
- ✅ Mapear fornecedores e histórico de compras
- ✅ Analisar saúde financeira vs necessidade de compra
- ✅ Integrar com WhatsApp (Evolution API) para cotações
- ⏳ Gerar sugestões de compra (em progresso)

---

## 📚 Capacidades Implementadas (100%)

### 1. 🔍 Skill de Popularidade (Demanda Reprimida)

**O que faz:**
Analisa orçamentos que não viraram venda por falta de estoque.

**Capacidades específicas:**

| Capacidade | Descrição | Status |
|------------|-----------|--------|
| **Identificar vendas perdidas** | Cruza orçamentos (TOP 900/1000) com histórico de estoque na data da negociação | ✅ 100% |
| **Calcular impacto financeiro** | Calcula valor total perdido por produto | ✅ 100% |
| **Análise de moda** | Identifica quantidade mais comum pedida (não média, mas moda estatística) | ✅ 100% |
| **Ranking de prioridade** | Top 100 itens com maior valor perdido | ✅ 100% |
| **Drilldown detalhado** | Lista orçamentos insuficientes por produto com clientes afetados | ✅ 100% |

**Exemplo de uso:**
```
Comprador: "Quais produtos perdemos mais vendas no último mês?"

Agent: "Lucas, no mês passado perdemos R$ 47.350 em vendas não realizadas.
Os top 3 produtos foram:

1. Cabo Flexível 4mm (CODPROD: 1234)
   - Valor perdido: R$ 15.200
   - Orçamentos: 25 cotações
   - Moda de quantidade: 100m (cliente pede em rolos de 100m)
   - Recomendação: Comprar 500m para cobrir demanda típica

2. Disjuntor 32A Bipolar (CODPROD: 5678)
   - Valor perdido: R$ 12.800
   - Orçamentos: 18 cotações
   - Moda de quantidade: 10 unidades
   - Recomendação: Lote mínimo de 50 unidades

3. Lâmpada LED 9W (CODPROD: 9012)
   - Valor perdido: R$ 8.950
   - Orçamentos: 32 cotações
   - Moda de quantidade: 20 unidades
   - Recomendação: Comprar 100 unidades"
```

**Queries SQL:**
- `queries_popularity_summary.sql` (análise geral)
- `queries_popularity_drilldown.sql` (detalhamento por produto)

**Métodos da API:**
- `get_popularity_analysis(ini, fin, empresa, codprod, grupoprod)`
- `get_popularity_drilldown(codprod, ini, fin, empresa)`

---

### 2. 🤝 Skill de Inteligência de Fornecedores

**O que faz:**
Mapeia histórico de compras e relacionamento com fornecedores.

**Capacidades específicas:**

| Capacidade | Descrição | Status |
|------------|-----------|--------|
| **Identificar fornecedores** | Localiza de quem compramos cada produto/grupo | ✅ 100% |
| **Ranking por volume** | Ordena fornecedores por qtd/valor comprado | ✅ 100% |
| **Análise por grupo** | Consolida compras por grupo de produto | ✅ 100% |
| **Histórico detalhado** | Lista produtos, marcas, qtd, valor por fornecedor | ✅ 100% |
| **Preparação para negociação** | Raio-X completo do relacionamento comercial | ✅ 100% |

**Exemplo de uso:**
```
Comprador: "De quem compramos cabos flexíveis no último ano?"

Agent: "Seus principais fornecedores de cabos flexíveis (2024):

1. FORNECEDOR: ABC Elétrica (CODPARC: 500)
   - Volume: R$ 245.800 em 42 pedidos
   - Principais itens:
     • Cabo Flexível 2.5mm - 2.500m (R$ 89.400)
     • Cabo Flexível 4mm - 1.800m (R$ 95.200)
     • Cabo Flexível 6mm - 800m (R$ 61.200)
   - Prazo médio de entrega: 7 dias
   - Última compra: 15/01/2025

2. FORNECEDOR: XYZ Distribuidora (CODPARC: 750)
   - Volume: R$ 128.500 em 25 pedidos
   - Principais itens:
     • Cabo Flexível 10mm - 600m (R$ 78.300)
     • Cabo Flexível 16mm - 300m (R$ 50.200)
   - Prazo médio de entrega: 10 dias
   - Última compra: 08/02/2025

Recomendação: ABC Elétrica tem melhor histórico para bitolas menores.
Para bitolas acima de 10mm, XYZ tem melhores preços."
```

**Queries SQL:**
- `queries_suppliers_list.sql` (lista fornecedores)
- `queries_supplier_groups.sql` (consolidação por grupo)
- `queries_supplier_products.sql` (detalhamento de produtos)

**Métodos da API:**
- `get_suppliers_for_product(ini, fin, empresa, codprod, grupoprod)`
- `get_supplier_purchase_summary(codparc, ini, fin, empresa)`

---

### 3. ⚖️ Skill de Equilíbrio Financeiro

**O que faz:**
Cruza necessidade de compra com realidade financeira (caixa + contas a pagar/receber).

**Capacidades específicas:**

| Capacidade | Descrição | Status |
|------------|-----------|--------|
| **Análise de caixa** | Consolida saldos bancários e caixas internos | ✅ 100% |
| **Contas a pagar** | Categoriza em Atrasados/No Prazo/Futuros | ✅ 100% |
| **Valorização de estoque** | Calcula valor real usando CUSREP (custo de reposição) | ✅ 100% |
| **Índice de pressão** | Calcula Pagar/Receber no horizonte de N dias | ✅ 100% |
| **Cobertura de estoque** | Quantos meses de venda estão imobilizados | ✅ 100% |
| **Folga operacional** | Caixa disponível após compromissos | ✅ 100% |

**Exemplo de uso:**
```
Comprador: "Posso comprar R$ 80k em estoque de cabos agora?"

Agent: "Análise Financeira (Horizonte: 30 dias):

💰 SITUAÇÃO DO CAIXA:
- Saldo disponível: R$ 152.300
- Contas a pagar (30d): R$ 198.700
- Contas a receber (30d): R$ 145.200
- Folga operacional: R$ 98.800 (insuficiente!)

📊 ÍNDICES:
- Pagar/Receber: 1.37 (comprando 37% a mais do que recebendo)
- Estoque imobilizado: R$ 428.500
- Cobertura: 4.2 meses de venda
- % do estoque no ativo: 78% (ALTO!)

⚠️ RECOMENDAÇÃO:
NÃO recomendo compra de R$ 80k agora. Motivos:

1. Folga operacional está em R$ 98.8k, mas você tem R$ 198.7k a pagar
2. Índice Pagar/Receber em 1.37 indica pressão de caixa
3. Estoque já cobre 4.2 meses (ideal: 2-3 meses)

ALTERNATIVA:
- Compre apenas R$ 35k dos itens mais críticos (curva A em ruptura)
- Foque em VENDER o estoque atual para recuperar liquidez
- Reavalie em 15 dias quando o recebível entrar"
```

**Queries SQL:**
- `queries_inventory_valuation.sql` (valor do estoque)
- `queries_financial_cash_flow.sql` (saldos em caixa)
- `queries_financial_payable_summary.sql` (contas a pagar)
- `queries_financial_flow_comparison.sql` (pagar vs receber)

**Métodos da API:**
- `get_financial_procurement_balance(dias_horizonte=30)`

---

### 4. 📈 Skill de Análise de Giro

**O que faz:**
Analisa giro de produtos e identifica oportunidades de compra.

**Capacidades específicas:**

| Capacidade | Descrição | Status |
|------------|-----------|--------|
| **Consulta direta de giro** | Acessa dados do motor de giro Sankhya (TGFGIR) | ✅ 100% |
| **Média de vendas** | Calcula média de vendas por período | ✅ 100% |
| **Identificar oportunidades** | Lista produtos que precisam reposição | ✅ 100% |
| **Análise por categoria** | Consolida giro por grupo de produtos | ✅ 100% |
| **Itens por fornecedor** | Cruza giro com fornecedores históricos | ✅ 100% |
| **Produtos alternativos** | Identifica substitutos disponíveis | ✅ 100% |

**Queries SQL:**
- `queries_giro_direct.sql` (consulta motor de giro)
- `queries_sales_average.sql` (média de vendas)
- `queries_opportunities_by_supplier.sql` (oportunidades por fornecedor)

**Métodos da API:**
- `get_giro_data(codrel=2535)`
- `get_opportunities(codrel=2535)`
- `get_supplier_items(codparc, codrel=2535)`
- `get_full_category_analysis(target_type, target_value, codrel=2535)`
- `get_group_stock_summary(codrel=2535)`
- `get_alternatives(codprod)`

---

### 5. 📱 Integração WhatsApp (Evolution API)

**O que faz:**
Permite comunicação automatizada com fornecedores via WhatsApp.

**Capacidades específicas:**

| Capacidade | Descrição | Status |
|------------|-----------|--------|
| **Enviar mensagens de texto** | Disparo de cotações via texto | ✅ 100% |
| **Enviar arquivos** | Envio de planilhas/PDFs (mapa de cotação) | ✅ 100% |
| **Receber mensagens** | Captura respostas de fornecedores | ✅ 100% |
| **Templates prontos** | Mensagens pré-formatadas para cotação | ⏳ 50% |

**Métodos da API:**
- `send_text(number, text)`
- `send_media(number, media_url, caption, media_type)`
- `get_messages(number)`

---

## 🔧 Arquitetura Técnica

### Estrutura de Arquivos

```
procurement/
├── services/
│   ├── sankhya_adapter.py      (349 linhas - 21 métodos)
│   └── evolution_service.py    (integração WhatsApp)
├── workflows/
│   └── radar.py               (motor de análise - em desenvolvimento)
├── rules/
│   ├── business_rules.yaml    (políticas de estoque)
│   └── queries_*.sql          (16 queries especializadas)
├── knowledge/
│   └── supplier_state.json    (366 linhas - estado dos fornecedores)
└── training/
    ├── KNOWLEDGE_SUMMARY.md   (conhecimento extraído)
    └── video_summaries.md     (526 linhas - análise de vídeos)
```

### Queries SQL Disponíveis (16)

1. `queries_abc.sql` - Curva ABC
2. `queries_popularity.sql` - Popularidade base
3. `queries_popularity_summary.sql` - Resumo de vendas perdidas
4. `queries_popularity_drilldown.sql` - Detalhamento de orçamentos
5. `queries_suppliers_list.sql` - Lista de fornecedores
6. `queries_supplier_groups.sql` - Consolidação por grupo
7. `queries_supplier_products.sql` - Produtos por fornecedor
8. `queries_financial_cash_flow.sql` - Fluxo de caixa
9. `queries_financial_payable_summary.sql` - Contas a pagar
10. `queries_inventory_valuation.sql` - Valorização de estoque
11. `queries_financial_flow_comparison.sql` - Pagar vs Receber
12. `queries_giro_direct.sql` - Motor de giro
13. `queries_sales_average.sql` - Média de vendas
14. `queries_opportunities_by_supplier.sql` - Oportunidades por fornecedor

### Métodos da API (21 funções)

**SankhyaProcurementService** (`sankhya_adapter.py`):

```python
# Popularidade
get_popularity_analysis(ini, fin, empresa, codprod, grupoprod)
get_popularity_drilldown(codprod, ini, fin, empresa)

# Fornecedores
get_suppliers_for_product(ini, fin, empresa, codprod, grupoprod)
get_supplier_purchase_summary(codparc, ini, fin, empresa)

# Financeiro
get_financial_procurement_balance(dias_horizonte=30)

# Giro e Oportunidades
get_giro_data(codrel=2535)
get_opportunities(codrel=2535)
get_supplier_items(codparc, codrel=2535)
get_full_category_analysis(target_type, target_value, codrel=2535)
get_group_stock_summary(codrel=2535)
get_alternatives(codprod)

# ABC
get_abc_giro_data()
```

**EvolutionWhatsAppService** (`evolution_service.py`):

```python
send_text(number, text)
send_media(number, media_url, caption, media_type)
get_messages(number)
```

---

## 📊 Regras de Negócio (business_rules.yaml)

```yaml
# Políticas de Estoque
dias_seguranca_curva_a: 30
dias_seguranca_curva_b: 20
dias_seguranca_curva_c: 10

# Pesos de Decisão
peso_popularidade: 0.4    # 40% - vendas perdidas
peso_giro: 0.4           # 40% - histórico de vendas
peso_financeiro: 0.2     # 20% - saúde do caixa

# TOPs Sankhya
tops_pedido_compra: [200, 227]
tops_orcamento: [900, 1000]
tipmov_compra: 'C'

# Configurações de Análise
max_items_sugestao: 100
meses_historico_fornecedor: 12
meses_media_vendas: 3
```

---

## 🎯 Conhecimento de Negócio

### Estratégia de Precificação

- **Varejo**: 28% de margem
- **Atacado**: 25% de margem
- **Categorias**:
  1. Preço de Mercado (Cabos, Disjuntores)
  2. Margem Geral (grupos específicos)
  3. Formação Padrão (28%/25%)

### Domínios de Produtos

- **Iluminação**: LED Integrado, Lâmpadas, Fitas, Trilhos
- **Condutores**: Cabos Flexíveis 750V, Cabos 1KV
- **Proteção**: Disjuntores, Quadros
- **Fixação e Infra**: Eletrocalhas, Perfilados

### Processo de Cotação

- **Mapa Excel**: Suporta até 10 fornecedores (colunas 0 a 0.9)
- **Critérios**:
  - Urgência → Priorizar prazo de entrega
  - Rotina → Priorizar menor preço total (com IPI/ST)

---

## 🚀 Capacidades em Desenvolvimento (Fase 2 - 85%)

### ⏳ Sugestão de Compra Reativa

**Status**: Em progresso (workflow/radar.py)

**O que fará:**
Gerar automaticamente planilha de sugestão de compra cruzando:
- Giro de produtos (demanda histórica)
- Popularidade (vendas perdidas)
- Saúde financeira (capacidade de compra)

**Output esperado:**
```csv
CODPROD,PRODUTO,CURVA,ESTOQUE_ATUAL,GIRO_30D,VENDAS_PERDIDAS,SUGESTAO_COMPRA,VALOR_TOTAL,FORNECEDOR_1,FORNECEDOR_2
1234,Cabo 4mm,A,50m,120m,25 cotações,200m,R$ 8.500,ABC Elétrica,XYZ Dist
```

### ⏳ Inteligência de Cabos (Maiores Pontas)

**Status**: Lógica mapeada, integração pendente

**O que fará:**
Para produtos tipo "Cabo", aplicar filtro de "Maior Ponta" conforme processos da empresa (visto em vídeos de treinamento).

---

## 📅 Roadmap Futuro (Fase 3 - A Iniciar)

### 📅 Mapa de Cotação Automatizado

**O que fará:**
- Gerar automaticamente Excel com template de cotação
- Listar produtos sugeridos + quantidades
- Pré-preencher fornecedores históricos
- Enviar via WhatsApp para os fornecedores

### 📅 Monitor de Ruptura Proativo

**O que fará:**
- Alertar quando item curva A entrar em tendência de falta
- Calcular ponto de pedido inteligente
- Notificar comprador antes da ruptura

### 📅 Alternativos Inteligentes

**O que fará:**
- Sugerir troca automática de marca/modelo
- Baseado em estoque disponível de alternativos
- Manter qualidade/especificação equivalente

---

## 📈 Métricas de Maturidade

### Fase 1: Visibilidade (✅ 100%)
- ✅ Conectividade Sankhya
- ✅ Mapeamento de tabelas core
- ✅ Extração de conhecimento

### Fase 2: Inteligência (✅ 85%)
- ✅ Skills de análise (popularidade, fornecedores, financeiro)
- ✅ Integração WhatsApp
- ⏳ Sugestão automatizada (em progresso)

### Fase 3: Automação (📅 0%)
- 📅 Mapa de cotação automatizado
- 📅 Monitor proativo
- 📅 Alternativos inteligentes

---

## 💬 Exemplos de Perguntas que o Comprador Pode Fazer

### Análise de Demanda
- ✅ "Quais produtos mais perdemos vendas no último mês?"
- ✅ "Qual o valor financeiro que deixamos de faturar em cabos?"
- ✅ "Qual quantidade os clientes geralmente pedem do produto X?"

### Inteligência de Fornecedores
- ✅ "De quem compramos disjuntores no último ano?"
- ✅ "Quais grupos de produtos o fornecedor ABC vende para nós?"
- ✅ "Qual nosso histórico de compras com a XYZ Distribuidora?"

### Saúde Financeira
- ✅ "Temos caixa para comprar R$ 50k em estoque agora?"
- ✅ "Qual nossa folga operacional para os próximos 30 dias?"
- ✅ "Quanto está imobilizado em estoque atualmente?"
- ✅ "Estamos comprando mais do que recebendo?"

### Giro e Oportunidades
- ✅ "Quais produtos precisam de reposição urgente?"
- ✅ "Mostre o giro de cabos flexíveis dos últimos 3 meses"
- ✅ "Quais oportunidades de compra o fornecedor ABC tem?"

### Processos (Em desenvolvimento)
- ⏳ "Gere uma sugestão de compra para esta semana"
- ⏳ "Crie um mapa de cotação para enviar aos fornecedores"
- ⏳ "Quais produtos alternativos posso oferecer ao cliente?"

---

## 🔐 Segurança e Compliance

### Dados Sensíveis
- ✅ Apenas consultas (SELECT) - sem UPDATE/DELETE/INSERT
- ✅ Filtro por empresa (CODEMP)
- ✅ Logs de todas as operações

### Integrações Externas
- ✅ Evolution API (WhatsApp) via token autenticado
- ✅ Credenciais em variáveis de ambiente
- ✅ Rate limiting configurado

---

## 🎯 Resumo Executivo

### O que o COMPRADOR consegue fazer HOJE:

1. ✅ **Identificar oportunidades perdidas** - Sabe exatamente o que deixou de vender
2. ✅ **Conhecer fornecedores** - Histórico completo de quem vende o quê
3. ✅ **Proteger o caixa** - Cruza necessidade vs realidade financeira
4. ✅ **Analisar giro** - Identifica produtos que precisam reposição
5. ✅ **Comunicar via WhatsApp** - Envia cotações automatizadas

### O que está em desenvolvimento:

6. ⏳ **Gerar sugestão de compra** - Planilha automática otimizada
7. ⏳ **Inteligência específica** - Lógica de cabos e outros processos customizados

### O que está no roadmap:

8. 📅 **Automatizar cotações** - Mapa + envio automático
9. 📅 **Monitorar rupturas** - Alertas proativos
10. 📅 **Sugerir alternativos** - Substituições inteligentes

---

**Conclusão**: O Role COMPRADOR está em estado **PRODUTIVO** para análise e tomada de decisão. A automação completa (Fase 3) depende da conclusão da Fase 2.

---

*Relatório gerado em: 13/02/2026*
*Próxima revisão: Conclusão da Fase 2*
