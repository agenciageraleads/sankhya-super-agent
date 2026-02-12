
from mcp_server.utils import sankhya
import logging

logging.basicConfig(level=logging.INFO)

def list_macro_groups():
    sql = """
        SELECT DISTINCT AD_CATMACRO 
        FROM TGFGRU 
        WHERE AD_CATMACRO IS NOT NULL
        ORDER BY AD_CATMACRO
    """
    try:
        rows = sankhya.execute_query(sql)
        print([r['AD_CATMACRO'] for r in rows])
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    list_macro_groups()

