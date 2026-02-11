# Protocolo de Resiliência Sankhya

Este documento define o comportamento padrão que o Agente deve adotar ao encontrar erros técnicos ou de negócio durante a interação com a API Sankhya.

## Princípio Fundamental

**"Erros não são o fim, são inputs para a solução."**

Ao receber um erro (Exception, HTTP 400/500, ou mensagem de erro funcional como "ORA-xxxxx"), o Agente **NÃO DEVE** desistir imediatamente ou apenas repassar o erro ao usuário. Ele deve tentar se recuperar autonomamente.

## O Ciclo de Auto-Correção (OODA Loop)

1. **OBSERVAR (Observe)**
    * Capturar a mensagem de erro exata.
    * Identificar códigos-chave (ex: `ORA-20101`, `Campo 'CODPROD' obrigatório`).

2. **ORIENTAR (Orient)**
    * Consultar a **Base de Conhecimento** usando a ferramenta `search_solutions(query)`.
    * Usar a mensagem de erro como query principal.
    * Ler os snippets dos artigos retornados para entender o contexto (é um erro de cadastro? falta de saldo? regra fiscal?).

3. **DECIDIR (Decide)**
    * Se a solução for clara (ex: "Preencher campo X"), formular a correção.
    * Se a solução exigir dados que o Agente não tem, perguntar ao usuário (mas citando o artigo: "Segundo a doc, preciso do campo X").
    * Se não houver solução na KB, aí sim escalar o erro original.

4. **AGIR (Act)**
    * Reconstruir o payload da requisição com a correção aplicada.
    * Chamar a ferramenta novamente (`save_record`, `call_sankhya_service`, etc.).

## Exemplos de Cenários

### Cenário A: Erro de Banco de Dados

* **Erro:** `ORA-20101: O produto não possui Grupo informado.`
* **Ação do Agente:**
    1. Busca "ORA-20101 produto grupo" na KB.
    2. Encontra artigo explicando que `CODGRUPOPROD` é obrigatório na `TGFPRO`.
    3. Verifica o payload enviado e nota ausência do campo.
    4. Adiciona um grupo padrão ou pergunta ao usuário "Qual o grupo deste produto?" explicando o motivo.

### Cenário B: Erro de Processo

* **Erro:** `Nota fiscal rejeitada: Diferença de alíquota.`
* **Ação do Agente:**
    1. Busca "Rejeição diferença alíquota" na KB.
    2. Encontra artigo sobre parametrização de TOP ou Parceiro.
    3. Consulta a TOP usada na nota.
    4. Sugere ao usuário: "A TOP 1234 parece estar configurada errada para interestadual, conforme o artigo X. Deseja que eu verifique a configuração?"

---
> 🤖 **Regra de Ouro para o LLM:** Antes de dizer "Não consigo", diga "Deixe-me verificar na documentação como resolver este erro".
