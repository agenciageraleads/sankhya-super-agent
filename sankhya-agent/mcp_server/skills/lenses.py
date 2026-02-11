"""
Módulo de Lentes Virtuais (Data Lenses) - Otimização de Dados e Economia de Tokens.
Este módulo fornece visões simplificadas e pré-processadas do ERP.
"""
import logging
import json
import os
from typing import List, Dict, Any, Optional

try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

logger = logging.getLogger("skill-lenses")

def _get_rules():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "knowledge", "business_rules.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def get_consolidated_sales_lens(months: int = 3) -> str:
    """
    Retorna uma visão consolidada e limpa das vendas por segmento do grupo.
    Economiza tokens ao pré-processar agrupamentos (1+5+7 e 2+6).
    """
    rules = _get_rules()
    atacado_ids = rules.get("group_structure", {}).get("ATACADO", {}).get("emp_ids", [1, 5, 7])
    industria_ids = rules.get("group_structure", {}).get("INDUSTRIA", {}).get("emp_ids", [2, 6])
    
    ids_all = atacado_ids + industria_ids
    ids_str = ", ".join(map(str, ids_all))
    
    sql = f"""
    SELECT 
        CODEMP, 
        TO_CHAR(DTNEG, 'YYYY-MM') as MES, 
        SUM(VLRNOTA) as TOTAL 
    FROM TGFCAB 
    WHERE STATUSNOTA = 'L' 
      AND TIPMOV = 'V' 
      AND DTNEG > ADD_MONTHS(SYSDATE, -{months})
      AND CODEMP IN ({ids_str})
    GROUP BY CODEMP, TO_CHAR(DTNEG, 'YYYY-MM')
    ORDER BY MES DESC, CODEMP
    """
    
    try:
        data = sankhya.execute_query(sql)
        if not data: return "Nenhuma venda encontrada no período."
        
        # Processamento de Consolidação Literária
        consolidated = []
        for r in data:
            emp = r['CODEMP']
            seg = "ATACADO" if emp in atacado_ids else "INDÚSTRIA"
            consolidated.append({
                "Mês": r['MES'],
                "Segmento": seg,
                "Empresa": emp,
                "Venda Líquida": f"R$ {r['TOTAL']:,.2f}"
            })
            
        return "### 📊 Lente de Vendas Consolidada (Últimos 3 Meses)\n" + \
               format_as_markdown_table(consolidated)
    except Exception as e:
        return f"Erro ao processar lente de vendas: {str(e)}"

def get_finance_hotspot_lens() -> str:
    """
    Lente focada em 'Pontos de Calor' financeiros: Pendências, Lançamentos Sem Natureza e Alertas de Ruído.
    """
    rules = _get_rules()
    
    # 1. Alerta de Natureza Errada (Saída em Receita) - Ignorando Compensações e TOP 900 (Orçamento)
    sql_noise = """
    SELECT COUNT(*) as QTD, SUM(VLRDESDOB) as TOTAL 
    FROM TGFFIN 
    WHERE CODNAT = 1010100 
      AND RECDESP = -1 
      AND DTNEG > SYSDATE - 30
      AND CODTIPOPER <> 900
      AND HISTORICO NOT LIKE '%Compensa%'
      AND HISTORICO NOT LIKE '%Devolu%'
    """
    
    # 2. Lançamentos Sem Natureza - Ignorando TOP 900
    sql_unbound = "SELECT COUNT(*) as QTD, SUM(VLRDESDOB) as TOTAL FROM TGFFIN WHERE CODNAT = 0 AND DTNEG > SYSDATE - 60 AND CODTIPOPER <> 900"
    
    try:
        noise = sankhya.execute_query(sql_noise)[0]
        unbound = sankhya.execute_query(sql_unbound)[0]
        
        report = ["### ⚡ Lente de Saúde Financeira (Alertas de Qualidade)\n"]
        
        if noise['QTD'] > 0:
            report.append(f"⚠️ **Ruído na Receita:** {noise['QTD']} lançamentos (R$ {noise['TOTAL']:,.2f}) detectados como saída na conta de venda. Isso distorce seu lucro bruto.")
            
        if unbound['QTD'] > 0:
            report.append(f"🔴 **Pontos Cegos:** R$ {unbound['TOTAL']:,.2f} em {unbound['QTD']} lançamentos estão sem classificação (Natureza 0).")
            
        if noise['QTD'] == 0 and unbound['QTD'] == 0:
            report.append("✅ **Qualidade de Dados:** Nenhuma inconsistência grave detectada nos últimos 60 dias.")
            
        return "\n\n".join(report)
    except Exception as e:
        return f"Erro ao processar lente financeira: {str(e)}"
