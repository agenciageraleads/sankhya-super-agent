import sys
import os

# Adiciona o diretório mcp_server ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "mcp_server"))

try:
    from tools import run_sql_select
except ImportError:
    print("❌ Falha ao importar run_sql_select.")
    sys.exit(1)

def analyze_cable_patterns():
    print("--- Analisando Padrões de Cabos e Cores (TGFPRO) ---")
    # Busca produtos que contenham keywords de cabos e cores comuns
    sql = """
    SELECT DESCRPROD, MARCA, CODGRUPOPROD 
    FROM TGFPRO 
    WHERE (DESCRPROD LIKE '%CABO%' OR DESCRPROD LIKE '%FLEXIVEL%')
    AND ROWNUM <= 50
    """
    print(run_sql_select(sql))

def detect_color_suffixes():
    print("\n--- Detectando Sufixos de Cores Comuns ---")
    # Tenta identificar abreviações de cores no final ou meio das strings
    sql = """
    SELECT DISTINCT SUBSTR(DESCRPROD, INSTR(DESCRPROD, ' ', -1) + 1) as POSSIVEL_COR, COUNT(*)
    FROM TGFPRO
    WHERE DESCRPROD LIKE '%CABO%'
    GROUP BY SUBSTR(DESCRPROD, INSTR(DESCRPROD, ' ', -1) + 1)
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    """
    print(run_sql_select(sql))

if __name__ == "__main__":
    analyze_cable_patterns()
    detect_color_suffixes()
