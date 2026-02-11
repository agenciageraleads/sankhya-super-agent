"""
Módulo de Monitoramento Proativo (Watchers) do SSA.
Define alertas e verificações automáticas no Sankhya.
"""
import logging
from typing import List, Dict, Any, Optional
try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

logger = logging.getLogger("skill-watchers")

class Watcher:
    def __init__(self, name: str, query: str, description: str, severity: str = "INFO"):
        self.name = name
        self.query = query
        self.description = description
        self.severity = severity

    def run(self) -> Optional[Dict]:
        try:
            result = sankhya.execute_query(self.query)
            if result:
                return {
                    "name": self.name,
                    "description": self.description,
                    "count": len(result),
                    "data": result,
                    "severity": self.severity
                }
        except Exception as e:
            logger.error(f"Erro ao rodar watcher {self.name}: {str(e)}")
        return None

# Definição dos Watchers Padrão
SYSTEM_WATCHERS = [
    Watcher(
        "Notas Pendentes",
        "SELECT NUNOTA, CODPARC, VLRNOTA FROM TGFCAB WHERE STATUSNOTA = 'P' AND DTNEG > SYSDATE - 7",
        "Notas que foram digitadas mas não confirmadas nos últimos 7 dias.",
        "WARNING"
    ),
    Watcher(
        "Estoque Crítico",
        "SELECT CODPROD, ESTOQUE FROM TGFEST WHERE ESTOQUE < 5 AND CODPROD IN (SELECT CODPROD FROM TGFPRO WHERE ATIVO = 'S')",
        "Produtos ativos com menos de 5 unidades em estoque.",
        "DANGER"
    ),
    Watcher(
        "Novos Parceiros sem CPF/CNPJ",
        "SELECT CODPARC, NOMEPARC FROM TGFPAR WHERE (CGC_CPF IS NULL OR CGC_CPF = '') AND DTALTER > SYSDATE - 1",
        "Parceiros criados ou alterados hoje sem documento fiscal.",
        "INFO"
    )
]

def run_all_watchers() -> str:
    """Executa todos os vigias proativos e retorna um painel de alertas."""
    alerts = []
    for watcher in SYSTEM_WATCHERS:
        res = watcher.run()
        if res:
            color = "🔴" if res['severity'] == "DANGER" else "🟡" if res['severity'] == "WARNING" else "🔵"
            alerts.append(f"{color} **{res['name']}**: {res['count']} ocorrência(s)\n_{res['description']}_")
            # Adiciona tabela resumida se for importante
            if res['count'] > 0:
                alerts.append(format_as_markdown_table(res['data'][:5])) # Mostra só os 5 primeiros
    
    if not alerts:
        return "✅ **Tudo limpo!** Nenhum alerta proativo detectado nos vigias do sistema."
    
    return "### 🚨 Painel de Alertas Proativos\n\n" + "\n\n".join(alerts)
