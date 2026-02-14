import os
import logging
from typing import List, Dict, Any, Optional
from mcp_server.domains.procurement.services.sankhya_adapter import SankhyaProcurementService

logger = logging.getLogger("procurement-radar")

class ProcurementRadar:
    """
    Fluxo 1: Monitoramento e Predição v2.0
    Integra Lead Time Dinâmico + CMV Budget Control
    """

    def __init__(self):
        domain_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sankhya_service = SankhyaProcurementService(domain_path)
        self.rules = self.sankhya_service.config

    def run_analysis(self) -> List[Dict[str, Any]]:
        """Executa análise com lead time dinâmico e validação de budget."""
        logger.info("Iniciando Radar de Compras v2.0 (Lead Time + Budget Control)...")

        # 1. NOVO: Busca orçamento do mês
        budget_enabled = self.rules.get("budget_control", {}).get("enabled", False)
        if budget_enabled:
            budget_data = self.sankhya_service.calculate_purchase_budget_allocation(
                growth_factor=self.rules.get("budget_control", {}).get("growth_factor_annual", 0.20)
            )
            logger.info(f"Orçamento global: R$ {budget_data['orcamento_global']:,.2f}")
        else:
            budget_data = None

        # 2. Busca dados
        abc_data = self.sankhya_service.get_abc_giro_data()
        pop_data = self.sankhya_service.get_popularity_data()

        if not abc_data:
            logger.warning("Nenhum dado de ABC/Giro encontrado.")
            return []

        popularity_map = {int(p["CODPROD"]): p for p in pop_data if "CODPROD" in p}
        opportunities = []

        for item in abc_data:
            codprod = int(item.get("CODPROD", 0))
            if not codprod:
                continue

            # NOVO: Identifica fornecedor principal
            supplier_info = self._get_primary_supplier(codprod)
            if not supplier_info:
                logger.debug(f"Produto {codprod} sem fornecedor principal. Pulando.")
                continue

            codparc = supplier_info["CODPARC"]

            # NOVO: Busca lead time dinâmico
            leadtime_data = self.sankhya_service.get_effective_leadtime(codprod, codparc)
            leadtime_dias = leadtime_data["leadtime_dias"]
            leadtime_fonte = leadtime_data["fonte"]

            # Cálculo de demanda (existente)
            curva = item.get("CURVA", "C").strip()
            estoque_atual = float(item.get("ESTOQUE", 0))
            venda_mensal = float(item.get("VENDA_MENSAL", 0))

            buffer_multiplier = 1 + self.rules.get("analysis", {}).get("demand_buffer", 0.20)
            venda_mensal_ajustada = venda_mensal * buffer_multiplier

            prazo_pagamento_meses = float(item.get("PRAZO_PAG_MESES", 1))
            quantidade_alvo = venda_mensal_ajustada * prazo_pagamento_meses

            # NOVO: Adiciona estoque de segurança baseado em lead time DINÂMICO
            giro_diario = venda_mensal / 30 if venda_mensal > 0 else 0
            estoque_seguranca = giro_diario * leadtime_dias
            quantidade_alvo += estoque_seguranca

            # Adiciona demanda reprimida (existente)
            pop_item = popularity_map.get(codprod, {})
            qtd_perdida = float(pop_item.get("QTD_ORCADA", 0))
            quantidade_alvo += qtd_perdida

            # NOVO: Valida budget antes de sugerir
            if estoque_atual < quantidade_alvo:
                sugestao_qtd = quantidade_alvo - estoque_atual
                custo_unitario = float(item.get("CUSTOGER", 0))
                valor_compra = sugestao_qtd * custo_unitario

                # Valida orçamento se habilitado
                if budget_enabled:
                    budget_check = self.sankhya_service.validate_purchase_against_budget(
                        codparc=codparc,
                        valor_compra=valor_compra
                    )
                else:
                    budget_check = {
                        "aprovado": True,
                        "orcamento_disponivel": 0,
                        "percentual_utilizado": 0,
                        "mensagem": "Budget control desabilitado"
                    }

                ops = {
                    "CODPROD": codprod,
                    "PRODUTO": item.get("DESCRPROD", f"Produto {codprod}"),
                    "CURVA": curva,
                    "FORNECEDOR": supplier_info.get("NOMEPARC", "N/A"),
                    "CODPARC": codparc,
                    "ESTOQUE_ATUAL": estoque_atual,
                    "SUGESTAO_COMPRA": round(sugestao_qtd, 0),
                    "VALOR_ESTIMADO": round(valor_compra, 2),
                    "DEMANDA_MENSAL_AJUSTADA": round(venda_mensal_ajustada, 2),

                    # NOVO: Informações de Lead Time
                    "LEADTIME_DIAS": leadtime_dias,
                    "LEADTIME_FONTE": leadtime_fonte,
                    "LEADTIME_CONFIAVEL": leadtime_data["confiavel"],
                    "ESTOQUE_SEGURANCA": round(estoque_seguranca, 2),

                    # NOVO: Informações de Budget
                    "ORCAMENTO_DISPONIVEL": budget_check.get("orcamento_disponivel", 0),
                    "PERCENTUAL_ORCAMENTO": budget_check.get("percentual_utilizado", 0),
                    "COMPRA_APROVADA": budget_check["aprovado"],
                    "STATUS_BUDGET": budget_check["mensagem"],

                    "MOTIVO": f"Estoque para {prazo_pagamento_meses}m + {leadtime_dias}d LT ({leadtime_fonte}) + demanda reprimida"
                }
                opportunities.append(ops)

        # NOVO: Ordenação prioriza compras aprovadas
        opportunities.sort(
            key=lambda x: (
                not x["COMPRA_APROVADA"],  # Aprovadas primeiro
                x["CURVA"],                 # Depois por curva ABC
                -x.get("VALOR_ESTIMADO", 0) # Depois por valor DESC
            )
        )

        logger.info(f"Análise concluída: {len(opportunities)} oportunidades encontradas")
        return opportunities

    def _get_primary_supplier(self, codprod: int) -> Optional[Dict[str, Any]]:
        """Busca fornecedor principal por volume de compras nos últimos 12 meses."""
        sql = """
            SELECT CODPARC, MAX(NOMEPARC) AS NOMEPARC
            FROM (
                SELECT
                    CAB.CODPARC,
                    PAR.NOMEPARC,
                    SUM(ITE.QTDNEG) AS VOLUME,
                    ROW_NUMBER() OVER (PARTITION BY ITE.CODPROD ORDER BY SUM(ITE.QTDNEG) DESC) AS RN
                FROM TGFITE ITE
                JOIN TGFCAB CAB ON ITE.NUNOTA = CAB.NUNOTA
                JOIN TGFPAR PAR ON CAB.CODPARC = PAR.CODPARC
                WHERE CAB.TIPMOV = 'O'
                  AND CAB.STATUSNOTA = 'L'
                  AND ITE.CODPROD = :CODPROD
                  AND CAB.DTNEG >= ADD_MONTHS(SYSDATE, -12)
                GROUP BY CAB.CODPARC, PAR.NOMEPARC, ITE.CODPROD
            ) WHERE RN = 1
            GROUP BY CODPARC
        """
        results = self.sankhya_service._execute_with_params(sql, {"CODPROD": codprod})
        return results[0] if results else None
