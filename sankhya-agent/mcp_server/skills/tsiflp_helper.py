"""
Agente gerado automaticamente pelo Orquestrador para: analisar duplicidade e processos produtivos de matéria prima
Baseado na tabela: TSIFLP
"""
import logging
try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

logger = logging.getLogger("skill-tsiflp")

def analyze_tsiflp_data(limit: int = 10) -> str:
    """Analisa os últimos registros da tabela TSIFLP."""
    sql = f"SELECT * FROM TSIFLP WHERE ROWNUM <= {limit}"
    try:
        result = sankhya.execute_query(sql)
        if not result:
            return "Nenhum dado encontrado em TSIFLP."
        return f"**Análise de TSIFLP:**\n\n" + format_as_markdown_table(result)
    except Exception as e:
        return f"Erro ao analisar TSIFLP: {str(e)}"
