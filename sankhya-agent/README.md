# Walkthrough — Sankhya Super Agent (SSA)

## Fase 1: Setup & Autenticação (Concluída)

- **Estrutura:** Projeto criado em `sankhya-agent/`
- **Auth:** OAuth 2.0 (Client Credentials) validado
- **Teste:** Conexão com Gateway OK

## Fase 2: Ferramentas & Knowledge Base (Concluída)

- **Ferramentas MCP:** 8 ferramentas de leitura/diagnóstico (`tools.py`)
- **Segurança:** Validação SQL blindada (5 camadas)
- **Auditoria:** Logs em `logs/activity.log`
- **Knowledge Base:** Documentação da API e Schema Map

## Fase 3: Interface de Chat (Concluída)

- **UI:** Interface Web construída com Streamlit (`app.py`)
- **Cérebro:** Cliente Gemini (`agent_client.py`) que decide quais ferramentas usar
- **Fluxo:** Pergunta -> LLM -> Tool Call -> Resposta Formatada

## Fase 4: Inteligência de Negócio & BI (Concluída)

- **BI Conversacional:** SSA agora gera gráficos Plotly dinâmicos (Barra, Linha, Pizza) no chat.
- **Skill Especializada:** Analisador de compras (`procurement.py`) e Impacto de Produção.

## Fase 5: Fábrica de Agentes & Segurança (Concluída)

- **Auto-Expansão:** SSA cria novas ferramentas (`orchestrator.py`) baseadas em descrições de tabelas.
- **Blindagem:** Validação estática de código (AST) para impedir execução de comandos perigosos.

## Fase 6: Monitoramento Proativo (Concluída)

- **Vigias (Watchers):** Sistema de monitoramento automático para notas pendentes e estoque crítico.
- **Painel de Alertas:** Relatórios gerados proativamente para evitar perdas financeiras.

---

## Estrutura do Projeto 📂

- `app.py`: Interface Streamlit (Entry point)
- `agent_client.py`: Lógica do cliente Gemini e orquestração de ferramentas
- `mcp_server/`: Servidor de ferramentas e lógica core do Sankhya
- `knowledge/`: Dicionário de dados e base de conhecimento
- `scripts/`: Scripts de utilidade e indexação
- `tests/`: Scripts de teste e validação
- `logs/`: Logs de auditoria e atividades

---

## Como Rodar o Agente 🚀

### 1. Configurar Chaves

Certifique-se de que o `.env` possui as credenciais do Sankhya e a chave do Gemini:

```ini
SANKHYA_API_URL=https://api.sankhya.com.br
SANKHYA_CLIENT_ID=...
SANKHYA_CLIENT_SECRET=...
SANKHYA_X_TOKEN=...
GEMINI_API_KEY=AIza...  <-- Adicione sua chave aqui
```

### 2. Iniciar a Interface

No terminal, dentro da pasta `sankhya-agent`:

```bash
streamlit run app.py
```

### 3. Usar

Acesse `http://localhost:8501` no navegador e converse com o agente:

- "Qual o saldo de estoque do produto 20?"
- "Quem é o parceiro 1?"
- "Me mostre as colunas da tabela TGFPRO"
