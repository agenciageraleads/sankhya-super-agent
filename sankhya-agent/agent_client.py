import os
import json
import logging
import re
from openai import OpenAI
from dotenv import load_dotenv

from mcp_server.tools import register_tools, GLOBAL_TOOL_REGISTRY, get_openai_tools_schema

# Inicializa o registro de ferramentas (incluindo skills dinâmicas)
register_tools()

load_dotenv()
logger = logging.getLogger("ssa-client")

# Configuração da OpenAI
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

def get_system_prompt():
    """Gera o prompt do sistema com a lista atual de ferramentas disponíveis."""
    tools_list = "\n".join([f"- `{name}`: {func.__doc__.strip().split('\\n')[0] if func.__doc__ else 'Sem descrição'}" 
                             for name, func in GLOBAL_TOOL_REGISTRY.items()])
    
    return f"""
Você é o Sankhya Super Agent (SSA), um assistente especializado no ERP Sankhya.
Sua missão é ajudar usuários (diretores, gerentes, suporte) a obter informações do sistema.

**Regras de Ouro:**
1. **Segurança Primeiro:** Você tem ferramentas de LEITURA e algumas de APOIO. Se o usuário pedir para deletar, explique que não pode.
2. **Contexto:** Use as ferramentas disponíveis para responder. Não invente dados.
3. **Formatação:** As ferramentas retornam tabelas em Markdown. Repasse-as para o usuário.
4. **Explicação:** Se uma query retornar vazio, sugira o motivo.
5. **Business:** Você atua na empresa "Portal Distribuidora / B&B".

**Ferramentas Ativas no Momento:**
{tools_list}
"""

# Schemas dinâmicos para a OpenAI
def get_tools_schema():
    return get_openai_tools_schema()

# Mapa de execução gerado dinamicamente
def get_available_functions():
    return GLOBAL_TOOL_REGISTRY


def run_simulation(last_message: str):
    """
    Modo SIMULAÇÃO (Sem OpenAI):
    Usa regras simples (regex) para detectar a intenção do usuário e chamar ferramentas.
    """
    msg = last_message.lower()
    
    # 1. Estoque (Ex: "saldo produto 20")
    match_estoque = re.search(r"(estoque|saldo).*?(\d+)", msg)
    if match_estoque:
        codprod = int(match_estoque.group(2))
        return get_stock_info(codprod=codprod)

    # 2. Parceiro (Ex: "parceiro 1")
    match_parceiro = re.search(r"(parceiro|cliente|fornecedor).*?(\d+)", msg)
    if match_parceiro:
        codparc = int(match_parceiro.group(2))
        return get_partner_info(codparc=codparc)
        
    # 3. Nota Fiscal (Ex: "nota 12345")
    match_nota = re.search(r"(nota|pedido).*?(\d+)", msg)
    if match_nota:
        nunota = int(match_nota.group(2))
        # Retorna cabeçalho + itens
        header = get_invoice_header(nunota=nunota)
        items = get_invoice_items(nunota=nunota)
        return f"{header}\n\n{items}"

    # 4. Colunas de Tabela (Ex: "colunas da TGFPRO")
    match_colunas = re.search(r"(coluna|tabela|estrutura).*?(tgf\w+|tsi\w+)", msg)
    if match_colunas:
        table = match_colunas.group(2).upper()
        return get_table_columns(table_name=table)

    # 5. Listar Tabelas
    if "quais tabelas" in msg or "listar tabelas" in msg:
        return list_tables()

    # 6. Docs (Ex: "como consultar")
    if "como" in msg or "consultar" in msg or "processo" in msg or "ajuda" in msg:
        return search_docs(query=msg)

    # 7. Fallback SQL (Ex: "sql select * from tgfpro")
    if msg.strip().startswith("sql"):
         sql = msg.replace("sql", "", 1).strip()
         return run_sql_select(sql=sql)

    return (
        "⚠️ **Modo Simulação (Sem IA)**: Não entendi o comando.\n\n"
        "Tente comandos diretos como:\n"
        "- 'Saldo do produto 20'\n"
        "- 'Parceiro 1'\n"
        "- 'Nota 12345'\n"
        "- 'Colunas da TGFPRO'\n"
        "- 'Como consultar notas?'\n"
        "- 'SQL SELECT * FROM TGFCAB WHERE ROWNUM <= 5'"
    )


def run_conversation(messages):
    """
    Gerencia o loop de conversa. 
    Se não tiver cliente OpenAI configurado, usa o modo SIMULAÇÃO.
    """
    # Se não tem API Key, roda simulação local
    if not client:
        # Pega a última mensagem do usuário na lista
        for m in reversed(messages):
            if m["role"] == "user":
                last_msg = m["content"]
                break
        else:
            last_msg = ""
            
        return f"**[MODO SIMULAÇÃO - SEM OPENAI KEY]**\n\n" + str(run_simulation(last_msg))

    # Fluxo OpenAI Real
    try:
        # Pede os schemas e mapas atuais (suporta Hot Reload)
        system_prompt = get_system_prompt()
        tools_schema = get_tools_schema()
        available_functions = get_available_functions()

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}] + messages,
            tools=tools_schema,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            # Adiciona a intenção do assistente ao histórico
            messages.append(response_message) 

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                tool_function = available_functions.get(function_name)
                if not tool_function:
                    continue
                
                print(f"🛠️ Executando: {function_name}({function_args})")
                
                try:
                    function_response = tool_function(**function_args)
                except Exception as e:
                    function_response = f"Erro na execução da ferramenta: {str(e)}"

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                })

            second_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}] + messages
            )
            return second_response.choices[0].message.content

        return response_message.content

    except Exception as e:
        logger.warning(f"Falha na OpenAI ({str(e)}). Entrando em modo FALLBACK (Simulação).")
        # Fallback: Tenta extrair a última mensagem do usuário e rodar simulação
        last_user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_msg = m["content"]
                break
        
        return f"⚠️ **[MODO FALLBACK - ERRO OPENAI]**\n\n{run_simulation(last_user_msg)}"
