# PLAN - Organize Workspace

Plano para organizar a estrutura de arquivos do projeto **Sankhya Super Agent**, movendo scripts utilitários, testes e logs para pastas dedicadas, mantendo a raiz limpa e profissional.

## 🎯 Success Criteria

- [ ] Raiz do projeto contendo apenas arquivos essenciais de configuração e entry-points.
- [ ] Scripts utilitários movidos para `scripts/`.
- [ ] Arquivos de teste e validação movidos para `tests/`.
- [ ] Arquivos de log movidos para `logs/`.
- [ ] `README.md` atualizado com a nova estrutura.
- [ ] Garantia de que os entry-points (`app.py`, `agent_client.py`) continuam funcionando.

## 🛠 Tech Stack

- **Shell:** Bash (macOS) para movimentação de arquivos.
- **Python:** Para ajustes pontuais de caminhos caso necessário.

## 📂 Proposed Structure

```text
sankhya-agent/
├── app.py (Entry point - Streamlit)
├── agent_client.py (Core client logic)
├── mcp_server/ (Core Engine - Mantido)
├── knowledge/ (Dicionário e KB - Mantido)
├── scripts/
│   ├── knowledge_indexer.py
│   ├── analyze_naming.py
│   └── temp_query.py
├── tests/
│   ├── test_proactivity.py
│   ├── test_procurement.py
│   └── verify_new_tools.py
├── logs/
│   └── activity.log
├── docs/
│   └── PLAN-organize-workspace.md
├── guidelines.md
├── requirements.txt
├── .env
└── README.md
```

## 📝 Task Breakdown

### Phase 1: Preparation

- **task_id:** preparation
- **name:** Criar diretórios necessários
- **agent:** orchestrator
- **priority:** P0
- **INPUT:** Estrutura proposta
- **OUTPUT:** Pastas `scripts/`, `tests/`, `logs/` criadas.
- **VERIFY:** `ls -d scripts tests logs` deve retornar sucesso.

### Phase 2: File Migration

- **task_id:** migration
- **name:** Mover arquivos para as novas pastas
- **agent:** orchestrator
- **priority:** P1
- **dependencies:** [preparation]
- **INPUT:** Arquivos na raiz
- **OUTPUT:** Arquivos movidos conforme o plano.
- **VERIFY:** `ls` na raiz não deve mostrar scripts utilitários ou testes.

### Phase 3: Documentation & Fixes

- **task_id:** docs_fix
- **name:** Atualizar documentação e paths
- **agent:** orchestrator
- **priority:** P2
- **dependencies:** [migration]
- **INPUT:** Nova estrutura
- **OUTPUT:** `README.md` atualizado; verificação de imports se necessário.
- **VERIFY:** Conteúdo do `README.md` reflete a nova estrutura.

## ✅ PHASE X: Final Verification

- [ ] Verificar se `python app.py` (ou comando equivalente) inicia sem erros de import.
- [ ] Validar se `scripts/knowledge_indexer.py` ainda acessa a pasta `knowledge/` corretamente.
- [ ] Segurança: `security_scan.py` executado na nova estrutura.
