"""
Módulo de Inteligência Financeira e Tradução Contábil (Intercompany).
Responsável por traduzir regras de negócio complexas para relatórios de BI.
"""
import logging
from typing import List, Dict, Any, Optional

try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

logger = logging.getLogger("skill-finance-ai")

import json
import os

def load_business_rules():
    """Carrega as regras de negócio do arquivo centralizado."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "knowledge", "business_rules.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar business_rules.json: {e}")
        return {}

def get_segment_name(emp_id: int) -> str:
    rules = load_business_rules()
    group_struct = rules.get("group_structure", {})
    for name, data in group_struct.items():
        if emp_id in data.get("emp_ids", []):
            return f"{name} ({', '.join(map(str, data['emp_ids']))})"
    return f"Empresa {emp_id} (Outras)"

def analyze_productivity_by_unit() -> str:
    """
    Analisa a produtividade por SEGMENTO do grupo.
    Cruza Faturamento vs Custo de Pessoal (Parceiro 3).
    """
    # 1. Faturamento dos últimos 3 meses
    sql_vendas = """
    SELECT CODEMP, SUM(VLRNOTA) as FATURAMENTO 
    FROM TGFCAB 
    WHERE STATUSNOTA = 'L' AND TIPMOV = 'V' AND DTNEG > ADD_MONTHS(SYSDATE, -3)
    GROUP BY CODEMP
    """
    
    # 2. Custo de Pessoal (Parceiro 3)
    sql_pessoal = """
    SELECT CODEMP, SUM(VLRDESDOB) as CUSTO_PESSOAL
    FROM TGFFIN
    WHERE CODPARC = 3 AND DTNEG > ADD_MONTHS(SYSDATE, -3)
    GROUP BY CODEMP
    """
    
    try:
        vendas_data = sankhya.execute_query(sql_vendas)
        custos_data = sankhya.execute_query(sql_pessoal)
        
        consolidated = {}

        for r in vendas_data:
            seg = get_segment_name(r['CODEMP'])
            if seg not in consolidated: consolidated[seg] = {"fat": 0, "custo": 0}
            consolidated[seg]["fat"] += r['FATURAMENTO']
            
        for r in custos_data:
            seg = get_segment_name(r['CODEMP'])
            if seg not in consolidated: consolidated[seg] = {"fat": 0, "custo": 0}
            consolidated[seg]["custo"] += r['CUSTO_PESSOAL']
            
        results = []
        for group, vals in consolidated.items():
            fat = vals["fat"]
            custo = vals["custo"]
            produtividade = fat / custo if custo > 0 else 0
            peso_percent = (custo / fat * 100) if fat > 0 else 0
            
            results.append({
                "GRUPO": group,
                "FATURAMENTO": f"R$ {fat:,.2f}",
                "CUSTO PESSOAL": f"R$ {custo:,.2f}",
                "PRODUTIVIDADE": f"{produtividade:.2f}x",
                "PESO (%)": f"{peso_percent:.1f}%"
            })
            
        res_table = format_as_markdown_table(results)
        
        chart_data = {
            "data": [
                {
                    "type": "bar",
                    "name": "Faturamento",
                    "x": [r['GRUPO'] for r in results],
                    "y": [consolidated[r['GRUPO']]["fat"] for r in results]
                },
                {
                    "type": "bar",
                    "name": "Custo Pessoal (3)",
                    "x": [r['GRUPO'] for r in results],
                    "y": [consolidated[r['GRUPO']]["custo"] for r in results]
                }
            ],
            "layout": {
                "title": "Produtividade Consolidada (1+5)",
                "barmode": "group",
                "template": "plotly_dark"
            }
        }
        
        import json
        return f"### 📊 Análise de Produtividade por Unidade\n\n{res_table}\n\n" + \
               f"**Insights SSA:**\n" + \
               f"- Uma produtividade de **5.00x** significa que para cada R$ 1,00 gasto com o Parceiro 3, a empresa fatura R$ 5,00.\n" + \
               f"- Verifique as unidades onde o **Peso (%)** está acima da média do grupo.\n\n" + \
               f"```json-chart\n{json.dumps(chart_data)}\n```"

    except Exception as e:
        return f"Erro na análise de produtividade: {str(e)}"
