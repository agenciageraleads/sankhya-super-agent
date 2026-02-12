# 🗺️ Sankhya Super Agent (SSA) — Mapa de Capacidades

**Versão do Agente:** 2.0 (Gemini Powered)
**Status:** ✅ Operacional e Proativo
**Data da Auditoria:** 2026-02-12

---

## 1. Visão Geral (Resumo Executivo)

O SSA não é apenas um chatbot de SQL. Ele é uma **plataforma de inteligência** composta por um núcleo estático (Core Tools) e um sistema dinâmico de habilidades (Skills).

- **Total de Ferramentas Ativas:** ~34 ferramentas
- **Tabelas Mapeadas:** 35 tabelas principais (Comercial, Estoque, Financeiro, Fiscal)
- **Modo de Operação:** Proativo (OODA Loop + Auto-correção)

---

## 2. Inventário de Ferramentas (O Braço) 💪

### 🛠️ Core Tools (Nativas - `tools.py`)

Ferramentas de baixo nível para interação direta com o ERP.

| Ferramenta | Função | Segurança |
|---|---|---|
| `run_sql_select` | Executa consultas SQL livres | ✅ Leitura, Validação AST v5 |
| `load_records` | Consulta via API de Dados (mais robusto) | ✅ Leitura, API Oficial |
| `save_record` | Cria/Atualiza registros (Entidades liberadas) | 🔒 Escrita Controlada (Allowlist) |
| `call_sankhya_service` | Executa serviços de negócio (ações) | 🔒 Escrita Controlada (Allowlist) |
| `get_table_columns` | Consulta Dicionário de Dados (TDICAM) | ✅ Leitura |
| `list_tables` | Lista tabelas mapeadas no sistema | ✅ Leitura |
| `search_docs` | Pesquisa na Knowledge Base (texto) | ✅ Leitura |
| `search_solutions` | Pesquisa soluções de erros (ORA-...) | ✅ Leitura (DB Indexado) |
| `generate_chart_report` | Gera gráficos Plotly (Barra/Linha/Pizza) | ✅ Visualização |

### 🧠 Skills Especializadas (Dinâmicas - `mcp_server/skills/`)

Módulos de inteligência de negócio carregados dinamicamente.

#### 📦 Compras e Estoque (`procurement.py`)

- `get_purchase_suggestion(criteria)`: Gera sugestão de compra (Curva ABC).
- `get_product_purchasing_dossier(ids)`: Dossiê completo do produto (venda, estoque, custo).
- `get_stock_info(codprod)`: Consulta rápida de saldo e custo.

#### 💰 Financeiro e Vendas (`finance_ai.py`, `lenses.py`)

- `get_daily_sales_report(days)`: Relatório consolidado de vendas diárias.
- `get_consolidated_sales_lens`: Visão de vendas macro (3 meses).
- `get_finance_hotspot_lens`: Identifica pontos críticos financeiros.
- `analyze_productivity_by_unit`: Análise de produtividade/vendas por unidade.

#### 🔍 Diagnóstico e Auditoria (`*_helper.py`, `zendesk_connector.py`)

- `search_zendesk_help_center(query)`: **NOVO!** Busca soluções em TEMPO REAL na Central de Ajuda Sankhya (API Aberta).
- `diagnose_production_impact_issue`: Analisa impacto em produção.
- `diagnose_tgffcp_issue`: Diagnóstico fiscal (TGFFCP).
- `analyze_tgfpar_data`: Análise de cadastro de parceiros.
- `analyze_tsicta_data`: Análise de plano de contas.
- `analyze_tsiflp_data`: Análise financeira (TSIFLP).

#### 🤖 Meta-Cognição e Proatividade (`orchestrator.py`, `learning_engine.py`)

- `run_all_watchers`: Executa vigias ativos (notas pendentes, estoque crítico).
- `investigate_system_behavior`: Investigação autônoma de anomalias.
- **Fábrica de Ferramentas:** O agente pode **criar código**:
  - `propose_tool`, `create_agent_skill`, `publish_tool_proposal`.
- **Aprendizado de Erros:**
  - `propose_new_rule`: Aprende regras de correção (ex: ORA-00904) automaticamente.

---

## 3. Cobertura de Conhecimento (O Cérebro) 🧠

O agente possui conhecimento tático sobre as seguintes áreas do Sankhya (via `schema_map.json`):

### 📊 Comercial (Vendas/Compras)

- **TGFCAB** (Cabeçalho Notas), **TGFITE** (Itens), **TGFPAR** (Parceiros), **TGFPRO** (Produtos), **TGFTPV** (TOPs), **TGFTAB** (Tabelas Preço), **TGFVEN** (Vendedores).

### 📦 Estoque

- **TGFEST** (Saldo), **TGFCUS** (Custos), **TGFVOL** (Volumes), **TGFEXC** (Exceções).

### 💵 Financeiro

- **TGFFIN** (Financeiro), **TGFBOL** (Boletos), **TGFCBR** (Contas Banc.), **TSICTA** (Plano Contas), **TGFMBC** (Conciliação).

### ⚖️ Fiscal e Sistema

- **TGFIMP** (Impostos), **TGFDIN** (Importação), **TSIUSU** (Usuários), **TSIEMP** (Empresas), **TDICAM** (Dicionário).

---

## 4. Integrações Ativas 🔌

| Componente | Status | Detalhe |
|---|---|---|
| **Sankhya Gateway** | 🟢 Online | Autenticado via OAuth2 (Client Credentials) |
| **Google Gemini** | 🟢 Online | Modelo `gemini-2.0-flash` (Function Calling Ativo) |
| **Streamlit UI** | 🟢 Online | Interface de Chat com suporte a Tabelas e Gráficos |
| **Knowledge Base** | 🟢 Online | Base indexada (SQLite FTS5) para busca de erros |
| **Watcher Service** | 🟡 Manual | Executado sob demanda (`run_all_watchers`) |

---

## 5. Conclusão da Auditoria

O Sankhya Super Agent está **100% mapeado e funcional**.

- **Pontos Fortes:**
  - Capacidade de criar novas ferramentas (`orchestrator`).
  - Auto-correção de erros SQL (OODA Loop).
  - Cobertura completa das tabelas principais (Comercial/Estoque/Fin).
  - Skills avançadas de Compras e Diagnóstico.

- **Oportunidades:**
  - Ativar o `Watcher Service` como crontab/serviço background real.
  - Expandir cobertura para RH e Contabilidade (se necessário).
