# 📋 Especificação Técnica: Comprador Proativo

> **Versão**: 1.0
> **Data**: 13 de Fevereiro de 2026
> **Status**: Pronto para Implementação

---

## 🎯 Requisitos Funcionais Definidos

### **R1: Lógica de Priorização de Compras**

**Contexto**: Teto de compras limitado, precisa priorizar itens.

**Regra de Negócio:**

```python
def calcular_prioridade(item):
    """
    Priorização hierárquica:
    1. Curva ABC (A > B > C)
    2. Volume de cotações (demanda reprimida)
    3. Valor de vendas perdidas
    """
    score = 0

    # Peso por curva ABC (decisivo)
    if item['CURVA'] == 'A':
        score += 1000
    elif item['CURVA'] == 'B':
        score += 500
    elif item['CURVA'] == 'C':
        score += 100

    # Volume de cotações (secundário)
    score += item['QTD_ORCAMENTOS'] * 10

    # Vendas perdidas em R$ (terciário)
    score += item['VALOR_PERDIDO'] / 100

    return score
```

**Distribuição do Teto de Compras:**

```python
def distribuir_teto_compras(itens_priorizados, teto_total):
    """
    Distribui o teto proporcionalmente entre fornecedores e itens.
    """
    # 1. Ordenar por prioridade
    itens_sorted = sorted(itens_priorizados, key=lambda x: x['score'], reverse=True)

    # 2. Calcular proporção
    total_score = sum(item['score'] for item in itens_sorted)

    # 3. Distribuir teto proporcionalmente
    sugestao_final = []
    teto_usado = 0

    for item in itens_sorted:
        if teto_usado >= teto_total:
            break

        # Proporção baseada no score
        proporcao = item['score'] / total_score
        valor_alocado = min(
            item['VALOR_NECESSARIO'],
            (teto_total - teto_usado) * proporcao
        )

        if valor_alocado > 0:
            item['VALOR_ALOCADO'] = valor_alocado
            item['QTD_COMPRAR'] = valor_alocado / item['PRECO_MEDIO']
            sugestao_final.append(item)
            teto_usado += valor_alocado

    return sugestao_final, teto_usado
```

**Exemplo Prático:**

```
Teto de Compras: R$ 50.000

Itens Candidatos:
1. Cabo 4mm (A) - 25 cotações - R$ 15k perdido → Score: 1250
2. Disjuntor 32A (A) - 18 cotações - R$ 12k perdido → Score: 1180
3. Lâmpada LED (B) - 32 cotações - R$ 8k perdido → Score: 820
4. Abraçadeira (C) - 10 cotações - R$ 2k perdido → Score: 220

Distribuição:
- Cabo 4mm: 35% do teto = R$ 17.500
- Disjuntor 32A: 33% do teto = R$ 16.500
- Lâmpada LED: 23% do teto = R$ 11.500
- Abraçadeira: 9% do teto = R$ 4.500
```

---

### **R2: Regras de Comunicação**

**Horário de Operação:**

```python
HORARIOS_PERMITIDOS = {
    'dias_semana': [1, 2, 3, 4, 5],  # Segunda a Sexta (0=domingo)
    'hora_inicio': 8,
    'hora_fim': 18,
    'excluir_feriados': True
}

def pode_enviar_mensagem(timestamp):
    """
    Verifica se pode enviar mensagem no momento.
    """
    # Verificar dia da semana
    if timestamp.weekday() not in HORARIOS_PERMITIDOS['dias_semana']:
        return False, "Fim de semana - aguardar segunda-feira"

    # Verificar horário
    hora = timestamp.hour
    if not (HORARIOS_PERMITIDOS['hora_inicio'] <= hora < HORARIOS_PERMITIDOS['hora_fim']):
        return False, f"Fora do horário comercial (8h-18h)"

    # Verificar feriados
    if HORARIOS_PERMITIDOS['excluir_feriados'] and is_feriado(timestamp.date()):
        return False, "Feriado nacional - não enviar"

    return True, "OK para enviar"

def is_feriado(data):
    """
    Verifica se é feriado nacional.
    """
    FERIADOS_FIXOS = [
        (1, 1),   # Ano Novo
        (4, 21),  # Tiradentes
        (5, 1),   # Dia do Trabalho
        (9, 7),   # Independência
        (10, 12), # Nossa Senhora
        (11, 2),  # Finados
        (11, 15), # Proclamação da República
        (12, 25), # Natal
    ]

    # Feriados móveis (Carnaval, Sexta-feira Santa, Corpus Christi)
    # Pode usar biblioteca 'holidays' ou API

    return (data.month, data.day) in FERIADOS_FIXOS
```

**Agendamento Inteligente:**

```python
def agendar_envio(mensagem, tipo='rotina'):
    """
    Agenda envio para próximo horário válido.
    """
    agora = datetime.now()
    pode, motivo = pode_enviar_mensagem(agora)

    if pode:
        enviar_imediatamente(mensagem)
    else:
        # Calcular próximo horário válido
        proximo_horario = calcular_proximo_horario_valido(agora, tipo)
        agendar_para(mensagem, proximo_horario)
        log(f"Mensagem agendada para {proximo_horario}. Motivo: {motivo}")

def calcular_proximo_horario_valido(timestamp, tipo):
    """
    Encontra o próximo horário válido para envio.
    """
    if tipo == 'urgente':
        # Urgente: próxima hora comercial (pode ser mesmo dia)
        return proximo_horario_comercial(timestamp)
    else:
        # Rotina: próxima segunda 8h (se for fim de semana/feriado)
        return proxima_segunda_8h(timestamp)
```

---

### **R3: Modelo Multi-Agente com Decisão Centralizada**

**Arquitetura:**

```
┌────────────────────────────────────────────────────────────┐
│                  COMPRADOR SÊNIOR (Humano)                 │
│              Centraliza decisões e aprovações              │
└────────────────────────────────────────────────────────────┘
                            ↑
                   (Relatórios + Aprovações)
                            ↓
┌────────────────────────────────────────────────────────────┐
│              ORQUESTRADOR CENTRAL                          │
│         Roteia tarefas para agentes específicos            │
└────────────────────────────────────────────────────────────┘
              ↓              ↓              ↓
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ AGENTE CABOS     │ │ AGENTE ILUMINAÇÃO│ │ AGENTE PROTEÇÃO  │
│ - Cabos Flex     │ │ - LEDs           │ │ - Disjuntores    │
│ - Cabos 1KV      │ │ - Lâmpadas       │ │ - Quadros        │
│ - Fios           │ │ - Fitas LED      │ │ - DPS            │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

**Roteamento por Categoria:**

```python
CATEGORIAS_AGENTES = {
    'cabos': {
        'grupos': [101, 102, 103],  # CODGRUPOs de cabos
        'agente': 'comprador_cabos',
        'fornecedores_preferidos': [500, 750]
    },
    'iluminacao': {
        'grupos': [201, 202, 203],
        'agente': 'comprador_iluminacao',
        'fornecedores_preferidos': [600, 800]
    },
    'protecao': {
        'grupos': [301, 302],
        'agente': 'comprador_protecao',
        'fornecedores_preferidos': [450, 900]
    }
}

def rotear_tarefa(produto):
    """
    Roteia produto para agente especializado.
    """
    grupo = produto['CODGRUPOPROD']

    for categoria, config in CATEGORIAS_AGENTES.items():
        if grupo in config['grupos']:
            return config['agente']

    return 'comprador_geral'  # Fallback

def consolidar_sugestoes():
    """
    Consolida sugestões de múltiplos agentes para aprovação do sênior.
    """
    sugestoes_cabos = agente_cabos.gerar_sugestao()
    sugestoes_iluminacao = agente_iluminacao.gerar_sugestao()
    sugestoes_protecao = agente_protecao.gerar_sugestao()

    # Consolida tudo
    relatorio_consolidado = {
        'total_itens': len(sugestoes_cabos) + len(sugestoes_iluminacao) + len(sugestoes_protecao),
        'valor_total': sum_all_values(),
        'por_categoria': {
            'cabos': sugestoes_cabos,
            'iluminacao': sugestoes_iluminacao,
            'protecao': sugestoes_protecao
        }
    }

    # Envia para comprador sênior aprovar
    enviar_para_aprovacao(relatorio_consolidado, destinatario='comprador_senior')
```

**Benefício:** Equipe enxuta - Múltiplos agentes IA atuando, 1 humano decidindo.

---

### **R4: Detecção de Compras/Pedidos Existentes**

**Fonte de Dados:**

```python
def verificar_compras_recentes(codprod, dias=30):
    """
    Verifica se produto já foi comprado recentemente.
    Usa campo de compras pendentes da análise de giro.
    """
    giro = get_giro_data()

    item = next((x for x in giro if x['CODPROD'] == codprod), None)

    if not item:
        return {'tem_pendente': False}

    # Campo já vem da análise de giro
    compras_pendentes = item.get('COMPRAS_PENDENTES', 0)

    if compras_pendentes > 0:
        return {
            'tem_pendente': True,
            'qtd_pendente': compras_pendentes,
            'acao': 'SKIP',  # Não sugerir
            'motivo': f'Já existem {compras_pendentes} unidades em pedido pendente'
        }

    # Verificar notas de entrada recentes (últimos N dias)
    notas_recentes = """
        SELECT SUM(ITE.QTDNEG) as QTD_COMPRADA
        FROM TGFITE ITE
        JOIN TGFCAB CAB ON ITE.NUNOTA = CAB.NUNOTA
        WHERE ITE.CODPROD = :codprod
          AND CAB.TIPMOV = 'C'
          AND CAB.DTNEG >= TRUNC(SYSDATE) - :dias
          AND CAB.STATUSNOTA = 'L'
    """

    resultado = execute_query(notas_recentes, {'codprod': codprod, 'dias': dias})

    if resultado and resultado[0]['QTD_COMPRADA'] > 0:
        return {
            'tem_pendente': True,
            'qtd_comprada': resultado[0]['QTD_COMPRADA'],
            'acao': 'REDUZIR',  # Reduzir sugestão
            'motivo': f'Comprados {resultado[0]["QTD_COMPRADA"]} unidades nos últimos {dias} dias'
        }

    return {'tem_pendente': False}
```

**Integração na Sugestão:**

```python
def gerar_sugestao_semanal():
    itens_candidatos = calcular_itens_necessarios()

    sugestao_final = []
    for item in itens_candidatos:
        # Verificar pendências
        pendencia = verificar_compras_recentes(item['CODPROD'])

        if pendencia['tem_pendente']:
            if pendencia['acao'] == 'SKIP':
                # Pular este item
                log(f"Pulando {item['DESCRPROD']}: {pendencia['motivo']}")
                continue
            elif pendencia['acao'] == 'REDUZIR':
                # Reduzir quantidade sugerida
                item['QTD_SUGERIDA'] -= pendencia.get('qtd_comprada', 0)
                item['OBSERVACAO'] = pendencia['motivo']

        sugestao_final.append(item)

    return sugestao_final
```

---

### **R5: Gestão de Fornecedores**

**Abordagem:** Sempre perguntar ao comprador sobre fornecedores problemáticos.

```python
def selecionar_fornecedores(codprod):
    """
    Seleciona fornecedores para cotação, mas sempre pergunta antes.
    """
    # Buscar fornecedores históricos
    fornecedores = get_suppliers_for_product(
        ini=data_ano_passado(),
        fin=hoje(),
        empresa='1',
        codprod=codprod
    )

    if not fornecedores:
        return {'status': 'sem_historico', 'fornecedores': []}

    # Ranquear por volume/preço
    fornecedores_ranked = sorted(
        fornecedores,
        key=lambda x: (x['VOLUME_COMPRADO'], -x['PRECO_MEDIO']),
        reverse=True
    )

    # Pegar top 5
    top5 = fornecedores_ranked[:5]

    # Sempre perguntar ao comprador
    msg = f"""
📋 *Fornecedores para {produto_nome}*

Encontrei {len(fornecedores)} fornecedores no histórico.

*Top 5 sugeridos:*
"""

    for i, f in enumerate(top5, 1):
        msg += f"""
{i}. {f['RAZAOSOCIAL']}
   Volume: R$ {f['VOLUME_COMPRADO']:,.2f}
   Preço médio: R$ {f['PRECO_MEDIO']:.2f}
   Última compra: {f['DATA_ULTIMA_COMPRA']}
"""

    msg += """
*Algum fornecedor deve ser excluído?*
Responda: TODOS OK | EXCLUIR [nome/número]
"""

    send_whatsapp(comprador_whatsapp, msg)

    # Aguardar resposta
    return {'status': 'aguardando_confirmacao', 'fornecedores': top5}
```

**Blacklist Temporária (por sessão):**

```python
# Durante a conversa, comprador pode bloquear fornecedores
SESSION_BLACKLIST = []

def processar_resposta_fornecedor(resposta):
    """
    Processa resposta do comprador sobre fornecedores.
    """
    if "EXCLUIR" in resposta.upper():
        # Extrair nome/número do fornecedor
        fornecedor_bloqueado = extrair_fornecedor(resposta)
        SESSION_BLACKLIST.append(fornecedor_bloqueado)

        return f"✅ Fornecedor {fornecedor_bloqueado} excluído desta cotação"

    return "✅ Todos fornecedores confirmados"
```

---

### **R6: Formato Excel da Sugestão**

**Colunas Definidas:**

```python
EXCEL_COLUMNS = [
    'CODPROD',
    'PRODUTO',
    'CURVA',
    'ESTOQUE_ATUAL',
    'GIRO_30D',
    'GIRO_90D',              # ← NOVO
    'DATA_ULTIMA_COMPRA',    # ← NOVO
    'DATA_ULTIMA_VENDA',     # ← NOVO
    'QTD_ULTIMA_COMPRA',     # ← NOVO (para multiplos)
    'SUGESTAO_SISTEMA',      # ← NOVO (sugestão do Sankhya)
    'SUGESTAO_AGENTE',       # ← NOVO (sugestão da IA)
    'VALOR_UNIT',
    'VALOR_TOTAL',
    'FORNECEDOR_SELECIONADO', # ← Apenas 1
    'MOTIVO_FORNECEDOR',      # ← Explicação da escolha
    'JUSTIFICATIVA'           # ← Por que comprar
]
```

**Exemplo de Dados:**

```python
{
    'CODPROD': 1234,
    'PRODUTO': 'Cabo Flexível 4mm Vermelho',
    'CURVA': 'A',
    'ESTOQUE_ATUAL': 50,
    'GIRO_30D': 120,
    'GIRO_90D': 380,  # Sazonalidade
    'DATA_ULTIMA_COMPRA': '2026-01-15',
    'DATA_ULTIMA_VENDA': '2026-02-12',
    'QTD_ULTIMA_COMPRA': 500,  # Última vez compramos 500m
    'SUGESTAO_SISTEMA': 200,   # Sankhya sugere 200m
    'SUGESTAO_AGENTE': 250,    # IA sugere 250m (considerou vendas perdidas)
    'VALOR_UNIT': 42.50,
    'VALOR_TOTAL': 10625.00,   # 250m × R$ 42.50
    'FORNECEDOR_SELECIONADO': 'ABC Elétrica',
    'MOTIVO_FORNECEDOR': 'Melhor histórico nos últimos 6 meses + menor preço',
    'JUSTIFICATIVA': '25 cotações perdidas no último mês (R$ 15.200). Giro 90d mostra sazonalidade alta. Recomendo comprar acima do sistema.'
}
```

**Lógica de Escolha de Fornecedor:**

```python
def escolher_fornecedor(fornecedores):
    """
    Escolhe 1 fornecedor baseado em critérios objetivos.
    """
    if len(fornecedores) == 1:
        return fornecedores[0], "Único fornecedor histórico"

    # Score composto
    for f in fornecedores:
        score = 0

        # Preço (40%)
        preco_normalizado = 1 - (f['PRECO_MEDIO'] / max_preco)
        score += preco_normalizado * 0.4

        # Volume histórico (30%)
        volume_normalizado = f['VOLUME_COMPRADO'] / max_volume
        score += volume_normalizado * 0.3

        # Recência (20%)
        dias_ultima_compra = (hoje() - f['DATA_ULTIMA_COMPRA']).days
        recencia_normalizada = 1 - min(dias_ultima_compra / 365, 1)
        score += recencia_normalizada * 0.2

        # Frequência (10%)
        frequencia_normalizada = f['QTD_PEDIDOS'] / max_pedidos
        score += frequencia_normalizada * 0.1

        f['SCORE'] = score

    melhor = max(fornecedores, key=lambda x: x['SCORE'])

    # Gerar justificativa
    motivos = []
    if melhor['PRECO_MEDIO'] == min(f['PRECO_MEDIO'] for f in fornecedores):
        motivos.append("menor preço")
    if melhor['VOLUME_COMPRADO'] == max(f['VOLUME_COMPRADO'] for f in fornecedores):
        motivos.append("maior volume histórico")
    if dias_ultima_compra < 90:
        motivos.append("compra recente")

    motivo = " + ".join(motivos) if motivos else "melhor score geral"

    return melhor, motivo
```

---

### **R7: Tratamento de Erros**

**Políticas por Tipo:**

```python
ERROR_POLICIES = {
    'whatsapp_offline': {
        'retry': 3,
        'backoff': [5, 15, 30],  # minutos
        'fallback': 'email',
        'fallback_to': 'sandro@portaldistribuidora.com.br'
    },
    'sankhya_timeout': {
        'retry': 3,
        'wait': 3600,  # 1 hora em segundos
        'log_level': 'WARNING'
    },
    'dados_inconsistentes': {
        'action': 'analyze_and_report',
        'skip_item': True,
        'notify': True
    },
    'erro_desconhecido': {
        'action': 'emergency_stop',
        'notify': 'Lucas Borges',
        'find_contact': 'whatsapp_contacts'  # Buscar nos contatos
    }
}
```

**Implementação:**

```python
def handle_whatsapp_error(error, mensagem):
    """
    Trata erro de WhatsApp com fallback para email.
    """
    policy = ERROR_POLICIES['whatsapp_offline']

    for attempt in range(policy['retry']):
        try:
            time.sleep(policy['backoff'][attempt] * 60)
            send_whatsapp(mensagem)
            return True
        except Exception as e:
            log(f"Tentativa {attempt + 1} falhou: {e}")

    # Fallback: Email
    log("WhatsApp falhou após 3 tentativas. Usando fallback: Email")
    send_email(
        to=policy['fallback_to'],
        subject="[COMPRADOR] Notificação via Email (WhatsApp offline)",
        body=mensagem['text'],
        attachments=mensagem.get('media')
    )

def handle_sankhya_timeout(query):
    """
    Trata timeout do Sankhya com wait de 1h.
    """
    policy = ERROR_POLICIES['sankhya_timeout']

    for attempt in range(policy['retry']):
        try:
            return execute_query(query)
        except TimeoutError:
            if attempt < policy['retry'] - 1:
                log(f"Sankhya timeout. Aguardando {policy['wait'] / 3600}h...")
                time.sleep(policy['wait'])
            else:
                raise

def handle_dados_inconsistentes(item, inconsistencia):
    """
    Analisa dados inconsistentes e reporta.
    """
    analise = f"""
⚠️ *Dados Inconsistentes Detectados*

Produto: {item['DESCRPROD']} (#{item['CODPROD']})

Inconsistência: {inconsistencia}

Análise:
{analisar_inconsistencia(item, inconsistencia)}

Ação tomada: Item excluído da sugestão desta semana.

Verificar manualmente no Sankhya.
    """

    send_whatsapp(comprador_whatsapp, analise)
    log_inconsistencia(item, inconsistencia)

def handle_erro_desconhecido(error):
    """
    Para tudo e notifica Lucas Borges.
    """
    # Buscar contato do Lucas nos contatos WhatsApp
    lucas_numero = buscar_contato_whatsapp("Lucas Borges")

    if not lucas_numero:
        lucas_numero = "5511999999999"  # Fallback

    mensagem_emergencia = f"""
🚨 *ERRO CRÍTICO - SISTEMA PAUSADO*

Erro desconhecido detectado:
```
{str(error)}
```

O sistema foi pausado automaticamente.

Verificar logs e reiniciar manualmente.

Timestamp: {datetime.now()}
    """

    send_whatsapp(lucas_numero, mensagem_emergencia)

    # Parar scheduler
    scheduler.pause()

    raise SystemError(f"Sistema pausado devido a erro desconhecido: {error}")
```

---

### **R8: Auditoria e Logs**

**Nível Básico:**

```python
# Estrutura do log
LOG_ENTRY = {
    'timestamp': '2026-02-13T08:00:00',
    'action': 'sugestao_semanal',
    'autonomy_level': 3,
    'user': 'comprador_senior',
    'status': 'success',  # success | pending | failed
    'summary': {
        'itens_sugeridos': 15,
        'valor_total': 45000,
        'fornecedores_contatados': 8
    },
    'approval': {
        'required': True,
        'approved': True,
        'timestamp': '2026-02-13T08:15:00'
    }
}

def log_action(action, data, status='success'):
    """
    Registra ação no log básico (JSON).
    """
    log_file = f"logs/procurement_{datetime.now().strftime('%Y%m')}.json"

    entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'autonomy_level': autonomy_manager.get_current_level(),
        'status': status,
        'data': data
    }

    # Append to JSON file
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')

    # Também log no console
    logger.info(f"[{action}] {status}: {json.dumps(data)}")
```

**Retenção:** 90 dias (depois compacta/arquiva)

---

### **R9: Estratégia de Testes**

**Filosofia:** "Consertar o pneu com o carro andando"

```python
# Sem ambiente de staging
# Sem dry-run mode
# Testes = Produção real

# MAS: Com safeguards mínimos
SAFEGUARDS = {
    'max_valor_cotacao_sem_aprovacao': 5000,  # Acima disso, sempre aprovar
    'max_fornecedores_por_rodada': 10,        # Evitar spam
    'intervalo_minimo_envios': 300,           # 5 min entre mensagens
}

def validar_antes_executar(acao):
    """
    Validações mínimas antes de executar em produção.
    """
    if acao['tipo'] == 'cotacao' and acao['valor_total'] > SAFEGUARDS['max_valor_cotacao_sem_aprovacao']:
        return False, "Valor muito alto - requer aprovação manual"

    if acao['qtd_mensagens'] > SAFEGUARDS['max_fornecedores_por_rodada']:
        return False, "Muitas mensagens - verificar"

    return True, "OK"
```

**Aprendizado Contínuo:**
- Erros → Feedback negativo → Ajuste de autonomia
- Acertos → Feedback positivo → Ganho de autonomia
- Sistema aprende com erros reais

---

### **R10: Métricas de Sucesso**

**Dashboard de Métricas:**

```python
METRICAS = {
    'reducao_rupturas': {
        'meta': 0.95,  # > 95% de cobertura em itens A
        'calculo': lambda: (itens_a_sem_falta / total_itens_a)
    },
    'economia_compras': {
        'meta': 1.10,  # +10% economia vs compra manual
        'calculo': lambda: (preco_atual / preco_historico)
    },
    'tempo_economizado': {
        'meta': 10,  # 10h+ por semana
        'calculo': lambda: horas_antes - horas_depois
    },
    'taxa_conversao': {
        'meta': 0.60,  # > 60% cotações viram compras
        'calculo': lambda: (compras_efetivadas / cotacoes_enviadas)
    },
    'acuracia_previsao': {
        'meta': 0.80,  # > 80% sugestão bate com necessidade
        'calculo': lambda: (sugestoes_corretas / total_sugestoes)
    },
    'feedbacks_corretivos': {
        'meta': 'decrescente',
        'calculo': lambda: count_feedbacks_negativos_30d()
    }
}

def gerar_relatorio_metricas():
    """
    Gera relatório semanal de métricas.
    """
    relatorio = "📊 *Relatório Semanal - Comprador Autônomo*\n\n"

    for metrica, config in METRICAS.items():
        valor_atual = config['calculo']()
        meta = config['meta']

        if isinstance(meta, float):
            status = "✅" if valor_atual >= meta else "⚠️"
            relatorio += f"{status} {metrica}: {valor_atual:.1%} (meta: {meta:.1%})\n"
        else:
            relatorio += f"📈 {metrica}: {valor_atual}\n"

    return relatorio
```

**Skill de Negociação (Futura):**

```python
# Placeholder para futura implementação
def skill_negociacao():
    """
    Analisa cotações recebidas e sugere contra-propostas.

    Funcionalidades futuras:
    - Comparar preços entre fornecedores
    - Identificar outliers (preços muito altos)
    - Sugerir contra-proposta baseada em histórico
    - Negociar descontos por volume
    """
    pass
```

---

## 📅 Cronograma de Implementação

### **Sprint 1: Fundação (Semana 1)**
- [ ] Scheduler (APScheduler)
- [ ] Autonomy Manager
- [ ] Sistema de logs básico
- [ ] Regras de horário/feriados

### **Sprint 2: Rotina Prioritária #1 (Semana 2)**
- [ ] Sugestão Semanal completa
- [ ] Geração de Excel com colunas definidas
- [ ] Lógica de priorização (ABC + cotações + perdas)
- [ ] Distribuição de teto de compras

### **Sprint 3: Cotação Automática (Semana 3)**
- [ ] Seleção de fornecedores
- [ ] Mapa de cotação
- [ ] Envio WhatsApp + aprovação
- [ ] Captura de respostas

### **Sprint 4: Monitor de Ruptura (Semana 4)**
- [ ] Análise diária de estoque
- [ ] Alertas de itens críticos
- [ ] Integração com sugestão

### **Sprint 5: Ajustes e Otimização (Semana 5)**
- [ ] Feedback loop refinado
- [ ] Tratamento de erros
- [ ] Métricas iniciais

---

## ✅ Checklist de Aceitação

Antes de considerar MVP completo:

- [ ] Sugestão semanal roda automaticamente (Segunda 8h)
- [ ] Excel gerado com todas as colunas corretas
- [ ] WhatsApp enviado apenas em horário comercial
- [ ] Sistema pede aprovação antes de enviar cotações
- [ ] Fornecedores confirmados antes de contato
- [ ] Logs registrados corretamente
- [ ] Erros tratados conforme política
- [ ] Feedbacks capturados e processados
- [ ] Autonomia ajustada baseado em taxa de acerto
- [ ] Métricas básicas funcionando

---

## 🚀 Pronto para Implementar

**Status**: ✅ Especificação Completa
**Aprovação**: Pendente
**Próximo Passo**: Implementar Sprint 1

---

*Documento criado em 13/02/2026 - Versão 1.0*
