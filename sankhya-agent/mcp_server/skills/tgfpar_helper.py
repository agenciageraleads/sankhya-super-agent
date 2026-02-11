"""
Agente gerado automaticamente pelo Orquestrador para: analisar parceiros
Baseado na tabela: TGFPAR
"""
import logging
try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

logger = logging.getLogger("skill-tgfpar")

def analyze_tgfpar_data(limit: int = 10) -> str:
    """Analisa os últimos registros da tabela TGFPAR."""
    sql = f"SELECT * FROM TGFPAR WHERE ROWNUM <= {limit}"
    try:
        result = sankhya.execute_query(sql)
        if not result:
            return "Nenhum dado encontrado em TGFPAR."
        return f"**Análise de TGFPAR:**\n\n" + format_as_markdown_table(result)
    except Exception as e:
        return f"Erro ao analisar TGFPAR: {str(e)}"
