import os
import logging
from typing import List, Dict, Any
from mcp_server.domains.procurement.services.sankhya_adapter import SankhyaProcurementService

logger = logging.getLogger("procurement-radar")

class ProcurementRadar:
    """
    Fluxo 1: Monitoramento e Predição.
    Implementa a lógica do Manual de Processos v1.0.
    """

    def __init__(self):
        domain_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sankhya_service = SankhyaProcurementService(domain_path)
        self.rules = self.sankhya_service.config

    def run_analysis(self) -> List[Dict[str, Any]]:
        """Executa a análise baseada no Manual de Treinamento."""
        logger.info("Iniciando análise do Radar de Compras (Manual v1.0)...")
        
        # 1. Busca dados
        abc_data = self.sankhya_service.get_abc_giro_data()
        pop_data = self.sankhya_service.get_popularity_data()
        
        if not abc_data:
            logger.warning("Nenhum dado de ABC/Giro encontrado.")
            return []

        popularity_map = {int(p["CODPROD"]): p for p in pop_data if "CODPROD" in p}
        opportunities = []
        
        for item in abc_data:
            codprod = int(item.get("CODPROD", 0))
            if not codprod: continue
            
            # Dados base
            curva = item.get("CURVA", "C").strip()
            estoque_atual = float(item.get("ESTOQUE", 0))
            venda_mensal = float(item.get("VENDA_MENSAL", 0)) # Manual usa base mensal
            
            # Lógica do Manual:
            # 1. Baseada na quantidade mensal de vendas
            # 2. Acrescentar buffer (Ex: 20%)
            buffer_multiplier = 1 + self.rules.get("analysis", {}).get("demand_buffer", 0.20)
            venda_mensal_ajustada = venda_mensal * buffer_multiplier
            
            # 3. Multiplicar pela quantidade de meses do prazo de pagamento
            # (Pegamos o prazo médio do fornecedor principal ou padrão de 1 mês se não houver)
            prazo_pagamento_meses = float(item.get("PRAZO_PAG_MESES", 1))
            
            quantidade_alvo = venda_mensal_ajustada * prazo_pagamento_meses
            
            # 4. Adiciona demanda reprimida (orçamentos perdidos)
            pop_item = popularity_map.get(codprod, {})
            qtd_perdida = float(pop_item.get("QTD_ORCADA", 0))
            quantidade_alvo += qtd_perdida # Orçamentos são demanda imediata represada
            
            # 5. Verifica necessidade
            if estoque_atual < quantidade_alvo:
                ops = {
                    "CODPROD": codprod,
                    "PRODUTO": item.get("DESCRPROD", f"Produto {codprod}"),
                    "CURVA": curva,
                    "ESTOQUE_ATUAL": estoque_atual,
                    "SUGESTAO_COMPRA": round(quantidade_alvo - estoque_atual, 0),
                    "DEMANDA_MENSAL_AJUSTADA": round(venda_mensal_ajustada, 2),
                    "MOTIVO": f"Abaixo do Ponto de Equilíbrio (Estoque para {prazo_pagamento_meses} meses + orçamentos)"
                }
                opportunities.append(ops)
                
        # Ordenação por Curva (A > B > C) e depois por valor de sugestão
        opportunities.sort(key=lambda x: (x["CURVA"], -x["SUGESTAO_COMPRA"]))
        
        return opportunities
