
import logging
import sys
import os

# Adjust path to find modules
sys.path.append(os.getcwd())

from mcp_server.utils import sankhya

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug-giro")

def debug_giro_table():
    print("--- Debugging TGFGIR Table ---")
    
    # Check 1: Count total records
    try:
        count = sankhya.execute_query("SELECT COUNT(*) AS QTD FROM TGFGIR")
        print(f"Total Rows in TGFGIR: {count}")
    except Exception as e:
        print(f"Error counting TGFGIR: {e}")

    # Check 2: Check distinct CODREL and CODEMP
    try:
        summary = sankhya.execute_query("SELECT CODREL, CODEMP, COUNT(*) as QTD FROM TGFGIR GROUP BY CODREL, CODEMP")
        print("Summary of TGFGIR (CODREL, CODEMP):")
        for row in summary:
            print(row)
    except Exception as e:
        print(f"Error checking summary: {e}")
        
    # Check 3: Check Columns (Select * limit 1)
    try:
        sample = sankhya.execute_query("SELECT * FROM TGFGIR WHERE ROWNUM <= 1")
        if sample:
            print("Sample Row columns:", sample[0].keys())
        else:
            print("No sample row found.")
    except Exception as e:
        print(f"Error fetching sample: {e}")

if __name__ == "__main__":
    debug_giro_table()
