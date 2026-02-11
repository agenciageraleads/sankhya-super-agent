"""
Agente gerado automaticamente pelo Orquestrador para: analisar contas a pagar
Baseado na tabela: TSICTA
"""
import logging
try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

logger = logging.getLogger("skill-tsicta")

def analyze_tsicta_data(limit: int = 10) -> str:
    """Analisa os últimos registros da tabela TSICTA."""
    sql = f"SELECT * FROM TSICTA WHERE ROWNUM <= {limit}"
    try:
        result = sankhya.execute_query(sql)
        if not result:
            return "Nenhum dado encontrado em TSICTA."
        return f"**Análise de TSICTA:**\n\n" + format_as_markdown_table(result)
    except Exception as e:
        return f"Erro ao analisar TSICTA: {str(e)}"
