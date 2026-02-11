import os
import json
import logging
import re
from openai import OpenAI
from dotenv import load_dotenv

from mcp_server.tools import register_tools, GLOBAL_TOOL_REGISTRY, get_openai_tools_schema

# Inicializa o registro de ferramentas (incluindo skills dinâmicas)
register_tools()

load_dotenv(override=True)
logger = logging.getLogger("ssa-client")

# Configuração da OpenAI
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


def _run_auto_learning(function_name: str, function_args: dict, function_response: str, available_functions: dict) -> None:
    """
    Gatilhos determinísticos de auto-learning.
    Não depende do LLM lembrar de chamar a tool de aprendizado.
    """
    propose_fn = available_functions.get("propose_new_rule")
    if not propose_fn:
        return

    resp = (function_response or "").lower()
    rule_id = None
    condition = None
    description = None

    # Caso clássico observado no projeto: SQL MySQL em ambiente Oracle.
    if "ora-00904" in resp and ("curdate" in resp or "date_trunc" in resp):
        rule_id = "oracle_date_functions_only"
        condition = "SQL com funções MySQL/Postgres de data (CURDATE, DATE_TRUNC) em ambiente Oracle"
        description = (
            "Ao gerar SQL para Sankhya/Oracle, usar TRUNC(SYSDATE), SYSDATE e TO_CHAR; "
            "nunca usar CURDATE/DATE_TRUNC."
        )

    # Reforça regra de query única para evitar bloqueios frequentes na validação.
    elif "ponto-e-vírgula detectado" in resp or "apenas um statement por vez" in resp:
        rule_id = "single_statement_sql_only"
        condition = "Tentativa de executar SQL com múltiplos statements"
        description = "Toda execução SQL deve conter apenas um SELECT/WITH sem ponto-e-vírgula."

    if not rule_id:
        return

    try:
        learning_msg = propose_fn(rule_id=rule_id, condition=condition, description=description)
        logger.info(f"Auto-learning acionado ({rule_id}) após {function_name}: {learning_msg}")
    except Exception as e:
        logger.warning(f"Falha ao registrar auto-learning ({rule_id}): {str(e)}")


def _sanitize_sql_tail(sql: str) -> str:
    cleaned = (sql or "").strip()
    while cleaned.endswith(";"):
        cleaned = cleaned[:-1].rstrip()
    return cleaned


def _retry_tool_if_recoverable(function_name: str, function_args: dict, function_response: str, tool_function):
    """
    Auto-correção silenciosa para erros recuperáveis.
    Ex.: SQL bloqueada apenas por ';' no final.
    """
    resp = (function_response or "").lower()
    if function_name not in {"run_sql_select", "generate_chart_report"}:
        return function_response
    if "ponto-e-vírgula detectado" not in resp and "apenas um statement por vez" not in resp:
        return function_response

    sql = function_args.get("sql")
    if not isinstance(sql, str):
        return function_response

    fixed_sql = _sanitize_sql_tail(sql)
    if fixed_sql == sql:
        return function_response

    new_args = dict(function_args)
    new_args["sql"] = fixed_sql
    try:
        logger.info(f"Auto-correção SQL aplicada em {function_name}: removido ';' final e reexecutando.")
        return tool_function(**new_args)
    except Exception:
        return function_response

def get_system_prompt():
    """Gera o prompt do sistema com a lista atual de ferramentas disponíveis."""
    tools_list = "\n".join([f"- `{name}`: {func.__doc__.strip().split('\\n')[0] if func.__doc__ else 'Sem descrição'}" 
                             for name, func in GLOBAL_TOOL_REGISTRY.items()])
    
    return f"""
Você é o Sankhya Super Agent (SSA), um assistente especializado no ERP Sankhya.
Sua missão é ajudar usuários (diretores, gerentes, suporte) a obter informações do sistema.

**Regras de Ouro:**
1. **Segurança Primeiro:** Operações de escrita (criar/alterar/cancelar/faturar) são bloqueadas por padrão no SSA. Se o usuário pedir algo que altere dados, explique que não pode.
2. **Contexto:** Use as ferramentas disponíveis para responder. Não invente dados.
3. **Formatação:** As ferramentas retornam tabelas em Markdown. Repasse-as para o usuário.
4. **Explicação:** Se uma query retornar vazio, sugira o motivo.
5. **Business:** Você atua na empresa "Portal Distribuidora / B&B".
6. **Relatórios diários:** Para pedidos de "vendas diárias", "vendas de hoje" ou "empresa X e Y", prefira a ferramenta `get_daily_sales_report` antes de SQL livre.
7. **Multiempresa:** Em pedidos de indicadores/relatórios que dependem de empresa, sempre confirmar escopo (empresa específica ou todas). Se o usuário não escolher, responda com todas as empresas e explicite essa premissa.
8. **SQL no Sankhya:** Nunca finalize SQL com ponto-e-vírgula (`;`). Gere apenas um único statement.

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
    available_functions = get_available_functions()

    # 0. Vendas diárias / hoje (com filtro de empresas opcional)
    if "venda" in msg and ("diari" in msg or "diári" in msg or "hoje" in msg):
        fn = available_functions.get("get_daily_sales_report")
        if fn:
            days = 1 if "hoje" in msg else 7
            nums = re.findall(r"\b\d+\b", msg)
            codemp_csv = ",".join(nums) if nums else ""
            result = fn(days=days, codemp_csv=codemp_csv)
            if not codemp_csv:
                return "ℹ️ Escopo aplicado: **todas as empresas** (nenhuma empresa específica foi informada).\n\n" + result
            return result
        return "Ferramenta `get_daily_sales_report` não está disponível."
    
    # 1. Estoque (Ex: "saldo produto 20")
    match_estoque = re.search(r"(estoque|saldo).*?(\d+)", msg)
    if match_estoque:
        codprod = int(match_estoque.group(2))
        fn = available_functions.get("get_stock_info")
        return fn(codprod=codprod) if fn else "Ferramenta `get_stock_info` não está disponível."

    # 2. Parceiro (Ex: "parceiro 1")
    match_parceiro = re.search(r"(parceiro|cliente|fornecedor).*?(\d+)", msg)
    if match_parceiro:
        codparc = int(match_parceiro.group(2))
        fn = available_functions.get("get_partner_info")
        return fn(codparc=codparc) if fn else "Ferramenta `get_partner_info` não está disponível."
        
    # 3. Nota Fiscal (Ex: "nota 12345")
    match_nota = re.search(r"(nota|pedido).*?(\d+)", msg)
    if match_nota:
        nunota = int(match_nota.group(2))
        # Retorna cabeçalho + itens
        fn_header = available_functions.get("get_invoice_header")
        fn_items = available_functions.get("get_invoice_items")
        header = fn_header(nunota=nunota) if fn_header else "Ferramenta `get_invoice_header` não está disponível."
        items = fn_items(nunota=nunota) if fn_items else "Ferramenta `get_invoice_items` não está disponível."
        return f"{header}\n\n{items}"

    # 4. Colunas de Tabela (Ex: "colunas da TGFPRO")
    match_colunas = re.search(r"(coluna|tabela|estrutura).*?(tgf\w+|tsi\w+)", msg)
    if match_colunas:
        table = match_colunas.group(2).upper()
        fn = available_functions.get("get_table_columns")
        return fn(table_name=table) if fn else "Ferramenta `get_table_columns` não está disponível."

    # 5. Listar Tabelas
    if "quais tabelas" in msg or "listar tabelas" in msg:
        fn = available_functions.get("list_tables")
        return fn() if fn else "Ferramenta `list_tables` não está disponível."

    # 6. Docs (Ex: "como consultar")
    if "como" in msg or "consultar" in msg or "processo" in msg or "ajuda" in msg:
        fn = available_functions.get("search_docs")
        return fn(query=msg) if fn else "Ferramenta `search_docs` não está disponível."

    # 7. Fallback SQL (Ex: "sql select * from tgfpro")
    if msg.strip().startswith("sql"):
         sql = msg.replace("sql", "", 1).strip()
         fn = available_functions.get("run_sql_select")
         return fn(sql=sql) if fn else "Ferramenta `run_sql_select` não está disponível."

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
        # Garante hot-reload das skills mesmo sem OpenAI.
        register_tools()
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
        # Hot-reload real: sempre reindexa ferramentas/skills antes de cada rodada.
        register_tools()
        # Pede os schemas e mapas atuais (suporta Hot Reload)
        system_prompt = get_system_prompt()
        tools_schema = get_tools_schema()
        available_functions = get_available_functions()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
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

                # Se der erro recuperável, tenta corrigir e reexecutar sem expor o erro bruto ao usuário.
                function_response = _retry_tool_if_recoverable(
                    function_name=function_name,
                    function_args=function_args,
                    function_response=str(function_response),
                    tool_function=tool_function,
                )

                # Aprendizado automático pós-execução de ferramenta.
                _run_auto_learning(function_name, function_args, str(function_response), available_functions)

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                })

            second_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_prompt}] + messages
            )
            return second_response.choices[0].message.content

        return response_message.content

    except Exception as e:
        error_msg = str(e)

        # Mensagens mais acionáveis no UI (gadget) quando a OpenAI falha.
        if "429" in error_msg or "insufficient_quota" in error_msg:
            fallback_prefix = (
                "⚠️ **[MODO FALLBACK - QUOTA OPENAI EXCEDIDA]**\n\n"
                "Sua conta OpenAI atingiu limite de uso/créditos. Ajuste billing/limites e tente novamente.\n\n"
            )
        elif "401" in error_msg or "invalid_api_key" in error_msg:
            fallback_prefix = (
                "⚠️ **[MODO FALLBACK - OPENAI NAO AUTENTICOU]**\n\n"
                "A `OPENAI_API_KEY` parece invalida/sem permissao. Verifique a chave e o modelo configurado.\n\n"
            )
        else:
            fallback_prefix = f"⚠️ **[MODO FALLBACK - ERRO OPENAI]**\n\n*Erro: {error_msg}*\n\n"

        logger.warning(f"Falha na OpenAI ({error_msg}). Entrando em modo FALLBACK (Simulação).")
        # Fallback: Tenta extrair a última mensagem do usuário e rodar simulação
        last_user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_msg = m["content"]
                break
        
        return fallback_prefix + run_simulation(last_user_msg)
