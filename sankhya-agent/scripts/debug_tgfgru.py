
from mcp_server.utils import sankhya
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)

def inspect_tgfgru():
    # Dump raw data for inspection
    sql = """
        SELECT CODGRUPOPROD, DESCRGRUPOPROD, AD_CATMACRO 
        FROM TGFGRU 
        WHERE ROWNUM <= 20
        ORDER BY CODGRUPOPROD
    """
    try:
        rows = sankhya.execute_query(sql)
        df = pd.DataFrame(rows)
        print(df.to_string())
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    inspect_tgfgru()

