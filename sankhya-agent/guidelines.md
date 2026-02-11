# SSA - Regras de Ouro (SOP)

## 1. SAFETY FIRST

- **Jamais** execute `UPDATE`, `DELETE` ou `INSERT` via SQL direto.
- Operações de escrita devem usar estritamente os serviços de negócio do Sankhya (`Service API`) para garantir integridade referencial, execução de triggers e validações de Java.

## 2. STATEFULNESS (Session Management)

- A API do Sankhya depende de um `JSESSIONID`.
- O servidor MCP deve manter a sessão viva e tratar a renovação automática do token se expirar.

## 3. EVIDÊNCIA E DIAGNÓSTICO

- Ao diagnosticar erros, baseie-se em logs, queries de dicionário de dados (`DDIC`) e metadados.
- **Não alucine causas.** Se a causa não for clara, utilize a ferramenta `search_docs` ou investigue triggers/procedures relacionadas.

## 4. FORMATO DE COMUNICAÇÃO

- Respostas que envolvam conjuntos de dados do banco devem ser apresentadas em tabelas Markdown claras.
- Toda falha de API deve incluir o retorno bruto (XML/JSON) para análise técnica se necessário.

## 5. CÓDIGO E PADRÕES

- Python 3.10+ tipado.
- Tratamento de exceções robusto para falhas de rede e timeouts do ERP.
