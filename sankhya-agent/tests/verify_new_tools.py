import sys
import os
import json

# Adiciona o diretório mcp_server ao path para importar tools
sys.path.append(os.path.join(os.path.dirname(__file__), "mcp_server"))

# Importa as ferramentas a serem testadas
# Nota: Isso vai instanciar o SankhyaGatewayClient que tentará autenticar se houver credenciais.
try:
    from tools import search_solutions, load_records, test_connection
    print("✅ Módulo tools importado com sucesso.")
except Exception as e:
    print(f"❌ Erro ao importar tools: {e}")
    sys.exit(1)

def test_kb():
    print("\n--- Testando Knowledge Base (search_solutions) ---")
    query = "Rejeição 997: Série"
    result = search_solutions(query)
    
    if "Nenhuma solução encontrada" in result:
        print(f"⚠️ Aviso: Nenhum resultado para '{query}'. A base pode estar vazia ou a query não corresponde.")
    elif "Erro ao buscar" in result:
        print(f"❌ Erro na busca: {result}")
    else:
        print(f"✅ Busca retornou resultados. Preview:\n{result[:300]}...")

def test_api_connection():
    print("\n--- Testando Conexão API (test_connection) ---")
    result = test_connection()
    print(f"Resultado: {result}")
    
    if "✅" in result:
        return True
    return False

def test_load_records():
    print("\n--- Testando Leitura Universal (load_records - Usuario) ---")
    # Tenta buscar o usuário logado (ou qualquer usuário) para não expor dados sensíveis
    # Usando critério vazio para trazer os primeiros, mas limitando campos
    result = load_records(entity_name="Usuario", criteria="", fields=["CODUSU", "NOMEUSU"])
    print(f"Resultado:\n{result[:500]}...") # Log curto

if __name__ == "__main__":
    print("Iniciando bateria de testes do Sankhya Super Agent...")
    
    # 1. Testa KB (não depende de credenciais Sankhya)
    test_kb()
    
    # 2. Testa Conexão API
    if test_api_connection():
        # 3. Se conectado, testa load_records
        test_load_records()
    else:
        print("\n⚠️ Pular testes de API Universal pois a conexão falhou (verifique .env).")
        
    print("\nValidação concluída.")
