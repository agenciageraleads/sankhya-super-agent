import requests
import urllib.parse
from typing import List, Dict, Any

ZENDESK_BASE_URL = "https://ajuda.sankhya.com.br/api/v2/help_center"

def search_zendesk_help_center(query: str, limit: int = 5) -> str:
    """
    Pesquisa em tempo real na Central de Ajuda Sankhya (Zendesk).
    Use esta ferramenta quando a busca local (search_solutions) não retornar resultados satisfatórios
    ou para buscar informações muito recentes.
    
    Args:
        query: Termos de pesquisa (ex: "erro nota fiscal 123", "como cadastrar parceiro").
        limit: Número máximo de resultados (padrão 5).
    """
    try:
        # Endpoint de busca da Zendesk API V2
        # Documentação: https://developer.zendesk.com/api-reference/help_center/help-center-api/search/
        encoded_query = urllib.parse.quote(query)
        url = f"{ZENDESK_BASE_URL}/articles/search.json?query={encoded_query}&per_page={limit}&locale=pt-br"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return f"❌ Erro na API Zendesk: {response.status_code} - {response.text}"
            
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            return f"Nenhum resultado encontrado na Central de Ajuda online para: '{query}'"
            
        formatted_results = []
        for item in results:
            title = item.get("title", "Sem título")
            html_url = item.get("html_url", "#")
            snippet = item.get("snippet", "Sem descrição")
            # Remove tags HTML básicas do snippet se houver
            snippet = snippet.replace("<em>", "**").replace("</em>", "**")
            
            formatted_results.append(f"### 🌐 [{title}]({html_url})\n{snippet}\n\n[Ler artigo completo]({html_url})")
            
        return f"**Resultados online na Central de Ajuda Sankhya para '{query}':**\n\n" + "\n\n---\n\n".join(formatted_results)

    except Exception as e:
        return f"❌ Erro ao conectar na Zendesk: {str(e)}"
