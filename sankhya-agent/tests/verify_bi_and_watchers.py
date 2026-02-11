import os
import sys

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.join(os.getcwd()))

from mcp_server.tools import register_tools, GLOBAL_TOOL_REGISTRY, generate_chart_report

def test_features():
    print("🚀 Iniciando testes das novas funcionalidades...")
    
    # 1. Registro e Descoberta Dinâmica
    register_tools()
    print(f"✅ Ferramentas registradas: {len(GLOBAL_TOOL_REGISTRY)}")
    
    # 2. Teste de Gráfico (BI Conversacional)
    print("\n📊 Testando Geração de Gráfico...")
    # SQL simulando saldo por banco (TSICTA)
    sql_bancos = "SELECT DESCRICAO, SALDOREAL FROM TSICTA WHERE ATIVA = 'S' AND ROWNUM <= 5"
    res_chart = generate_chart_report(sql_bancos, chart_type="bar", title="Saldo por Banco")
    if "plotly" in res_chart:
        print("✅ Gráfico (JSON) gerado com sucesso!")
        # print(res_chart[:200] + "...")
    else:
        print(f"❌ Falha ao gerar gráfico: {res_chart}")

    # 3. Teste de Monitoramento Proativo (Watchers)
    print("\n🚨 Testando Monitoramento Proativo (Watchers)...")
    if "run_all_watchers" in GLOBAL_TOOL_REGISTRY:
        run_watchers = GLOBAL_TOOL_REGISTRY["run_all_watchers"]
        res_watchers = run_watchers()
        print("✅ Watchers executados!")
        print(f"Relatório resumido:\n{res_watchers[:300]}...")
    else:
        print("❌ Ferramenta 'run_all_watchers' não encontrada no registro!")

if __name__ == "__main__":
    test_features()
