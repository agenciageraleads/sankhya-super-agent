import sys
import os

# Adiciona o diretório mcp_server ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "mcp_server"))

try:
    from tools import investigate_system_behavior
    print("✅ Ferramenta de proatividade importada com sucesso.")
except ImportError as e:
    print(f"❌ Erro ao importar ferramenta: {e}")
    sys.exit(1)

def test_proactivity_skill():
    print("\n--- Testando Skill de Proatividade: Investigando 'TGFCAB' ---")
    try:
        # Tenta investigar a tabela principal de cabeçalho de notas
        report = investigate_system_behavior("Quero entender a tabela TGFCAB")
        print(report)
        
        if "Metadados da Tabela `TGFCAB`" in report and "Amostra de Dados Reais" in report:
            print("\n✅ Teste de Proatividade concluído com sucesso.")
        else:
            print("\n⚠️ O relatório parece incompleto.")
            
    except Exception as e:
        print(f"❌ Erro durante a execução da skill: {e}")

if __name__ == "__main__":
    test_proactivity_skill()
