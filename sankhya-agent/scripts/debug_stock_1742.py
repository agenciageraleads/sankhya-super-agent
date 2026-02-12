
from mcp_server.utils import sankhya
import logging

logging.basicConfig(level=logging.INFO)

def check_stock():
    # Check what is in TGFGIR for Product 1742 (ABRAC ACO P/ LAMP TUB T8)
    # Filter by Report 2535 and Companies 1, 5
    sql = """
        SELECT CODEMP, CODLOCAL, ESTOQUE, GIRODIARIO, SUGCOMPRA
        FROM TGFGIR
        WHERE CODPROD = 1742
          AND CODREL = 2535
          AND CODEMP IN (1, 5)
    """
    try:
        rows = sankhya.execute_query(sql)
        print(f'Rows for 1742: {rows}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    check_stock()

