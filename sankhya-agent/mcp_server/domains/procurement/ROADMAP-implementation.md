# 🚀 Roadmap de Implementação: Comprador Proativo e Autônomo

> **Documento Base para Desenvolvimento**
> Cronograma detalhado de 5 sprints para implementação completa do sistema de compras proativo.

---

## 📋 Índice

1. [Visão Geral](#-visão-geral)
2. [Estrutura de Pastas](#-estrutura-de-pastas)
3. [Sprint 1: Fundação](#-sprint-1-fundação-semana-1)
4. [Sprint 2: Sugestão Semanal](#-sprint-2-sugestão-semanal-semana-2)
5. [Sprint 3: Cotação Automática](#-sprint-3-cotação-automática-semana-3)
6. [Sprint 4: Monitor de Ruptura](#-sprint-4-monitor-de-ruptura-semana-4)
7. [Sprint 5: Análise de Vendas Perdidas](#-sprint-5-análise-de-vendas-perdidas-semana-5)
8. [Checklist Final](#-checklist-final)
9. [Como Executar](#-como-executar)

---

## 🎯 Visão Geral

### Objetivo
Transformar o COMPRADOR de analista passivo em assistente proativo capaz de substituir um auxiliar de compras real.

### Modelo Operacional
- **Híbrido**: APScheduler (Cron) + Event-Driven (Watchers)
- **Autonomia**: Nível 3 (Semi-autônomo) com evolução automática
- **Comunicação**: WhatsApp via Evolution API

### Métricas de Sucesso
- Taxa de ruptura de estoque < 5% para curva A
- 80% das sugestões aceitas pelo comprador
- Redução de 30% no tempo gasto em cotações manuais
- ROI positivo em 90 dias

---

## 📁 Estrutura de Pastas

```
sankhya-agent/mcp_server/domains/procurement/
├── services/
│   ├── sankhya_adapter.py          (existente - 349 linhas)
│   ├── evolution_service.py        (existente)
│   ├── scheduler_service.py        (🆕 Sprint 1)
│   ├── autonomy_manager.py         (🆕 Sprint 1)
│   └── excel_generator.py          (🆕 Sprint 2)
├── workflows/
│   ├── sugestao_semanal.py         (🆕 Sprint 2)
│   ├── cotacao_automatica.py       (🆕 Sprint 3)
│   ├── monitor_ruptura.py          (🆕 Sprint 4)
│   └── analise_vendas_perdidas.py  (🆕 Sprint 5)
├── rules/
│   ├── business_rules.yaml         (existente)
│   ├── communication_rules.yaml    (🆕 Sprint 1)
│   └── queries_*.sql               (existente - 16 queries)
├── logs/
│   ├── actions/                    (🆕 Sprint 1)
│   ├── feedback/                   (🆕 Sprint 1)
│   └── errors/                     (🆕 Sprint 1)
├── templates/
│   └── excel_cotacao.xlsx          (🆕 Sprint 2)
└── tests/
    ├── test_scheduler.py           (🆕 Sprint 1)
    ├── test_autonomy.py            (🆕 Sprint 1)
    ├── test_sugestao_semanal.py    (🆕 Sprint 2)
    ├── test_cotacao.py             (🆕 Sprint 3)
    └── test_monitor_ruptura.py     (🆕 Sprint 4)
```

---

## 🔧 Sprint 1: Fundação (Semana 1)

### Objetivos
- Sistema de agendamento funcional
- Autonomy Manager implementado
- Sistema de logs estruturado
- Validação de horários comerciais

### 📦 Entregas

#### 1.1 Scheduler Service (`scheduler_service.py`)

**Descrição:** Gerenciador de rotinas agendadas usando APScheduler.

**Arquivo:** `services/scheduler_service.py`

**Conteúdo:**
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from typing import Callable, Dict, List
import pytz

class ProcurementScheduler:
    def __init__(self, timezone: str = 'America/Sao_Paulo'):
        self.scheduler = BackgroundScheduler(timezone=timezone)
        self.timezone = pytz.timezone(timezone)
        self.logger = logging.getLogger(__name__)
        self.jobs: Dict[str, Dict] = {}

    def start(self):
        """Inicia o scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Scheduler iniciado")

    def stop(self):
        """Para o scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Scheduler parado")

    def add_job(
        self,
        job_id: str,
        func: Callable,
        cron_expression: str,
        args: tuple = (),
        kwargs: dict = None,
        description: str = ""
    ):
        """
        Adiciona um job agendado.

        Args:
            job_id: Identificador único do job
            func: Função a ser executada
            cron_expression: Expressão cron (ex: "0 8 * * 1")
            args: Argumentos posicionais
            kwargs: Argumentos nomeados
            description: Descrição do job
        """
        if kwargs is None:
            kwargs = {}

        trigger = CronTrigger.from_crontab(cron_expression, timezone=self.timezone)

        job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            args=args,
            kwargs=kwargs,
            id=job_id,
            name=description,
            replace_existing=True
        )

        self.jobs[job_id] = {
            'function': func.__name__,
            'cron': cron_expression,
            'description': description,
            'next_run': job.next_run_time
        }

        self.logger.info(f"Job '{job_id}' adicionado: {description}")
        return job

    def remove_job(self, job_id: str):
        """Remove um job agendado."""
        self.scheduler.remove_job(job_id)
        if job_id in self.jobs:
            del self.jobs[job_id]
        self.logger.info(f"Job '{job_id}' removido")

    def get_jobs(self) -> List[Dict]:
        """Retorna lista de jobs agendados."""
        return [
            {
                'id': job_id,
                **job_info
            }
            for job_id, job_info in self.jobs.items()
        ]

    def is_business_hours(self) -> bool:
        """
        Verifica se está em horário comercial.
        Segunda a Sexta, 8h-18h, exceto feriados.
        """
        now = datetime.now(self.timezone)

        # Verifica dia da semana (0=Segunda, 6=Domingo)
        if now.weekday() > 4:  # Sábado ou Domingo
            return False

        # Verifica horário (8h-18h)
        if now.hour < 8 or now.hour >= 18:
            return False

        # TODO: Verificar feriados brasileiros (integrar com biblioteca)
        return True


# Singleton instance
_scheduler_instance = None

def get_scheduler() -> ProcurementScheduler:
    """Retorna instância singleton do scheduler."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ProcurementScheduler()
    return _scheduler_instance
```

**Checklist:**
- [ ] Criar arquivo `services/scheduler_service.py`
- [ ] Implementar classe `ProcurementScheduler`
- [ ] Adicionar validação de horário comercial
- [ ] Implementar singleton `get_scheduler()`
- [ ] Adicionar logging estruturado

---

#### 1.2 Autonomy Manager (`autonomy_manager.py`)

**Descrição:** Sistema de níveis de autonomia que evolui com feedback.

**Arquivo:** `services/autonomy_manager.py`

**Conteúdo:**
```python
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging

class AutonomyManager:
    def __init__(self, storage_path: str = "logs/autonomy/state.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)

        # Níveis de autonomia
        self.levels = {
            1: {
                'name': 'Informativo',
                'description': 'Apenas análises e relatórios',
                'requires_approval': False,
                'can_execute': False
            },
            2: {
                'name': 'Consultivo',
                'description': 'Análises + Sugestões com justificativa',
                'requires_approval': False,
                'can_execute': False
            },
            3: {
                'name': 'Semi-autônomo',
                'description': 'Gera documentos, solicita aprovação antes de enviar',
                'requires_approval': True,
                'can_execute': True
            },
            4: {
                'name': 'Autônomo',
                'description': 'Envia cotações automaticamente, notifica depois',
                'requires_approval': False,
                'can_execute': True
            },
            5: {
                'name': 'Totalmente Autônomo',
                'description': 'Fecha compras dentro de regras pré-aprovadas',
                'requires_approval': False,
                'can_execute': True
            }
        }

        # Carregar estado
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Carrega estado do arquivo ou cria novo."""
        if self.storage_path.exists():
            with open(self.storage_path, 'r') as f:
                return json.load(f)

        # Estado inicial
        return {
            'current_level': 3,  # Começamos no semi-autônomo
            'start_date': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat(),
            'total_actions': 0,
            'positive_feedback': 0,
            'negative_feedback': 0,
            'neutral_feedback': 0,
            'level_history': [
                {
                    'level': 3,
                    'date': datetime.now().isoformat(),
                    'reason': 'Nível inicial'
                }
            ]
        }

    def _save_state(self):
        """Salva estado no arquivo."""
        self.state['last_update'] = datetime.now().isoformat()
        with open(self.storage_path, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_current_level(self) -> int:
        """Retorna nível de autonomia atual."""
        return self.state['current_level']

    def get_level_info(self, level: Optional[int] = None) -> Dict:
        """Retorna informações sobre um nível."""
        if level is None:
            level = self.get_current_level()
        return self.levels.get(level, {})

    def requires_approval(self, action_type: str) -> bool:
        """
        Verifica se ação requer aprovação no nível atual.

        Args:
            action_type: Tipo de ação (sugestao_semanal, cotacao, etc)
        """
        level = self.get_current_level()
        level_info = self.levels[level]

        return level_info['requires_approval']

    def register_action(
        self,
        action_id: str,
        action_type: str,
        data: Dict
    ):
        """
        Registra uma ação executada.

        Args:
            action_id: ID único da ação
            action_type: Tipo de ação
            data: Dados da ação
        """
        log_path = Path(f"logs/actions/{datetime.now().strftime('%Y-%m')}")
        log_path.mkdir(parents=True, exist_ok=True)

        log_file = log_path / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"

        entry = {
            'action_id': action_id,
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'autonomy_level': self.get_current_level(),
            'data': data,
            'feedback_type': None,
            'user_response': None
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        self.state['total_actions'] += 1
        self._save_state()

    def register_feedback(
        self,
        action_id: str,
        feedback_type: str,
        user_message: str
    ):
        """
        Registra feedback do usuário.

        Args:
            action_id: ID da ação
            feedback_type: 'positive', 'negative', 'neutral'
            user_message: Mensagem do usuário
        """
        # Atualizar contadores
        if feedback_type == 'positive':
            self.state['positive_feedback'] += 1
        elif feedback_type == 'negative':
            self.state['negative_feedback'] += 1
        else:
            self.state['neutral_feedback'] += 1

        self._save_state()

        # Verificar se deve ajustar nível
        self._evaluate_level_change()

        # Registrar em log de feedback
        log_path = Path(f"logs/feedback/{datetime.now().strftime('%Y-%m')}")
        log_path.mkdir(parents=True, exist_ok=True)

        log_file = log_path / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"

        entry = {
            'action_id': action_id,
            'timestamp': datetime.now().isoformat(),
            'feedback_type': feedback_type,
            'user_message': user_message
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def _evaluate_level_change(self):
        """Avalia se deve mudar nível de autonomia."""
        total = self.state['total_actions']

        # Precisa de pelo menos 20 ações
        if total < 20:
            return

        # Calcular taxa de acerto (últimos 30 dias)
        recent_stats = self._get_recent_stats(days=30)

        if recent_stats['total'] < 20:
            return

        taxa_acerto = (recent_stats['positive'] / recent_stats['total']) * 100

        current_level = self.get_current_level()

        # Decisão de evolução
        if taxa_acerto > 90 and current_level < 5:
            self._level_up(taxa_acerto)
        elif taxa_acerto < 70 and current_level > 1:
            self._level_down(taxa_acerto)

    def _get_recent_stats(self, days: int = 30) -> Dict:
        """Retorna estatísticas dos últimos N dias."""
        cutoff_date = datetime.now() - timedelta(days=days)

        positive = 0
        negative = 0
        neutral = 0
        total = 0

        # Ler logs de feedback
        feedback_dir = Path("logs/feedback")
        if not feedback_dir.exists():
            return {'total': 0, 'positive': 0, 'negative': 0, 'neutral': 0}

        for log_file in feedback_dir.glob("**/*.jsonl"):
            with open(log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    entry_date = datetime.fromisoformat(entry['timestamp'])

                    if entry_date >= cutoff_date:
                        total += 1
                        if entry['feedback_type'] == 'positive':
                            positive += 1
                        elif entry['feedback_type'] == 'negative':
                            negative += 1
                        else:
                            neutral += 1

        return {
            'total': total,
            'positive': positive,
            'negative': negative,
            'neutral': neutral
        }

    def _level_up(self, taxa_acerto: float):
        """Sobe um nível de autonomia."""
        old_level = self.get_current_level()
        new_level = old_level + 1

        self.state['current_level'] = new_level
        self.state['level_history'].append({
            'level': new_level,
            'date': datetime.now().isoformat(),
            'reason': f'Taxa de acerto {taxa_acerto:.1f}% nos últimos 30 dias'
        })

        self._save_state()

        self.logger.info(f"Autonomia aumentada: Nível {old_level} → {new_level}")

        # TODO: Notificar comprador via WhatsApp

    def _level_down(self, taxa_acerto: float):
        """Desce um nível de autonomia."""
        old_level = self.get_current_level()
        new_level = old_level - 1

        self.state['current_level'] = new_level
        self.state['level_history'].append({
            'level': new_level,
            'date': datetime.now().isoformat(),
            'reason': f'Taxa de acerto {taxa_acerto:.1f}% nos últimos 30 dias (abaixo de 70%)'
        })

        self._save_state()

        self.logger.warning(f"Autonomia reduzida: Nível {old_level} → {new_level}")

        # TODO: Notificar comprador via WhatsApp

    def get_dashboard_data(self) -> Dict:
        """Retorna dados para dashboard de evolução."""
        recent_stats = self._get_recent_stats(days=30)

        taxa_acerto = 0
        if recent_stats['total'] > 0:
            taxa_acerto = (recent_stats['positive'] / recent_stats['total']) * 100

        current_level = self.get_current_level()
        level_info = self.get_level_info()

        # Calcular progresso para próximo nível
        progresso = 0
        if current_level < 5:
            if taxa_acerto >= 90:
                progresso = 100
            else:
                progresso = (taxa_acerto / 90) * 100

        return {
            'current_level': current_level,
            'level_name': level_info['name'],
            'level_description': level_info['description'],
            'taxa_acerto_30d': round(taxa_acerto, 1),
            'total_actions': self.state['total_actions'],
            'positive_feedback': self.state['positive_feedback'],
            'negative_feedback': self.state['negative_feedback'],
            'neutral_feedback': self.state['neutral_feedback'],
            'progresso_proximo_nivel': round(progresso, 1),
            'level_history': self.state['level_history'][-5:]  # Últimas 5 mudanças
        }


# Singleton instance
_autonomy_instance = None

def get_autonomy_manager() -> AutonomyManager:
    """Retorna instância singleton do autonomy manager."""
    global _autonomy_instance
    if _autonomy_instance is None:
        _autonomy_instance = AutonomyManager()
    return _autonomy_instance
```

**Checklist:**
- [ ] Criar arquivo `services/autonomy_manager.py`
- [ ] Implementar classe `AutonomyManager`
- [ ] Implementar sistema de 5 níveis
- [ ] Implementar feedback loop
- [ ] Implementar cálculo de taxa de acerto
- [ ] Implementar evolução automática
- [ ] Criar estrutura de logs
- [ ] Implementar singleton `get_autonomy_manager()`

---

#### 1.3 Communication Rules (`communication_rules.yaml`)

**Descrição:** Regras de comunicação e horários comerciais.

**Arquivo:** `rules/communication_rules.yaml`

**Conteúdo:**
```yaml
# Regras de Comunicação - Comprador Proativo
horario_comercial:
  dias_semana: [0, 1, 2, 3, 4]  # Segunda a Sexta (0=Segunda)
  hora_inicio: 8
  hora_fim: 18
  timezone: 'America/Sao_Paulo'

  # Feriados nacionais brasileiros (atualizar anualmente)
  feriados_fixos:
    - '01-01'  # Ano Novo
    - '04-21'  # Tiradentes
    - '05-01'  # Dia do Trabalho
    - '09-07'  # Independência
    - '10-12'  # Nossa Senhora Aparecida
    - '11-02'  # Finados
    - '11-15'  # Proclamação da República
    - '12-25'  # Natal

  # Feriados móveis 2026 (atualizar anualmente)
  feriados_moveis:
    - '2026-02-16'  # Carnaval
    - '2026-02-17'  # Carnaval
    - '2026-04-03'  # Sexta-feira Santa
    - '2026-06-04'  # Corpus Christi

whatsapp:
  # Números de contato
  comprador_principal: '+5511999999999'
  comprador_backup: '+5511888888888'

  # Configurações de envio
  max_retries: 3
  retry_delay_seconds: 60
  timeout_seconds: 30

  # Fallback para email
  fallback_email:
    enabled: true
    smtp_server: 'smtp.gmail.com'
    smtp_port: 587
    from_email: 'comprador@empresa.com'
    to_email: 'lucas@empresa.com'

error_policies:
  whatsapp_falha:
    action: 'fallback_email'
    max_attempts: 3

  sankhya_timeout:
    action: 'aguardar_retry'
    wait_time_minutes: 60
    max_retries: 3

  sankhya_erro_critico:
    action: 'notificar_admin'
    stop_execution: true
```

**Checklist:**
- [ ] Criar arquivo `rules/communication_rules.yaml`
- [ ] Definir horários comerciais
- [ ] Listar feriados 2026
- [ ] Configurar WhatsApp
- [ ] Configurar fallback email
- [ ] Definir políticas de erro

---

#### 1.4 Sistema de Logs

**Descrição:** Estrutura de logs JSON para auditoria.

**Estrutura:**
```
logs/
├── actions/
│   └── 2026-02/
│       └── 2026-02-13.jsonl
├── feedback/
│   └── 2026-02/
│       └── 2026-02-13.jsonl
├── errors/
│   └── 2026-02/
│       └── 2026-02-13.jsonl
└── autonomy/
    └── state.json
```

**Formato de Log de Ação:**
```json
{
  "action_id": "uuid-123",
  "timestamp": "2026-02-13T08:00:00",
  "action_type": "sugestao_semanal",
  "autonomy_level": 3,
  "data": {
    "produtos_sugeridos": 15,
    "valor_total": 45000
  },
  "feedback_type": null,
  "user_response": null
}
```

**Checklist:**
- [ ] Criar estrutura de pastas `logs/`
- [ ] Implementar rotação de logs (90 dias)
- [ ] Adicionar logging em todos os serviços
- [ ] Testar gravação de logs

---

#### 1.5 Testes Sprint 1

**Arquivo:** `tests/test_scheduler.py`

```python
import pytest
from datetime import datetime
from services.scheduler_service import ProcurementScheduler, get_scheduler

def test_scheduler_singleton():
    """Testa se get_scheduler retorna mesma instância."""
    s1 = get_scheduler()
    s2 = get_scheduler()
    assert s1 is s2

def test_add_job():
    """Testa adição de job."""
    scheduler = ProcurementScheduler()

    def dummy_job():
        pass

    job = scheduler.add_job(
        job_id='test_job',
        func=dummy_job,
        cron_expression='0 8 * * 1',
        description='Test job'
    )

    assert job is not None
    assert 'test_job' in scheduler.jobs

def test_business_hours():
    """Testa validação de horário comercial."""
    scheduler = ProcurementScheduler()

    # TODO: Mock datetime para testar cenários específicos
    result = scheduler.is_business_hours()
    assert isinstance(result, bool)
```

**Arquivo:** `tests/test_autonomy.py`

```python
import pytest
from services.autonomy_manager import AutonomyManager, get_autonomy_manager

def test_autonomy_singleton():
    """Testa se get_autonomy_manager retorna mesma instância."""
    a1 = get_autonomy_manager()
    a2 = get_autonomy_manager()
    assert a1 is a2

def test_initial_level():
    """Testa nível inicial."""
    manager = AutonomyManager(storage_path='logs/test_autonomy.json')
    assert manager.get_current_level() == 3

def test_requires_approval():
    """Testa se ação requer aprovação."""
    manager = AutonomyManager(storage_path='logs/test_autonomy.json')

    # Nível 3 requer aprovação
    assert manager.requires_approval('sugestao_semanal') == True

def test_register_action():
    """Testa registro de ação."""
    manager = AutonomyManager(storage_path='logs/test_autonomy.json')

    manager.register_action(
        action_id='test-123',
        action_type='sugestao_semanal',
        data={'produtos': 10}
    )

    assert manager.state['total_actions'] > 0

def test_register_feedback():
    """Testa registro de feedback."""
    manager = AutonomyManager(storage_path='logs/test_autonomy.json')

    manager.register_feedback(
        action_id='test-123',
        feedback_type='positive',
        user_message='Perfeito!'
    )

    assert manager.state['positive_feedback'] > 0
```

**Checklist:**
- [ ] Criar `tests/test_scheduler.py`
- [ ] Criar `tests/test_autonomy.py`
- [ ] Implementar testes básicos
- [ ] Rodar pytest e garantir 100% pass

---

### ✅ Critérios de Aceitação Sprint 1

- [ ] Scheduler inicia e para sem erros
- [ ] Jobs podem ser adicionados via cron expression
- [ ] Validação de horário comercial funciona
- [ ] Autonomy Manager carrega/salva estado
- [ ] Nível inicial é 3 (Semi-autônomo)
- [ ] Feedback pode ser registrado
- [ ] Taxa de acerto é calculada corretamente
- [ ] Logs são gravados em formato JSON
- [ ] Testes passam com 100% de sucesso

---

## 📊 Sprint 2: Sugestão Semanal (Semana 2)

### Objetivos
- Implementar rotina de sugestão semanal de compra
- Gerar Excel com 16 colunas
- Integrar com WhatsApp
- Solicitar aprovação antes de enviar

### 📦 Entregas

#### 2.1 Excel Generator (`excel_generator.py`)

**Descrição:** Gerador de planilhas Excel para sugestões de compra.

**Arquivo:** `services/excel_generator.py`

**Conteúdo:**
```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from typing import List, Dict
from datetime import datetime
from pathlib import Path

class ExcelSugestaoCompra:
    def __init__(self):
        self.wb = None
        self.ws = None

    def gerar(self, sugestoes: List[Dict], output_path: str) -> str:
        """
        Gera planilha Excel com sugestões de compra.

        Args:
            sugestoes: Lista de dicionários com dados dos produtos
            output_path: Caminho para salvar arquivo

        Returns:
            Caminho do arquivo gerado
        """
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.title = "Sugestão de Compra"

        # Definir colunas
        headers = [
            "CODPROD",
            "PRODUTO",
            "CURVA",
            "ESTOQUE_ATUAL",
            "GIRO_30D",
            "GIRO_90D",
            "VENDAS_PERDIDAS_QTD",
            "VENDAS_PERDIDAS_VALOR",
            "SUGESTAO_COMPRA",
            "VALOR_ESTIMADO",
            "FORNECEDOR_1",
            "FORNECEDOR_2",
            "FORNECEDOR_3",
            "ULTIMA_COMPRA_DATA",
            "ULTIMA_COMPRA_VALOR",
            "PRIORIDADE"
        ]

        # Escrever cabeçalho
        self._write_header(headers)

        # Escrever dados
        for idx, item in enumerate(sugestoes, start=2):
            self._write_row(idx, item)

        # Ajustar larguras
        self._auto_adjust_columns()

        # Salvar arquivo
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        self.wb.save(output_file)

        return str(output_file)

    def _write_header(self, headers: List[str]):
        """Escreve cabeçalho formatado."""
        for col, header in enumerate(headers, start=1):
            cell = self.ws.cell(row=1, column=col, value=header)

            # Estilo do cabeçalho
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

    def _write_row(self, row_num: int, item: Dict):
        """Escreve linha de dados."""
        # Mapeamento de campos
        values = [
            item.get('CODPROD'),
            item.get('PRODUTO'),
            item.get('CURVA'),
            item.get('ESTOQUE_ATUAL', 0),
            item.get('GIRO_30D', 0),
            item.get('GIRO_90D', 0),
            item.get('VENDAS_PERDIDAS_QTD', 0),
            item.get('VENDAS_PERDIDAS_VALOR', 0),
            item.get('SUGESTAO_COMPRA', 0),
            item.get('VALOR_ESTIMADO', 0),
            item.get('FORNECEDOR_1', ''),
            item.get('FORNECEDOR_2', ''),
            item.get('FORNECEDOR_3', ''),
            item.get('ULTIMA_COMPRA_DATA', ''),
            item.get('ULTIMA_COMPRA_VALOR', 0),
            item.get('PRIORIDADE', 0)
        ]

        for col, value in enumerate(values, start=1):
            cell = self.ws.cell(row=row_num, column=col, value=value)

            # Formatação condicional para prioridade
            if col == 3:  # Coluna CURVA
                if value == 'A':
                    cell.fill = PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid")
                elif value == 'B':
                    cell.fill = PatternFill(start_color="87CEEB", end_color="87CEEB", fill_type="solid")

            # Bordas
            cell.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

    def _auto_adjust_columns(self):
        """Ajusta largura das colunas automaticamente."""
        for column_cells in self.ws.columns:
            length = max(len(str(cell.value or '')) for cell in column_cells)
            self.ws.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)
```

**Checklist:**
- [ ] Criar arquivo `services/excel_generator.py`
- [ ] Implementar classe `ExcelSugestaoCompra`
- [ ] Definir 16 colunas conforme especificação
- [ ] Adicionar formatação condicional
- [ ] Testar geração de Excel

---

#### 2.2 Workflow Sugestão Semanal (`sugestao_semanal.py`)

**Descrição:** Workflow completo de sugestão semanal de compra.

**Arquivo:** `workflows/sugestao_semanal.py`

**Conteúdo:**
```python
from typing import List, Dict
from datetime import datetime, timedelta
import logging
from pathlib import Path
import uuid

from services.sankhya_adapter import SankhyaProcurementService
from services.autonomy_manager import get_autonomy_manager
from services.evolution_service import EvolutionWhatsAppService
from services.excel_generator import ExcelSugestaoCompra

class SugestaoSemanalWorkflow:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sankhya = SankhyaProcurementService()
        self.autonomy = get_autonomy_manager()
        self.whatsapp = EvolutionWhatsAppService()
        self.excel_gen = ExcelSugestaoCompra()

    def executar(self) -> Dict:
        """
        Executa workflow completo de sugestão semanal.

        Returns:
            Resultado da execução
        """
        action_id = str(uuid.uuid4())

        try:
            self.logger.info(f"[{action_id}] Iniciando Sugestão Semanal")

            # 1. Coletar dados
            dados = self._coletar_dados()

            # 2. Calcular sugestões
            sugestoes = self._calcular_sugestoes(dados)

            if not sugestoes:
                self.logger.info("Nenhuma sugestão de compra necessária")
                return {'status': 'nenhuma_sugestao'}

            # 3. Gerar Excel
            excel_path = self._gerar_excel(sugestoes, action_id)

            # 4. Registrar ação
            self.autonomy.register_action(
                action_id=action_id,
                action_type='sugestao_semanal',
                data={
                    'total_produtos': len(sugestoes),
                    'valor_total': sum(s['VALOR_ESTIMADO'] for s in sugestoes),
                    'excel_path': excel_path
                }
            )

            # 5. Verificar nível de autonomia
            nivel = self.autonomy.get_current_level()

            # 6. Enviar via WhatsApp
            if nivel >= 3:
                self._enviar_para_aprovacao(sugestoes, excel_path, action_id)
            else:
                self._enviar_apenas_informativo(sugestoes, excel_path)

            return {
                'status': 'sucesso',
                'action_id': action_id,
                'total_produtos': len(sugestoes),
                'excel_path': excel_path
            }

        except Exception as e:
            self.logger.error(f"[{action_id}] Erro na execução: {str(e)}")
            return {'status': 'erro', 'mensagem': str(e)}

    def _coletar_dados(self) -> Dict:
        """Coleta dados de giro, popularidade e financeiro."""
        hoje = datetime.now().strftime('%d/%m/%Y')
        ultima_semana = (datetime.now() - timedelta(days=7)).strftime('%d/%m/%Y')

        # Giro
        giro = self.sankhya.get_giro_data()

        # Popularidade (últimos 7 dias)
        popularidade = self.sankhya.get_popularity_analysis(
            ini=ultima_semana,
            fin=hoje
        )

        # Financeiro
        financeiro = self.sankhya.get_financial_procurement_balance(
            dias_horizonte=30
        )

        return {
            'giro': giro,
            'popularidade': popularidade,
            'financeiro': financeiro
        }

    def _calcular_sugestoes(self, dados: Dict) -> List[Dict]:
        """
        Calcula sugestões de compra usando lógica ABC.

        Priorização:
        1. Score base por curva (A=1000, B=500, C=100)
        2. + (Qtd de orçamentos perdidos × 10)
        3. + (Valor perdido / 100)
        4. Filtro por saúde financeira
        """
        giro = dados['giro']
        popularidade = dados['popularidade']
        financeiro = dados['financeiro']

        # Criar mapa de popularidade por CODPROD
        pop_map = {
            item['CODPROD']: item
            for item in popularidade
        }

        sugestoes = []

        for item in giro:
            codprod = item['CODPROD']
            estoque_atual = item.get('ESTOQUE_ATUAL', 0)
            giro_30d = item.get('GIRO_30D', 0)

            # Verificar se precisa reposição (estoque < 50% do giro mensal)
            if estoque_atual >= (giro_30d * 0.5):
                continue

            # Calcular score de prioridade
            score = self._calcular_score(item, pop_map.get(codprod))

            # Calcular quantidade sugerida
            qtd_sugerida = self._calcular_quantidade_sugerida(item, pop_map.get(codprod))

            # Buscar fornecedores
            fornecedores = self._buscar_fornecedores(codprod)

            sugestoes.append({
                'CODPROD': codprod,
                'PRODUTO': item['DESCRPROD'],
                'CURVA': item['CURVA'],
                'ESTOQUE_ATUAL': estoque_atual,
                'GIRO_30D': giro_30d,
                'GIRO_90D': item.get('GIRO_90D', 0),
                'VENDAS_PERDIDAS_QTD': pop_map.get(codprod, {}).get('QTD_ORCAMENTOS', 0),
                'VENDAS_PERDIDAS_VALOR': pop_map.get(codprod, {}).get('VALOR_TOTAL_PERDIDO', 0),
                'SUGESTAO_COMPRA': qtd_sugerida,
                'VALOR_ESTIMADO': qtd_sugerida * item.get('CUSREP', 0),
                'FORNECEDOR_1': fornecedores[0] if len(fornecedores) > 0 else '',
                'FORNECEDOR_2': fornecedores[1] if len(fornecedores) > 1 else '',
                'FORNECEDOR_3': fornecedores[2] if len(fornecedores) > 2 else '',
                'ULTIMA_COMPRA_DATA': item.get('ULTIMA_COMPRA_DATA', ''),
                'ULTIMA_COMPRA_VALOR': item.get('ULTIMA_COMPRA_VALOR', 0),
                'PRIORIDADE': score
            })

        # Ordenar por prioridade (maior primeiro)
        sugestoes.sort(key=lambda x: x['PRIORIDADE'], reverse=True)

        # Aplicar limite de budget (se necessário)
        sugestoes = self._aplicar_limite_financeiro(sugestoes, financeiro)

        return sugestoes[:100]  # Top 100

    def _calcular_score(self, item_giro: Dict, item_pop: Dict = None) -> int:
        """Calcula score de prioridade."""
        score = 0

        # Score base por curva
        if item_giro['CURVA'] == 'A':
            score += 1000
        elif item_giro['CURVA'] == 'B':
            score += 500
        elif item_giro['CURVA'] == 'C':
            score += 100

        # Adicionar popularidade
        if item_pop:
            score += item_pop.get('QTD_ORCAMENTOS', 0) * 10
            score += item_pop.get('VALOR_TOTAL_PERDIDO', 0) / 100

        return int(score)

    def _calcular_quantidade_sugerida(self, item_giro: Dict, item_pop: Dict = None) -> float:
        """Calcula quantidade sugerida de compra."""
        giro_30d = item_giro.get('GIRO_30D', 0)
        curva = item_giro['CURVA']

        # Dias de segurança por curva
        dias_seguranca = {
            'A': 30,
            'B': 20,
            'C': 10
        }

        dias = dias_seguranca.get(curva, 15)

        # Quantidade base
        qtd_base = (giro_30d / 30) * dias

        # Adicionar moda de vendas perdidas (se houver)
        if item_pop and item_pop.get('MODA_QTD'):
            qtd_base = max(qtd_base, item_pop['MODA_QTD'])

        return round(qtd_base, 2)

    def _buscar_fornecedores(self, codprod: int) -> List[str]:
        """Busca top 3 fornecedores para produto."""
        hoje = datetime.now().strftime('%d/%m/%Y')
        ano_passado = (datetime.now() - timedelta(days=365)).strftime('%d/%m/%Y')

        fornecedores = self.sankhya.get_suppliers_for_product(
            ini=ano_passado,
            fin=hoje,
            empresa='1',
            codprod=codprod
        )

        # Retornar nomes dos top 3
        return [f['RAZAOSOCIAL'] for f in fornecedores[:3]]

    def _aplicar_limite_financeiro(self, sugestoes: List[Dict], financeiro: Dict) -> List[Dict]:
        """Aplica limite financeiro às sugestões."""
        folga = financeiro.get('folga_operacional', 0)

        if folga <= 0:
            self.logger.warning("Sem folga operacional - reduzindo sugestões")
            return sugestoes[:10]  # Apenas top 10 mais críticos

        # Calcular % do orçamento por curva
        orcamento_a = folga * 0.70  # 70% para curva A
        orcamento_b = folga * 0.20  # 20% para curva B
        orcamento_c = folga * 0.10  # 10% para curva C

        sugestoes_filtradas = []
        gasto_a = 0
        gasto_b = 0
        gasto_c = 0

        for item in sugestoes:
            valor = item['VALOR_ESTIMADO']
            curva = item['CURVA']

            if curva == 'A' and gasto_a + valor <= orcamento_a:
                sugestoes_filtradas.append(item)
                gasto_a += valor
            elif curva == 'B' and gasto_b + valor <= orcamento_b:
                sugestoes_filtradas.append(item)
                gasto_b += valor
            elif curva == 'C' and gasto_c + valor <= orcamento_c:
                sugestoes_filtradas.append(item)
                gasto_c += valor

        return sugestoes_filtradas

    def _gerar_excel(self, sugestoes: List[Dict], action_id: str) -> str:
        """Gera arquivo Excel."""
        output_path = f"output/sugestoes/{datetime.now().strftime('%Y-%m')}/sugestao_{action_id}.xlsx"
        return self.excel_gen.gerar(sugestoes, output_path)

    def _enviar_para_aprovacao(self, sugestoes: List[Dict], excel_path: str, action_id: str):
        """Envia para aprovação via WhatsApp (Nível 3)."""
        total_produtos = len(sugestoes)
        valor_total = sum(s['VALOR_ESTIMADO'] for s in sugestoes)

        mensagem = f"""🤖 *Sugestão Semanal de Compra*

Analisei o giro, vendas perdidas e saúde financeira.

📊 *Resumo:*
- {total_produtos} produtos identificados
- Valor total: R$ {valor_total:,.2f}
- Planilha anexa com detalhes

*Devo enviar para os fornecedores?*
Responda: SIM | NÃO | EDITAR

ID da ação: {action_id}
"""

        # TODO: Implementar envio de arquivo via WhatsApp
        self.whatsapp.send_text(
            number='+5511999999999',  # TODO: Pegar de config
            text=mensagem
        )

        self.logger.info(f"Sugestão enviada para aprovação via WhatsApp")

    def _enviar_apenas_informativo(self, sugestoes: List[Dict], excel_path: str):
        """Envia apenas como informativo (Nível 1-2)."""
        total_produtos = len(sugestoes)
        valor_total = sum(s['VALOR_ESTIMADO'] for s in sugestoes)

        mensagem = f"""📊 *Análise Semanal de Compras*

{total_produtos} produtos precisam de reposição.
Valor estimado: R$ {valor_total:,.2f}

Planilha em anexo para sua análise.
"""

        # TODO: Implementar envio de arquivo via WhatsApp
        self.whatsapp.send_text(
            number='+5511999999999',
            text=mensagem
        )


# Função para agendar
def executar_sugestao_semanal():
    """Função chamada pelo scheduler."""
    workflow = SugestaoSemanalWorkflow()
    return workflow.executar()
```

**Checklist:**
- [ ] Criar arquivo `workflows/sugestao_semanal.py`
- [ ] Implementar classe `SugestaoSemanalWorkflow`
- [ ] Implementar coleta de dados
- [ ] Implementar cálculo de prioridade ABC
- [ ] Implementar limite financeiro
- [ ] Implementar geração de Excel
- [ ] Implementar envio WhatsApp
- [ ] Integrar com Autonomy Manager

---

#### 2.3 Integração com Scheduler

**Arquivo:** `main.py` (ou ponto de entrada)

```python
from services.scheduler_service import get_scheduler
from workflows.sugestao_semanal import executar_sugestao_semanal

def setup_rotinas():
    """Configura todas as rotinas agendadas."""
    scheduler = get_scheduler()

    # Sugestão Semanal - Segunda-feira 8h
    scheduler.add_job(
        job_id='sugestao_semanal',
        func=executar_sugestao_semanal,
        cron_expression='0 8 * * 1',  # Segunda 8h
        description='Sugestão Semanal de Compra'
    )

    scheduler.start()
    print("Scheduler iniciado com rotinas configuradas")

if __name__ == '__main__':
    setup_rotinas()
```

**Checklist:**
- [ ] Criar `main.py` ou integrar em ponto de entrada existente
- [ ] Registrar job de sugestão semanal
- [ ] Testar execução manual
- [ ] Testar agendamento

---

#### 2.4 Testes Sprint 2

**Arquivo:** `tests/test_sugestao_semanal.py`

```python
import pytest
from workflows.sugestao_semanal import SugestaoSemanalWorkflow
from services.excel_generator import ExcelSugestaoCompra

def test_excel_generation():
    """Testa geração de Excel."""
    gen = ExcelSugestaoCompra()

    sugestoes = [
        {
            'CODPROD': 123,
            'PRODUTO': 'Cabo 4mm',
            'CURVA': 'A',
            'ESTOQUE_ATUAL': 50,
            'GIRO_30D': 120,
            'GIRO_90D': 360,
            'VENDAS_PERDIDAS_QTD': 10,
            'VENDAS_PERDIDAS_VALOR': 5000,
            'SUGESTAO_COMPRA': 200,
            'VALOR_ESTIMADO': 8500,
            'FORNECEDOR_1': 'ABC Elétrica',
            'FORNECEDOR_2': 'XYZ Dist',
            'FORNECEDOR_3': '',
            'ULTIMA_COMPRA_DATA': '01/01/2026',
            'ULTIMA_COMPRA_VALOR': 8000,
            'PRIORIDADE': 1500
        }
    ]

    path = gen.gerar(sugestoes, 'output/test_sugestao.xlsx')

    assert path.endswith('.xlsx')
    # TODO: Verificar conteúdo do Excel

def test_calcular_score():
    """Testa cálculo de score de prioridade."""
    workflow = SugestaoSemanalWorkflow()

    item_a = {'CURVA': 'A', 'CODPROD': 123}
    item_pop = {'QTD_ORCAMENTOS': 10, 'VALOR_TOTAL_PERDIDO': 5000}

    score = workflow._calcular_score(item_a, item_pop)

    # Score esperado: 1000 (curva A) + 100 (10×10) + 50 (5000/100) = 1150
    assert score == 1150
```

**Checklist:**
- [ ] Criar `tests/test_sugestao_semanal.py`
- [ ] Testar geração de Excel
- [ ] Testar cálculo de score
- [ ] Testar cálculo de quantidade sugerida
- [ ] Testar aplicação de limite financeiro

---

### ✅ Critérios de Aceitação Sprint 2

- [ ] Excel gerado com 16 colunas conforme especificação
- [ ] Lógica ABC de priorização funciona corretamente
- [ ] Limite financeiro é aplicado (70% A, 20% B, 10% C)
- [ ] WhatsApp envia mensagem de aprovação (Nível 3)
- [ ] Ação é registrada no Autonomy Manager
- [ ] Workflow executa sem erros
- [ ] Job agendado para Segunda 8h
- [ ] Testes passam com 100% de sucesso

---

## 📲 Sprint 3: Cotação Automática (Semana 3)

### Objetivos
- Enviar cotações automaticamente para fornecedores
- Capturar respostas via WhatsApp
- Comparar preços recebidos

### 📦 Entregas

#### 3.1 Workflow Cotação Automática (`cotacao_automatica.py`)

**Descrição:** Envia mapa de cotação para fornecedores via WhatsApp.

**Arquivo:** `workflows/cotacao_automatica.py`

**Conteúdo:**
```python
from typing import List, Dict
from datetime import datetime, timedelta
import logging
import uuid

from services.sankhya_adapter import SankhyaProcurementService
from services.autonomy_manager import get_autonomy_manager
from services.evolution_service import EvolutionWhatsAppService
from services.excel_generator import ExcelSugestaoCompra

class CotacaoAutomaticaWorkflow:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sankhya = SankhyaProcurementService()
        self.autonomy = get_autonomy_manager()
        self.whatsapp = EvolutionWhatsAppService()

    def executar(self, produtos: List[int], aprovacao_action_id: str = None):
        """
        Executa cotação automática para lista de produtos.

        Args:
            produtos: Lista de CODPRODs
            aprovacao_action_id: ID da ação que aprovou esta cotação
        """
        action_id = str(uuid.uuid4())

        try:
            self.logger.info(f"[{action_id}] Iniciando Cotação Automática")

            # Agrupar produtos por fornecedores comuns
            grupos_fornecedores = self._agrupar_por_fornecedores(produtos)

            # Para cada fornecedor, criar mapa e enviar
            for fornecedor_info in grupos_fornecedores:
                self._enviar_cotacao_fornecedor(
                    fornecedor_info,
                    action_id
                )

            # Registrar ação
            self.autonomy.register_action(
                action_id=action_id,
                action_type='cotacao_automatica',
                data={
                    'total_produtos': len(produtos),
                    'total_fornecedores': len(grupos_fornecedores),
                    'aprovacao_action_id': aprovacao_action_id
                }
            )

            # Notificar comprador
            self._notificar_comprador(action_id, len(produtos), len(grupos_fornecedores))

            return {
                'status': 'sucesso',
                'action_id': action_id,
                'fornecedores_contatados': len(grupos_fornecedores)
            }

        except Exception as e:
            self.logger.error(f"[{action_id}] Erro: {str(e)}")
            return {'status': 'erro', 'mensagem': str(e)}

    def _agrupar_por_fornecedores(self, produtos: List[int]) -> List[Dict]:
        """Agrupa produtos por fornecedores comuns."""
        # TODO: Implementar lógica de agrupamento inteligente
        # Por ora, retorna todos os fornecedores de cada produto

        hoje = datetime.now().strftime('%d/%m/%Y')
        ano_passado = (datetime.now() - timedelta(days=365)).strftime('%d/%m/%Y')

        fornecedores_map = {}

        for codprod in produtos:
            fornecedores = self.sankhya.get_suppliers_for_product(
                ini=ano_passado,
                fin=hoje,
                empresa='1',
                codprod=codprod
            )

            for fornecedor in fornecedores[:3]:  # Top 3
                codparc = fornecedor['CODPARC']

                if codparc not in fornecedores_map:
                    fornecedores_map[codparc] = {
                        'codparc': codparc,
                        'razao_social': fornecedor['RAZAOSOCIAL'],
                        'telefone': fornecedor.get('TELEFONE', ''),
                        'produtos': []
                    }

                fornecedores_map[codparc]['produtos'].append(codprod)

        return list(fornecedores_map.values())

    def _enviar_cotacao_fornecedor(self, fornecedor_info: Dict, action_id: str):
        """Envia mapa de cotação para um fornecedor."""
        # Gerar Excel de cotação
        excel_path = self._gerar_mapa_cotacao(
            fornecedor_info['produtos'],
            fornecedor_info['codparc']
        )

        # Mensagem
        mensagem = f"""Olá {fornecedor_info['razao_social']},

Segue mapa de cotação para os seguintes produtos:
{self._listar_produtos(fornecedor_info['produtos'])}

Prazo para resposta: 48h

Att,
Portal Distribuidora

ID: {action_id}
"""

        # Enviar via WhatsApp
        telefone = fornecedor_info['telefone']

        if telefone:
            # TODO: Implementar envio de arquivo
            self.whatsapp.send_text(
                number=telefone,
                text=mensagem
            )

            self.logger.info(f"Cotação enviada para {fornecedor_info['razao_social']}")
        else:
            self.logger.warning(f"Fornecedor {fornecedor_info['razao_social']} sem telefone")

    def _gerar_mapa_cotacao(self, produtos: List[int], codparc: int) -> str:
        """Gera mapa de cotação em Excel."""
        # TODO: Implementar geração de mapa de cotação
        # Formato: Produto | Quantidade | Unidade | [Colunas para preenchimento]
        return f"output/cotacoes/mapa_{codparc}.xlsx"

    def _listar_produtos(self, produtos: List[int]) -> str:
        """Lista produtos em texto."""
        # TODO: Buscar descrições dos produtos
        return "\n".join([f"- Produto {cod}" for cod in produtos[:5]])

    def _notificar_comprador(self, action_id: str, total_produtos: int, total_fornecedores: int):
        """Notifica comprador sobre envio."""
        mensagem = f"""✅ *Cotações Enviadas*

Enviei mapa de cotação para {total_fornecedores} fornecedores.
Total de {total_produtos} produtos.

Prazo de resposta: 48h

ID: {action_id}
"""

        # TODO: Pegar número de config
        self.whatsapp.send_text(
            number='+5511999999999',
            text=mensagem
        )
```

**Checklist:**
- [ ] Criar arquivo `workflows/cotacao_automatica.py`
- [ ] Implementar agrupamento por fornecedores
- [ ] Implementar geração de mapa de cotação
- [ ] Implementar envio via WhatsApp
- [ ] Implementar notificação para comprador
- [ ] Adicionar tratamento de erros

---

#### 3.2 Captura de Respostas

**Descrição:** Watcher para capturar respostas de cotações via WhatsApp.

**Arquivo:** `workflows/captura_respostas.py`

```python
from typing import Dict, List
from datetime import datetime
import logging
import re

from services.evolution_service import EvolutionWhatsAppService

class CapturaRespostasWorkflow:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.whatsapp = EvolutionWhatsAppService()

    def processar_mensagens_pendentes(self):
        """Processa mensagens recebidas de fornecedores."""
        # TODO: Implementar lógica de captura
        # 1. Buscar mensagens não lidas
        # 2. Identificar se é resposta de cotação (por ID)
        # 3. Extrair preços (parsing inteligente)
        # 4. Salvar em banco/log
        # 5. Comparar preços
        # 6. Notificar comprador
        pass

    def _extrair_precos(self, mensagem: str) -> List[Dict]:
        """Extrai preços de mensagem de texto."""
        # Regex para capturar valores
        # Exemplos: R$ 150,00 | 150.00 | 150,00
        pattern = r'R?\$?\s*(\d+[.,]\d{2})'

        matches = re.findall(pattern, mensagem)

        return [float(m.replace(',', '.')) for m in matches]
```

**Checklist:**
- [ ] Criar arquivo `workflows/captura_respostas.py`
- [ ] Implementar busca de mensagens
- [ ] Implementar parsing de preços
- [ ] Implementar comparação de preços
- [ ] Implementar notificação

---

### ✅ Critérios de Aceitação Sprint 3

- [ ] Cotações enviadas via WhatsApp para fornecedores
- [ ] Mapa de cotação gerado em Excel
- [ ] Respostas podem ser capturadas
- [ ] Preços são extraídos e comparados
- [ ] Comprador é notificado após envio
- [ ] Testes passam com 100% de sucesso

---

## ⚠️ Sprint 4: Monitor de Ruptura (Semana 4)

### Objetivos
- Monitorar itens curva A em risco de ruptura
- Alertar diariamente sobre estoque crítico
- Sugerir compra urgente

### 📦 Entregas

#### 4.1 Workflow Monitor de Ruptura (`monitor_ruptura.py`)

**Descrição:** Analisa estoque e alerta sobre riscos de ruptura.

**Arquivo:** `workflows/monitor_ruptura.py`

**Conteúdo:**
```python
from typing import List, Dict
from datetime import datetime
import logging
import uuid

from services.sankhya_adapter import SankhyaProcurementService
from services.autonomy_manager import get_autonomy_manager
from services.evolution_service import EvolutionWhatsAppService

class MonitorRupturaWorkflow:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sankhya = SankhyaProcurementService()
        self.autonomy = get_autonomy_manager()
        self.whatsapp = EvolutionWhatsAppService()

    def executar(self):
        """Executa monitoramento de ruptura."""
        action_id = str(uuid.uuid4())

        try:
            self.logger.info(f"[{action_id}] Iniciando Monitor de Ruptura")

            # Buscar produtos curva A
            giro = self.sankhya.get_giro_data()
            estoque = self.sankhya.get_group_stock_summary()

            # Identificar itens críticos
            itens_criticos = self._identificar_criticos(giro, estoque)

            if not itens_criticos:
                self.logger.info("Nenhum item em risco de ruptura")
                return {'status': 'ok'}

            # Registrar ação
            self.autonomy.register_action(
                action_id=action_id,
                action_type='monitor_ruptura',
                data={
                    'total_criticos': len(itens_criticos)
                }
            )

            # Notificar
            self._notificar_ruptura(itens_criticos, action_id)

            return {
                'status': 'alerta',
                'action_id': action_id,
                'itens_criticos': len(itens_criticos)
            }

        except Exception as e:
            self.logger.error(f"[{action_id}] Erro: {str(e)}")
            return {'status': 'erro', 'mensagem': str(e)}

    def _identificar_criticos(self, giro: List[Dict], estoque: Dict) -> List[Dict]:
        """Identifica itens curva A em risco."""
        criticos = []

        for item in giro:
            if item['CURVA'] != 'A':
                continue

            codprod = item['CODPROD']
            estoque_atual = estoque.get(codprod, 0)
            giro_30d = item.get('GIRO_30D', 0)

            if giro_30d == 0:
                continue

            # Calcular cobertura em dias
            dias_cobertura = (estoque_atual / giro_30d) * 30

            # Alertar se < 15 dias
            if dias_cobertura < 15:
                urgencia = 'CRÍTICA' if dias_cobertura < 7 else 'ALTA'

                criticos.append({
                    'produto': item['DESCRPROD'],
                    'codprod': codprod,
                    'estoque': estoque_atual,
                    'giro_30d': giro_30d,
                    'dias_cobertura': dias_cobertura,
                    'urgencia': urgencia
                })

        # Ordenar por urgência
        criticos.sort(key=lambda x: x['dias_cobertura'])

        return criticos

    def _notificar_ruptura(self, itens: List[Dict], action_id: str):
        """Notifica comprador sobre itens críticos."""
        msg = f"⚠️ *ALERTA DE RUPTURA*\n\n{len(itens)} produtos curva A em risco:\n\n"

        for item in itens[:5]:  # Top 5
            msg += f"""📦 *{item['produto']}*
   Estoque: {item['estoque']:.0f} un
   Cobertura: {item['dias_cobertura']:.1f} dias
   Urgência: {item['urgencia']}

"""

        msg += f"\n*Devo gerar cotação para estes itens?*\n\nID: {action_id}"

        # TODO: Pegar de config
        self.whatsapp.send_text(
            number='+5511999999999',
            text=msg
        )


def executar_monitor_ruptura():
    """Função chamada pelo scheduler."""
    workflow = MonitorRupturaWorkflow()
    return workflow.executar()
```

**Checklist:**
- [ ] Criar arquivo `workflows/monitor_ruptura.py`
- [ ] Implementar identificação de itens críticos
- [ ] Implementar cálculo de cobertura de estoque
- [ ] Implementar classificação de urgência
- [ ] Implementar notificação
- [ ] Agendar para diária 8h

---

### ✅ Critérios de Aceitação Sprint 4

- [ ] Itens curva A com < 15 dias de cobertura são identificados
- [ ] Urgência é classificada (CRÍTICA < 7 dias, ALTA < 15 dias)
- [ ] Comprador recebe alerta diário via WhatsApp
- [ ] Job agendado para execução diária às 8h
- [ ] Testes passam com 100% de sucesso

---

## 📉 Sprint 5: Análise de Vendas Perdidas (Semana 5)

### Objetivos
- Analisar vendas perdidas semanalmente
- Identificar produtos com alta demanda reprimida
- Sugerir ações corretivas

### 📦 Entregas

#### 5.1 Workflow Análise de Vendas Perdidas (`analise_vendas_perdidas.py`)

**Descrição:** Analisa orçamentos não convertidos por falta de estoque.

**Arquivo:** `workflows/analise_vendas_perdidas.py`

**Conteúdo:**
```python
from typing import List, Dict
from datetime import datetime, timedelta
import logging
import uuid

from services.sankhya_adapter import SankhyaProcurementService
from services.autonomy_manager import get_autonomy_manager
from services.evolution_service import EvolutionWhatsAppService

class AnaliseVendasPerdidasWorkflow:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sankhya = SankhyaProcurementService()
        self.autonomy = get_autonomy_manager()
        self.whatsapp = EvolutionWhatsAppService()

    def executar(self):
        """Executa análise de vendas perdidas."""
        action_id = str(uuid.uuid4())

        try:
            self.logger.info(f"[{action_id}] Iniciando Análise de Vendas Perdidas")

            # Analisar última semana
            hoje = datetime.now().strftime('%d/%m/%Y')
            semana_passada = (datetime.now() - timedelta(days=7)).strftime('%d/%m/%Y')

            analise = self.sankhya.get_popularity_analysis(
                ini=semana_passada,
                fin=hoje
            )

            if not analise:
                self.logger.info("Nenhuma venda perdida identificada")
                return {'status': 'ok'}

            # Calcular impacto
            total_perdido = sum(item['VALOR_TOTAL_PERDIDO'] for item in analise)

            # Registrar ação
            self.autonomy.register_action(
                action_id=action_id,
                action_type='analise_vendas_perdidas',
                data={
                    'total_produtos': len(analise),
                    'valor_total_perdido': total_perdido
                }
            )

            # Notificar
            self._notificar_vendas_perdidas(analise, total_perdido, action_id)

            return {
                'status': 'sucesso',
                'action_id': action_id,
                'valor_perdido': total_perdido
            }

        except Exception as e:
            self.logger.error(f"[{action_id}] Erro: {str(e)}")
            return {'status': 'erro', 'mensagem': str(e)}

    def _notificar_vendas_perdidas(self, analise: List[Dict], total: float, action_id: str):
        """Notifica comprador sobre vendas perdidas."""
        msg = f"""📉 *Análise de Vendas Perdidas* (última semana)

💰 *Total perdido:* R$ {total:,.2f}

Top 5 produtos:

"""

        for item in analise[:5]:
            msg += f"""🔸 *{item['DESCRPROD']}*
   Valor perdido: R$ {item['VALOR_TOTAL_PERDIDO']:,.2f}
   Orçamentos: {item['QTD_ORCAMENTOS']}
   Qtd típica: {item.get('MODA_QTD', 0)} un

"""

        msg += f"\nID: {action_id}"

        # TODO: Pegar de config
        self.whatsapp.send_text(
            number='+5511999999999',
            text=msg
        )


def executar_analise_vendas_perdidas():
    """Função chamada pelo scheduler."""
    workflow = AnaliseVendasPerdidasWorkflow()
    return workflow.executar()
```

**Checklist:**
- [ ] Criar arquivo `workflows/analise_vendas_perdidas.py`
- [ ] Implementar análise semanal
- [ ] Implementar cálculo de impacto
- [ ] Implementar notificação
- [ ] Agendar para Sexta 17h

---

### ✅ Critérios de Aceitação Sprint 5

- [ ] Análise de vendas perdidas executada semanalmente
- [ ] Top 5 produtos mais impactados são identificados
- [ ] Valor total perdido é calculado
- [ ] Comprador recebe relatório via WhatsApp
- [ ] Job agendado para Sexta às 17h
- [ ] Testes passam com 100% de sucesso

---

## ✅ Checklist Final

### Infraestrutura
- [ ] Scheduler rodando em produção
- [ ] Logs sendo gravados corretamente
- [ ] Autonomy Manager salvando estado
- [ ] WhatsApp integrado e funcional

### Rotinas Agendadas
- [ ] ✅ Sugestão Semanal (Segunda 8h)
- [ ] ✅ Monitor de Ruptura (Diária 8h)
- [ ] ✅ Análise de Vendas Perdidas (Sexta 17h)
- [ ] ✅ Cotação Automática (sob demanda)

### Funcionalidades
- [ ] Geração de Excel com 16 colunas
- [ ] Priorização ABC implementada
- [ ] Limite financeiro aplicado
- [ ] Validação de horário comercial
- [ ] Fallback de comunicação (WhatsApp → Email)
- [ ] Sistema de feedback funcionando
- [ ] Evolução de autonomia automática

### Testes
- [ ] 100% dos testes unitários passando
- [ ] Testes de integração validados
- [ ] Teste em produção realizado
- [ ] Métricas de sucesso definidas

### Documentação
- [ ] README atualizado
- [ ] Guia de operação criado
- [ ] Troubleshooting documentado
- [ ] Métricas de monitoramento definidas

---

## 🚀 Como Executar

### Instalação

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com credenciais

# 3. Criar estrutura de logs
mkdir -p logs/{actions,feedback,errors,autonomy}

# 4. Iniciar scheduler
python main.py
```

### Teste Manual

```bash
# Testar Sugestão Semanal
python -c "from workflows.sugestao_semanal import executar_sugestao_semanal; executar_sugestao_semanal()"

# Testar Monitor de Ruptura
python -c "from workflows.monitor_ruptura import executar_monitor_ruptura; executar_monitor_ruptura()"

# Testar Análise de Vendas Perdidas
python -c "from workflows.analise_vendas_perdidas import executar_analise_vendas_perdidas; executar_analise_vendas_perdidas()"
```

### Verificar Logs

```bash
# Ver ações registradas
cat logs/actions/$(date +%Y-%m)/$(date +%Y-%m-%d).jsonl

# Ver feedbacks
cat logs/feedback/$(date +%Y-%m)/$(date +%Y-%m-%d).jsonl

# Ver estado de autonomia
cat logs/autonomy/state.json
```

### Monitorar Scheduler

```python
from services.scheduler_service import get_scheduler

scheduler = get_scheduler()
jobs = scheduler.get_jobs()

for job in jobs:
    print(f"{job['id']}: Próxima execução em {job['next_run']}")
```

---

## 📊 Métricas de Acompanhamento

### Semana 1 (Sprint 1)
- [ ] Scheduler funcionando 24/7
- [ ] 0 crashes no Autonomy Manager
- [ ] Logs sendo gravados corretamente

### Semana 2 (Sprint 2)
- [ ] Primeira sugestão semanal enviada
- [ ] Excel gerado sem erros
- [ ] WhatsApp entregando mensagens

### Semana 3 (Sprint 3)
- [ ] Primeiras cotações enviadas
- [ ] Respostas capturadas
- [ ] Preços comparados

### Semana 4 (Sprint 4)
- [ ] Primeiro alerta de ruptura enviado
- [ ] Itens críticos identificados corretamente

### Semana 5 (Sprint 5)
- [ ] Primeiro relatório de vendas perdidas
- [ ] Valor total perdido calculado

### Pós-Implantação (30 dias)
- [ ] Taxa de aceitação de sugestões > 80%
- [ ] Ruptura de estoque curva A < 5%
- [ ] Tempo de cotação reduzido em 30%
- [ ] Feedback positivo > 90%

---

## 🎯 Sucesso do Projeto

O projeto será considerado bem-sucedido quando:

1. ✅ **Proatividade**: Comprador recebe sugestões automaticamente toda segunda
2. ✅ **Autonomia**: Sistema evolui de Nível 3 → 4 em 60 dias
3. ✅ **Eficiência**: Tempo de cotação reduzido de 2h → 15min
4. ✅ **Confiabilidade**: 95% de uptime do scheduler
5. ✅ **ROI**: Redução de 20% em vendas perdidas por falta de estoque

---

**Documento criado em:** 13 de Fevereiro de 2026
**Próxima revisão:** Fim de cada sprint
**Responsável:** Equipe de Desenvolvimento

🚀 **Vamos começar!**
