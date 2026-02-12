
from mcp_server.utils import sankhya
import logging

logging.basicConfig(level=logging.INFO)

def list_columns():
    sql = """
        SELECT column_name 
        FROM all_tab_columns 
        WHERE table_name = 'TGFGRU' 
        ORDER BY column_name
    """
    try:
        rows = sankhya.execute_query(sql)
        print([r['COLUMN_NAME'] for r in rows])
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    list_columns()

