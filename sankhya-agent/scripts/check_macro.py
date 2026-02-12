
from mcp_server.utils import sankhya
import logging

logging.basicConfig(level=logging.INFO)

def check_tgfpro():
    sql = """
        SELECT column_name 
        FROM all_tab_columns 
        WHERE table_name = 'TGFPRO' AND column_name LIKE '%MACRO%'
        ORDER BY column_name
    """
    try:
        rows = sankhya.execute_query(sql)
        print([r['COLUMN_NAME'] for r in rows])
        
        # Check TGFGRU content again for any non-null
        sql2 = "SELECT COUNT(*) as QTD FROM TGFGRU WHERE AD_CATMACRO IS NOT NULL"
        rows2 = sankhya.execute_query(sql2)
        print(f'Count AD_CATMACRO: {rows2}')

    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    check_tgfpro()

