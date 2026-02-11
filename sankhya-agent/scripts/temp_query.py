import sys
import os
import json

# Adiciona o diretório mcp_server ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "mcp_server"))

try:
    from tools import run_sql_select
except ImportError:
    print("❌ Falha ao importar run_sql_select.")
    sys.exit(1)

def check_tipmov():
    print("--- Verificando Tipos de Movimento (TGFCAB) ---")
    sql = "SELECT TIPMOV, COUNT(*) as QTD FROM TGFCAB GROUP BY TIPMOV"
    print(run_sql_select(sql))

def check_tgftop():
    print("\n--- Verificando Descrição de Operações (TGFTOP) ---")
    sql = "SELECT CODTOP, DESCROPER, TIPMOV FROM TGFTOP WHERE ROWNUM <= 20 ORDER BY TIPMOV"
    print(run_sql_select(sql))

if __name__ == "__main__":
    check_tipmov()
    check_tgftop()
