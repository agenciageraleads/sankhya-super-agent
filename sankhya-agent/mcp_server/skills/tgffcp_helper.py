"""
Agente especializado em Diagnóstico de TGFFCP
Gerado para: analisar duplicidade e composição de matéria prima nos processos de produção para os códigos 17364, 153363 e 17756
"""
import logging
try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

logger = logging.getLogger("skill-tgffcp")

def diagnose_tgffcp_issue(limit: int = 10) -> str:
    """Realiza um diagnóstico profundo baseado nos registros de TGFFCP."""
    sql = "SELECT * FROM TGFFCP WHERE NUNOTA IN (17364, 153363, 17756)"
    try:
        result = sankhya.execute_query(sql)
        if not result:
            return "Nenhum registro problemático encontrado em TGFFCP."
            
        res = f"### 🔍 Diagnóstico de TGFFCP (analisar duplicidade e composição de matéria prima nos processos de produção para os códigos 17364, 153363 e 17756)\n\n"
        res += format_as_markdown_table(result)
        
        ids_found = [r.get('CODPROD') or r.get('NUNOTA') for r in result if r.get('CODPROD') or r.get('NUNOTA')]
        
        
        res += "\n\n**💡 Recomendação SSA:**\nPara unificar produtos duplicados, escolha o código principal e transfira o estoque (TGFEST) via 'Nota de Transferência' ou 'Ajuste de Estoque'. Verifique se os códigos secundários estão vinculados a Estruturas de Produto/Produção antes de inativá-los."
        
        return res
    except Exception as e:
        return f"Erro no diagnóstico: {str(e)}"
