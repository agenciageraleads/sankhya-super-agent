"""
Motor Proativo do SSA - Roda os watchers em background e armazena os alertas.
"""
import time
import json
import os
import logging
from datetime import datetime

import sys
# Adiciona o diretório raiz ao path para encontrar mcp_server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.skills.watchers import run_all_watchers

logger = logging.getLogger("ssa-bg-worker")

ALERTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge", "active_alerts.json")

def start_background_monitoring(interval_seconds: int = 3600):
    """Roda os vigias periodicamente e salva o resultado."""
    logger.info(f"🚀 Motor Proativo iniciado. Intervalo: {interval_seconds}s")
    
    while True:
        try:
            report = run_all_watchers()
            data = {
                "last_run": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "report": report
            }
            
            with open(ALERTS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info("✅ Alertas proativos atualizados com sucesso.")
        except Exception as e:
            logger.error(f"Erro no Motor Proativo: {e}")
            
        time.sleep(interval_seconds)

if __name__ == "__main__":
    # Quando rodado diretamente, executa uma vez e sai (para teste ou cron)
    start_background_monitoring(60) 
