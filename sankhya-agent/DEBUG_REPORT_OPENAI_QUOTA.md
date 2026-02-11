# 🔍 Debug Report: Quota OpenAI Excedida

**Data:** 2026-02-10  
**Status:** ✅ Resolvido (com workaround)

---

## 1. Problema Identificado

### Sintoma

- Sistema exibindo "[MODO FALLBACK - ERRO OPENAI]"
- Respostas limitadas ao modo simulação
- Mensagem: "Nenhum resultado encontrado para 'ssa, como foram as vendas hoje? qual vendedor vendeu mais?'"

### Erro Real

```
Error code: 429 - insufficient_quota
You exceeded your current quota, please check your plan and billing details.
```

---

## 2. Causa Raiz

🎯 **A conta OpenAI atingiu o limite de uso/créditos disponíveis**

**Não é um problema de configuração:**

- ✅ API Key está correta no `.env`
- ✅ Sistema está carregando a chave corretamente
- ✅ Conexão com OpenAI está funcionando
- ❌ Quota de uso foi excedida

---

## 3. Soluções Implementadas

### 3.1 Melhorias no Tratamento de Erros

**Arquivo:** `agent_client.py`

**Mudanças:**

1. **Detecção específica de erro 429:** Sistema agora identifica quando o problema é quota excedida
2. **Mensagem clara para o usuário:** Informa sobre o problema e como resolver
3. **Modo simulação aprimorado:** Detecta mais tipos de perguntas e tenta usar `search_docs`

**Antes:**

```python
except Exception as e:
    logger.warning(f"Falha na OpenAI ({str(e)}). Entrando em modo FALLBACK (Simulação).")
    return f"⚠️ **[MODO FALLBACK - ERRO OPENAI]**\n\n{run_simulation(last_user_msg)}"
```

**Depois:**

```python
except Exception as e:
    error_msg = str(e)
    
    # Detecta erro de quota excedida (429)
    if "429" in error_msg or "insufficient_quota" in error_msg:
        fallback_prefix = "⚠️ **[MODO FALLBACK - QUOTA OPENAI EXCEDIDA]**\n\n" \
                        "💡 *A conta OpenAI atingiu o limite de uso. Adicione créditos em https://platform.openai.com/account/billing*\n\n"
    else:
        fallback_prefix = f"⚠️ **[MODO FALLBACK - ERRO OPENAI]**\n\n*Erro: {error_msg}*\n\n"
```

### 3.2 Modo Simulação Expandido

**Novos padrões detectados:**

- ✅ Perguntas sobre vendas: "como foram as vendas", "qual vendedor vendeu mais"
- ✅ Perguntas sobre faturamento: "quanto faturou", "receita"
- ✅ Perguntas genéricas com "?", "quem", "qual", "quando", "onde", "por que"

**Estratégia:** Quando não consegue usar a IA, tenta usar `search_docs` para buscar na base de conhecimento.

---

## 4. Como Resolver Definitivamente

### Opção 1: Adicionar Créditos (Recomendado)

1. Acesse: <https://platform.openai.com/account/billing>
2. Adicione um método de pagamento
3. Configure limites de uso (opcional)
4. Aguarde alguns minutos para a quota ser restaurada

### Opção 2: Usar Modo Simulação Temporariamente

O sistema continua funcionando em modo básico:

- ✅ Consultas diretas (produto, parceiro, nota)
- ✅ Busca em documentação
- ✅ Queries SQL diretas
- ❌ Sem interpretação avançada de linguagem natural
- ❌ Sem aprendizado contextual

---

## 5. Comandos Disponíveis no Modo Simulação

```
✅ Funcionam:
- "Saldo do produto 20"
- "Parceiro 1"
- "Nota 12345"
- "Colunas da TGFPRO"
- "Como consultar notas?"
- "Como foram as vendas hoje?" (usa search_docs)
- "SQL SELECT * FROM TGFCAB WHERE ROWNUM <= 5"

❌ Não funcionam (precisam de IA):
- Perguntas complexas com contexto
- Análises comparativas
- Sugestões baseadas em histórico
```

---

## 6. Prevenção Futura

### Monitoramento de Quota

Adicionar verificação proativa:

```python
# TODO: Implementar verificação de quota antes de fazer requisições
# Endpoint: GET https://api.openai.com/v1/usage
```

### Alertas

Configurar alertas na OpenAI:

1. Acesse: <https://platform.openai.com/account/limits>
2. Configure notificações quando atingir 80% da quota

---

## 7. Status Atual

✅ **Sistema funcionando em modo FALLBACK**

- Mensagens de erro mais claras
- Modo simulação aprimorado
- Usuário informado sobre como resolver

⏳ **Aguardando:**

- Adição de créditos na conta OpenAI
- Ou decisão de manter em modo simulação

---

## 8. Logs Relevantes

```
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
WARNING:ssa-client:Quota OpenAI excedida. Entrando em modo FALLBACK (Simulação).
```

---

**Próximos Passos:**

1. ✅ Código atualizado com melhor tratamento de erros
2. ⏳ Aguardando decisão sobre créditos OpenAI
3. 📝 Documentar comandos do modo simulação para usuários finais
