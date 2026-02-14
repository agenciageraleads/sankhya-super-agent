# 🤖 Arquitetura: Comprador Proativo e Autônomo

> **Objetivo**: Transformar o Comprador de analista passivo em assistente proativo capaz de substituir um auxiliar de compras real.

---

## 📋 Requisitos Definidos

### Modelo de Operação
- **P1**: Híbrido entre Agendado (Cron) + Event-Driven (Watchers)
- **P2**: Semi-autônomo (Nível 3) com evolução automática baseada em feedback
- **P3**: Ordem de prioridade:
  1. **B** - Sugestão Semanal (Segunda 8h)
  2. **D** - Cotação Automática (sob demanda)
  3. **A** - Monitor de Ruptura (Diária 8h)
  4. **C** - Análise de Vendas Perdidas (conforme necessário)
  5. **F** - Comparação de Preços (quando recebe cotações)
  6. **E** - Monitor Financeiro (antes de grandes compras)

### Comunicação
- **P4**: WhatsApp APENAS (via Evolution API)
- **P5**: Notificações no início do dia (8h), não no fim

### Sistema de Evolução
- **Monitorar feedbacks corretivos** do comprador
- **Menos correções** = mais autonomia automaticamente
- **Dashboard de maturidade** para visualizar evolução

---

## 🏗️ Arquitetura Híbrida

```
┌──────────────────────────────────────────────────────────────────┐
│                    COMPRADOR PROATIVO                            │
└──────────────────────────────────────────────────────────────────┘

LAYER 1: SCHEDULER (Rotinas Agendadas)
┌──────────────────────────────────────────────────────────────────┐
│  CRON JOBS                                                       │
│  ├─ Segunda 08:00  → Sugestão Semanal de Compra                 │
│  ├─ Diária 08:00   → Monitor de Ruptura                         │
│  ├─ Sexta 17:00    → Análise de Vendas Perdidas (semanal)       │
│  └─ Diária 09:00   → Check Financeiro (se há pendências)        │
└──────────────────────────────────────────────────────────────────┘
                              ↓
LAYER 2: ORCHESTRATOR (Decisão + Ação)
┌──────────────────────────────────────────────────────────────────┐
│  PROCUREMENT ORCHESTRATOR                                        │
│  ├─ Analisa dados (giro, popularidade, financeiro)              │
│  ├─ Aplica regras de negócio                                    │
│  ├─ Verifica autonomia atual (níveis de permissão)              │
│  ├─ Decide: Executar | Solicitar Aprovação | Apenas Informar   │
│  └─ Registra ação + contexto (para aprendizado)                 │
└──────────────────────────────────────────────────────────────────┘
                              ↓
LAYER 3: ACTIONS (Execução)
┌──────────────────────────────────────────────────────────────────┐
│  AÇÕES DISPONÍVEIS                                               │
│  ├─ Gerar Sugestão de Compra (Excel)                            │
│  ├─ Criar Mapa de Cotação                                       │
│  ├─ Enviar Cotação via WhatsApp (aprovação prévia)              │
│  ├─ Comparar Respostas                                          │
│  └─ Gerar Alertas/Relatórios                                    │
└──────────────────────────────────────────────────────────────────┘
                              ↓
LAYER 4: COMMUNICATION (WhatsApp Only)
┌──────────────────────────────────────────────────────────────────┐
│  EVOLUTION WHATSAPP API                                          │
│  ├─ Enviar mensagens formatadas                                 │
│  ├─ Enviar arquivos (Excel, PDF)                                │
│  ├─ Receber respostas (cotações de fornecedores)                │
│  └─ Capturar feedback do comprador                              │
└──────────────────────────────────────────────────────────────────┘
                              ↓
LAYER 5: LEARNING (Evolução Automática)
┌──────────────────────────────────────────────────────────────────┐
│  FEEDBACK LOOP & AUTONOMY MANAGER                                │
│  ├─ Registra cada ação executada                                │
│  ├─ Captura feedbacks corretivos ("não era isso", "errado")     │
│  ├─ Captura feedbacks positivos ("perfeito", "pode fazer")      │
│  ├─ Calcula taxa de acerto (últimos 30 dias)                    │
│  └─ Ajusta nível de autonomia automaticamente                   │
│                                                                  │
│  REGRA DE EVOLUÇÃO:                                              │
│  - Taxa de acerto > 90% por 30 dias → Sobe 1 nível              │
│  - Taxa de acerto < 70% por 15 dias → Desce 1 nível             │
│  - Sempre notifica comprador sobre mudança de nível              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Níveis de Autonomia (Evolutivos)

### Nível 1: Informativo (Inicial - 0-30 dias)
```
O que faz: Apenas análises e relatórios
Aprovação: Não requer
Exemplo: "Identifiquei que você perdeu R$ 15k em vendas de cabos"
```

### Nível 2: Consultivo (30-60 dias, >70% acerto)
```
O que faz: Análises + Sugestões com justificativa
Aprovação: Não requer
Exemplo: "Recomendo comprar 200m de Cabo 4mm pelos seguintes motivos..."
```

### Nível 3: Semi-autônomo ⭐ (60-90 dias, >80% acerto) **← COMEÇAMOS AQUI**
```
O que faz: Gera documentos (mapa cotação, sugestão)
Aprovação: Solicita antes de enviar
Exemplo: "Criei mapa de cotação para 15 produtos. Envio para os fornecedores?"
          [Sim] [Não] [Editar]
```

### Nível 4: Autônomo (90+ dias, >90% acerto)
```
O que faz: Envia cotações automaticamente
Aprovação: Notifica após executar
Exemplo: "Enviei mapa de cotação para 5 fornecedores (ABC, XYZ...)"
          "Você pode revisar em: [link]"
```

### Nível 5: Totalmente Autônomo (180+ dias, >95% acerto) **FUTURO**
```
O que faz: Fecha compras dentro de regras pré-aprovadas
Aprovação: Notifica após executar
Exemplo: "Comprei 100 unidades de Disjuntor 32A do fornecedor ABC"
          "Menor preço, estoque crítico, dentro do budget aprovado"
```

---

## 📅 Roadmap de Implementação

### **FASE 1: Fundação (Semana 1-2)** ✅ Parcialmente Completo

**O que fazer:**
- [x] Skills de análise (popularidade, fornecedores, financeiro) ✅
- [x] Integração WhatsApp ✅
- [ ] Sistema de agendamento (Cron Jobs)
- [ ] Autonomy Manager (controle de níveis)
- [ ] Feedback Loop (captura + registro)

**Entregável:**
- Scheduler funcionando
- Níveis 1-3 implementados
- Sistema de feedback básico

---

### **FASE 2: Rotinas Prioritárias (Semana 3-4)**

#### **1. Sugestão Semanal (Prioridade #1)**

**Trigger**: Segunda-feira 08:00

**Workflow:**
```python
def sugestao_semanal():
    # 1. Coletar dados
    giro = get_giro_data()
    vendas_perdidas = get_popularity_analysis(ini=ultima_semana, fin=hoje)
    financeiro = get_financial_procurement_balance(dias_horizonte=30)

    # 2. Aplicar lógica de negócio
    sugestoes = calcular_sugestoes(
        giro=giro,
        vendas_perdidas=vendas_perdidas,
        saude_financeira=financeiro,
        regras=business_rules
    )

    # 3. Gerar Excel
    planilha = gerar_excel_sugestao(sugestoes)

    # 4. Verificar nível de autonomia
    nivel = autonomy_manager.get_current_level()

    if nivel >= 3:  # Semi-autônomo
        # Envia para aprovação
        send_whatsapp(
            number=comprador_whatsapp,
            text=f"""
🤖 *Sugestão Semanal de Compra*

Analisei o giro, vendas perdidas e saúde financeira.

📊 *Resumo:*
- {len(sugestoes)} produtos identificados
- Valor total: R$ {total:,.2f}
- Impacto esperado: +R$ {impacto_vendas:,.2f} em vendas

Planilha anexa com detalhes.

*Devo enviar para os fornecedores?*
Responda: SIM | NÃO | EDITAR
            """,
            media=planilha
        )
    else:  # Apenas informativo
        send_whatsapp(
            number=comprador_whatsapp,
            text="Aqui está a análise semanal...",
            media=planilha
        )

    # 5. Registrar ação
    log_action(
        action='sugestao_semanal',
        nivel=nivel,
        requires_approval=(nivel < 4),
        data=sugestoes
    )
```

**Entregável:**
- Excel gerado automaticamente
- Mensagem WhatsApp formatada
- Aguarda resposta para prosseguir

---

#### **2. Cotação Automática (Prioridade #2)**

**Trigger**: Sob demanda (resposta "SIM" da sugestão semanal)

**Workflow:**
```python
def cotar_automaticamente(produtos: List[int]):
    # 1. Para cada produto, buscar fornecedores
    for codprod in produtos:
        fornecedores = get_suppliers_for_product(
            ini=ultimo_ano,
            fin=hoje,
            empresa='1',
            codprod=codprod
        )

        # 2. Criar mapa de cotação (Excel)
        mapa = criar_mapa_cotacao(
            produtos=[codprod],
            fornecedores=fornecedores[:5],  # Top 5
            template='padrao'
        )

        # 3. Enviar para cada fornecedor
        for fornecedor in fornecedores[:5]:
            telefone = obter_telefone(fornecedor['CODPARC'])

            send_whatsapp(
                number=telefone,
                text=f"""
Olá {fornecedor['RAZAOSOCIAL']},

Segue mapa de cotação para os seguintes produtos:
- {produto_descricao}

Prazo para resposta: 48h

Att,
Portal Distribuidora
                """,
                media=mapa
            )

        # 4. Registrar envio
        log_quotation_sent(
            codprod=codprod,
            fornecedores=[f['CODPARC'] for f in fornecedores],
            timestamp=now()
        )

    # 5. Notificar comprador
    send_whatsapp(
        number=comprador_whatsapp,
        text=f"✅ Cotações enviadas para {len(fornecedores)} fornecedores"
    )
```

---

#### **3. Monitor de Ruptura (Prioridade #3)**

**Trigger**: Diária 08:00

**Workflow:**
```python
def monitor_ruptura():
    # 1. Identificar produtos curva A em risco
    giro = get_giro_data()
    estoque_atual = get_group_stock_summary()

    itens_criticos = []
    for item in giro:
        if item['CURVA'] == 'A':
            estoque = estoque_atual.get(item['CODPROD'], 0)
            demanda_30d = item['GIRO_30D']

            # Cobertura < 15 dias?
            if estoque < (demanda_30d / 2):
                itens_criticos.append({
                    'produto': item['DESCRPROD'],
                    'estoque': estoque,
                    'demanda_30d': demanda_30d,
                    'dias_cobertura': (estoque / demanda_30d) * 30,
                    'urgencia': 'CRÍTICA' if estoque < (demanda_30d / 4) else 'ALTA'
                })

    if itens_criticos:
        # 2. Ordenar por urgência
        itens_criticos.sort(key=lambda x: x['dias_cobertura'])

        # 3. Notificar
        msg = f"""
⚠️ *ALERTA DE RUPTURA*

{len(itens_criticos)} produtos curva A em risco:

"""
        for item in itens_criticos[:5]:  # Top 5
            msg += f"""
📦 *{item['produto']}*
   Estoque: {item['estoque']:.0f} un
   Cobertura: {item['dias_cobertura']:.1f} dias
   Urgência: {item['urgencia']}

"""

        msg += "\n*Devo gerar cotação para estes itens?*"

        send_whatsapp(
            number=comprador_whatsapp,
            text=msg
        )
```

---

### **FASE 3: Funcionalidades Avançadas (Semana 5-6)**

#### **4. Análise de Vendas Perdidas**

**Trigger**: Sexta-feira 17:00 (semanal)

#### **5. Comparação de Preços**

**Trigger**: Quando recebe cotação de fornecedor (watcher WhatsApp)

#### **6. Monitor Financeiro**

**Trigger**: Antes de enviar cotações > R$ 50k

---

## 🔄 Sistema de Feedback Loop

### Estrutura de Dados

```python
# feedback_log.json
{
    "action_id": "uuid-123",
    "timestamp": "2026-02-13T08:00:00",
    "action_type": "sugestao_semanal",
    "autonomy_level": 3,
    "data": {
        "produtos_sugeridos": 15,
        "valor_total": 45000
    },
    "approval_required": true,
    "user_response": "SIM",  # ou "NÃO" ou "EDITAR"
    "feedback_type": "positive",  # positive | negative | neutral
    "execution_result": "success",
    "notes": null
}
```

### Captura de Feedback

```python
def capture_feedback(message_from_user: str, context_action_id: str):
    """
    Analisa mensagem do comprador e classifica feedback.
    """
    message_lower = message_from_user.lower()

    # Feedbacks positivos
    positive_patterns = [
        r'\b(sim|ok|pode|perfeito|correto|ótimo|bom)\b',
        r'\b(aprovo|aprovado|está bom)\b'
    ]

    # Feedbacks negativos
    negative_patterns = [
        r'\b(não|nao|errado|incorreto)\b',
        r'\b(não era isso|não é isso)\b',
        r'\b(refaça|refaz|muda)\b'
    ]

    feedback_type = 'neutral'
    for pattern in positive_patterns:
        if re.search(pattern, message_lower):
            feedback_type = 'positive'
            break

    for pattern in negative_patterns:
        if re.search(pattern, message_lower):
            feedback_type = 'negative'
            break

    # Registrar
    update_feedback_log(
        action_id=context_action_id,
        feedback_type=feedback_type,
        user_message=message_from_user
    )

    # Atualizar métricas
    autonomy_manager.update_metrics(feedback_type)
```

### Autonomy Manager

```python
class AutonomyManager:
    def __init__(self):
        self.current_level = 3  # Começamos no semi-autônomo
        self.min_level = 1
        self.max_level = 5

    def get_current_level(self) -> int:
        return self.current_level

    def update_metrics(self, feedback_type: str):
        """Atualiza métricas e ajusta nível se necessário."""
        # Pegar últimos 30 dias
        recent_actions = get_actions_last_n_days(30)

        total = len(recent_actions)
        if total < 20:  # Precisa de pelo menos 20 ações
            return

        positive = sum(1 for a in recent_actions if a['feedback_type'] == 'positive')
        negative = sum(1 for a in recent_actions if a['feedback_type'] == 'negative')

        taxa_acerto = (positive / total) * 100

        # Decisão de evolução
        if taxa_acerto > 90 and self.current_level < self.max_level:
            self._level_up(taxa_acerto)
        elif taxa_acerto < 70 and self.current_level > self.min_level:
            self._level_down(taxa_acerto)

    def _level_up(self, taxa_acerto: float):
        """Sobe um nível de autonomia."""
        old_level = self.current_level
        self.current_level += 1

        send_whatsapp(
            number=comprador_whatsapp,
            text=f"""
🎉 *EVOLUÇÃO DE AUTONOMIA*

Sua taxa de acerto nos últimos 30 dias foi de {taxa_acerto:.1f}%!

Nível anterior: {old_level}
Novo nível: {self.current_level}

{self._get_level_description(self.current_level)}

Continue dando feedbacks para eu aprender mais! 🤖
            """
        )

        log_autonomy_change(old_level, self.current_level, taxa_acerto)

    def _level_down(self, taxa_acerto: float):
        """Desce um nível de autonomia."""
        old_level = self.current_level
        self.current_level -= 1

        send_whatsapp(
            number=comprador_whatsapp,
            text=f"""
⚠️ *AJUSTE DE AUTONOMIA*

Taxa de acerto nos últimos 30 dias: {taxa_acerto:.1f}%

Para sua segurança, estou reduzindo minha autonomia:

Nível anterior: {old_level}
Novo nível: {self.current_level}

{self._get_level_description(self.current_level)}

Vou pedir mais aprovações até melhorar! 🤖
            """
        )

        log_autonomy_change(old_level, self.current_level, taxa_acerto)

    def _get_level_description(self, level: int) -> str:
        descriptions = {
            1: "Apenas análises e relatórios",
            2: "Análises + Sugestões",
            3: "Gero documentos, mas peço aprovação antes de enviar",
            4: "Envio cotações automaticamente, notificando depois",
            5: "Posso fechar compras dentro das regras pré-aprovadas"
        }
        return descriptions.get(level, "")
```

---

## 📊 Dashboard de Evolução (Opcional - Futuro)

```
┌─────────────────────────────────────────────────────────┐
│  EVOLUÇÃO DO COMPRADOR AUTÔNOMO                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Nível Atual: 3 (Semi-autônomo)                        │
│  Taxa de Acerto (30d): 87.5%                           │
│  Ações Executadas: 52                                  │
│  Feedbacks Positivos: 48                               │
│  Feedbacks Negativos: 4                                │
│                                                         │
│  Progresso para Nível 4:                               │
│  ████████░░ 85% (precisa 90%)                          │
│                                                         │
│  Últimas Ações:                                         │
│  ✅ Sugestão Semanal - 13/02 08:00 - Aprovado          │
│  ✅ Cotação Cabos - 12/02 14:30 - Sucesso              │
│  ❌ Sugestão Disjuntores - 11/02 09:15 - Corrigido     │
│  ✅ Monitor Ruptura - 10/02 08:00 - Aprovado           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Próximos Passos

### Implementação Imediata (Esta Semana)

1. **Criar Scheduler**
   - `procurement_scheduler.py`
   - Integração com APScheduler ou similar
   - Cron jobs para rotinas definidas

2. **Autonomy Manager**
   - `autonomy_manager.py`
   - Sistema de níveis
   - Feedback loop

3. **Sugestão Semanal (MVP)**
   - Workflow completo
   - Geração de Excel
   - Envio WhatsApp com aprovação

### Teste Piloto (Próxima Semana)

- Rodar em produção por 1 semana
- Coletar feedbacks reais
- Ajustar algoritmos
- Validar taxa de acerto

### Escala (Semana 3+)

- Implementar rotinas 2-6
- Dashboard de evolução
- Refinamento contínuo

---

**Quer que eu implemente o MVP agora?** 🚀

Posso começar por:
1. Scheduler + Autonomy Manager
2. Sugestão Semanal (rotina completa)
3. Sistema de feedback

**Ou prefere revisar/ajustar a arquitetura primeiro?**
