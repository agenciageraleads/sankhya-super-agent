import sys
import os

# Adiciona o diretório mcp_server ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "mcp_server"))

try:
    from tools import generate_purchase_suggestion, list_tables
    print("✅ Ferramentas importadas com sucesso.")
except ImportError as e:
    print(f"❌ Erro ao importar ferramentas: {e}")
    sys.path.append(os.path.dirname(__file__))
    from mcp_server.tools import generate_purchase_suggestion

def test_procurement_skill():
    print("\n--- Testando Analista de Compras: Sugestão Curva A ---")
    try:
        # Tenta gerar sugestão para Curva A (os 20 mais vendidos)
        report = generate_purchase_suggestion(criteria="curva_a")
        print(report)
        
        if "Dossiê de Compras" in report:
            print("\n✅ Teste de Dossiê concluído com sucesso.")
        else:
            print("\n⚠️ O relatório parece não conter o título esperado.")
            
    except Exception as e:
        print(f"❌ Erro durante a execução da skill: {e}")

if __name__ == "__main__":
    test_procurement_skill()
