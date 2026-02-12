import os
import json
import logging
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

from mcp_server.tools import register_tools, GLOBAL_TOOL_REGISTRY, get_gemini_tools_schema

# Inicializa o registro de ferramentas (incluindo skills dinâmicas)
register_tools()

load_dotenv(override=True)
logger = logging.getLogger("ssa-client")

# Configuração do Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# Modelo a ser utilizado nas chamadas ao Gemini
GEMINI_MODEL = "gemini-2.0-flash"


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
    """Gera o prompt do sistema enriquecido com knowledge base e protocolo de resiliência."""
    tools_list = "\n".join([f"- `{name}`: {func.__doc__.strip().split('\\n')[0] if func.__doc__ else 'Sem descrição'}" 
                             for name, func in GLOBAL_TOOL_REGISTRY.items()])
    
    return f"""
Você é o Sankhya Super Agent (SSA), o assistente MAIS INTELIGENTE e PROATIVO do ERP Sankhya.
Você serve a empresa "Portal Distribuidora / B&B". Seus usuários são diretores, gerentes e suporte.

═══════════════════════════════════════════
 PERSONALIDADE: RESOLVA, NÃO PERGUNTE
═══════════════════════════════════════════

Você é um RESOLVEDOR DE PROBLEMAS, não um robô passivo. Siga estas regras:

1. **AÇÃO PRIMEIRO:** Quando o usuário pedir algo, FAÇA. Não peça confirmação.
   - ❌ "De qual local você deseja o saldo?" → NÃO FAÇA ISSO. Use o padrão (CODLOCAL=10010000, CODEMP=1).
   - ✅ Execute direto e retorne os dados. Se houver múltiplos locais, retorne TODOS.
   - ❌ "Qual coluna deseja?" → NÃO FAÇA ISSO. Use `get_table_columns` para descobrir.
   - ✅ Consulte o dicionário de dados e monte a query correta.

2. **NUNCA INVENTE NOMES DE COLUNAS.** Se não souber a coluna exata:
   - Use `get_table_columns(table_name)` ANTES de escrever SQL customizado.
   - Ou use as ferramentas dedicadas (`get_stock_info`, `get_partner_info`, etc.) que já sabem os campos.

3. **PREFIRA FERRAMENTAS DEDICADAS** antes de SQL livre:
   - Estoque? → `get_stock_info(codprod)` (já inclui saldo, custo, marca)
   - Parceiro? → `get_partner_info(codparc)`
   - Nota? → `get_invoice_header(nunota)` + `get_invoice_items(nunota)`
   - Vendas? → `get_daily_sales_report(days, codemp_csv)`
   - Só use `run_sql_select` quando NÃO existir ferramenta dedicada.

4. **RESPOSTAS RICAS e ANALÍTICAS:** Não devolva dados crus. Interprete:
   - "O produto X tem saldo zero — pode indicar ruptura de estoque."
   - "As vendas caíram 15% comparado à semana anterior."
   - Ofereça INSIGHTS, não apenas tabelas.

═══════════════════════════════════════════
 PROTOCOLO DE RESILIÊNCIA (OODA LOOP)
═══════════════════════════════════════════

Quando receber um ERRO (ORA-xxxxx, HTTP 400/500, campo inválido), NUNCA desista:

1. **OBSERVAR:** Capture o código de erro exato (ex: ORA-00904).
2. **ORIENTAR:** Use `search_solutions(mensagem_do_erro)` para buscar na knowledge base.
3. **DECIDIR:** Se a solução for clara, aplique. Se precisar de info, pergunte citando o artigo.
4. **AGIR:** Corrija e re-execute. Só escale se após 2 tentativas não resolver.

Erros comuns que você DEVE resolver sozinho:
- `ORA-00904 (coluna inválida)` → Use `get_table_columns` para ver colunas reais e re-montar a query.
- `ponto-e-vírgula detectado` → Remova `;` e re-execute.
- `CURDATE/DATE_TRUNC` → Substitua por `TRUNC(SYSDATE)`, `SYSDATE`, `TO_CHAR` (Oracle).

═══════════════════════════════════════════
 CONHECIMENTO DO SCHEMA SANKHYA
═══════════════════════════════════════════

Parâmetros padrão da instância:
- CODEMP = 1 (empresa padrão)
- CODLOCAL = 10010000 (depósito principal)
- TOP_ENTRADA = 221 | TOP_SAIDA = 1221

Tabelas principais (Oracle — NUNCA use sintaxe MySQL):
- TGFCAB: Cabeçalho de notas (NUNOTA, NUMNOTA, DTNEG, VLRNOTA, CODPARC, STATUSNOTA, TIPMOV, CODEMP)
- TGFITE: Itens de notas (NUNOTA, SEQUENCIA, CODPROD, QTDNEG, VLRUNIT, VLRTOT)
- TGFPRO: Produtos (CODPROD, DESCRPROD, MARCA, CODVOL, ATIVO, USOPROD, CODGRUPOPROD)
- TGFEST: Estoque (CODPROD, CODLOCAL, CODEMP, ESTOQUE, CONTROLE)
- TGFCUS: Custos (CODPROD, CODEMP, CUSREP, DHALTER)
- TGFPAR: Parceiros (CODPARC, RAZAOSOCIAL, NOMEPARC, CGC_CPF, TIPPESSOA, CODCID, TELEFONE, EMAIL)
- TGFTPV: Tipo de Operação/TOP (CODTIPOPER, DESCROPER, DHALTER)
- TGFMBC: Conciliação bancária
- TSIUSU: Usuários (CODUSU, NOMEUSU)
- TSICID: Cidades (CODCID, NOMECID, UF)

Funções SQL Oracle permitidas:
- Data: SYSDATE, TRUNC(SYSDATE), TO_CHAR(data, 'formato'), ADD_MONTHS, MONTHS_BETWEEN
- Texto: NVL, TRIM, UPPER, LOWER, SUBSTR, INSTR
- Agregação: SUM, COUNT, AVG, MAX, MIN, ROUND
- ⛔ NUNCA use: CURDATE, DATE_TRUNC, NOW(), ISNULL, GETDATE (são MySQL/Postgres/SQLServer!)

Regras de negócio:
- CUSREP (custo de reposição) vem de TGFCUS, não de TGFEST.
- Coluna de estoque na TGFEST é "ESTOQUE" (não SALDOATU, não QTDESTOQUE).
- STATUSNOTA: 'L' (liberada), 'P' (pendente), 'C' (cancelada).
- TIPMOV: 'V' (venda), 'C' (compra), 'D' (devolução).

═══════════════════════════════════════════
 SEGURANÇA
═══════════════════════════════════════════

- JAMAIS execute UPDATE, DELETE, INSERT ou DROP via SQL. Use serviços de negócio.
- Operações de escrita são bloqueadas por padrão. Se pedirem, explique a restrição.
- Nunca finalize SQL com `;`. Apenas um statement por chamada.
- Nunca use comentários SQL (`--` ou `/* */`).

═══════════════════════════════════════════
 FERRAMENTAS ATIVAS ({len(GLOBAL_TOOL_REGISTRY)})
═══════════════════════════════════════════

{tools_list}
"""

# Schemas dinâmicos para o Gemini
def get_tools_schema():
    return get_gemini_tools_schema()

# Mapa de execução gerado dinamicamente
def get_available_functions():
    return GLOBAL_TOOL_REGISTRY


def _convert_messages_to_gemini(messages: list) -> list:
    """
    Converte mensagens no formato OpenAI (dicts com role/content) para
    o formato Gemini (types.Content com parts).
    """
    contents = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        # Gemini só aceita 'user' e 'model' como roles
        if role == "assistant":
            role = "model"
        elif role == "system":
            # system_instruction é enviado separadamente na config
            continue
        elif role == "tool":
            # Respostas de ferramentas não devem aparecer como mensagens normais
            continue
        elif role not in ("user", "model"):
            role = "user"

        if not content:
            continue

        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=content)]
            )
        )
    return contents


def run_simulation(last_message: str):
    """
    Modo SIMULAÇÃO (Sem Gemini):
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
    Se não tiver cliente Gemini configurado, usa o modo SIMULAÇÃO.
    """
    # Se não tem API Key, roda simulação local
    if not client:
        # Garante hot-reload das skills mesmo sem Gemini.
        register_tools()
        # Pega a última mensagem do usuário na lista
        for m in reversed(messages):
            if m["role"] == "user":
                last_msg = m["content"]
                break
        else:
            last_msg = ""
            
        return f"**[MODO SIMULAÇÃO - SEM GEMINI KEY]**\n\n" + str(run_simulation(last_msg))

    # Fluxo Gemini Real
    try:
        # Hot-reload real: sempre reindexa ferramentas/skills antes de cada rodada.
        register_tools()
        # Pede os schemas e mapas atuais (suporta Hot Reload)
        system_prompt = get_system_prompt()
        tools_schema = get_tools_schema()
        available_functions = get_available_functions()

        # Configura as ferramentas no formato Gemini
        gemini_tools = types.Tool(function_declarations=tools_schema)
        config = types.GenerateContentConfig(
            tools=[gemini_tools],
            system_instruction=system_prompt,
        )

        # Converte mensagens para o formato Gemini
        contents = _convert_messages_to_gemini(messages)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )
        
        # Loop multi-turn de tool calling (OODA loop).
        # Permite ao modelo chamar ferramentas várias vezes em sequência,
        # corrigindo erros e investigando schemas antes de responder.
        MAX_TOOL_ROUNDS = 5
        for _round in range(MAX_TOOL_ROUNDS):
            # Verifica se o modelo solicitou chamada de ferramentas
            response_parts = response.candidates[0].content.parts
            function_calls = [p for p in response_parts if p.function_call and p.function_call.name]

            if not function_calls:
                # Sem tool call — resposta final de texto
                break

            # Adiciona a resposta do modelo (com os function_calls) ao histórico
            contents.append(response.candidates[0].content)

            # Processa cada chamada de ferramenta
            function_response_parts = []
            for fc_part in function_calls:
                function_name = fc_part.function_call.name
                function_args = dict(fc_part.function_call.args) if fc_part.function_call.args else {}
                
                tool_function = available_functions.get(function_name)
                if not tool_function:
                    function_response_parts.append(
                        types.Part.from_function_response(
                            name=function_name,
                            response={"error": f"Ferramenta '{function_name}' não encontrada."},
                        )
                    )
                    continue
                
                print(f"🛠️ Executando [{_round+1}/{MAX_TOOL_ROUNDS}]: {function_name}({function_args})")
                
                try:
                    function_response = tool_function(**function_args)
                except Exception as e:
                    function_response = f"Erro na execução da ferramenta: {str(e)}"

                # Se der erro recuperável, tenta corrigir e reexecutar
                function_response = _retry_tool_if_recoverable(
                    function_name=function_name,
                    function_args=function_args,
                    function_response=str(function_response),
                    tool_function=tool_function,
                )

                # Aprendizado automático pós-execução de ferramenta
                _run_auto_learning(function_name, function_args, str(function_response), available_functions)

                function_response_parts.append(
                    types.Part.from_function_response(
                        name=function_name,
                        response={"result": str(function_response)},
                    )
                )

            # Envia resultados das ferramentas de volta ao modelo
            contents.append(types.Content(role="user", parts=function_response_parts))

            # O modelo pode decidir chamar MAIS ferramentas (OODA loop) ou gerar resposta final
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=config,
            )

        # Sem chamada de ferramenta — retorna texto direto
        return response.text

    except Exception as e:
        error_msg = str(e)

        # Mensagens mais acionáveis no UI quando o Gemini falha.
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            fallback_prefix = (
                "⚠️ **[MODO FALLBACK - QUOTA GEMINI EXCEDIDA]**\n\n"
                "Sua API Key Gemini atingiu o limite de uso. Verifique billing/limites e tente novamente.\n\n"
            )
        elif "401" in error_msg or "403" in error_msg or "API_KEY_INVALID" in error_msg:
            fallback_prefix = (
                "⚠️ **[MODO FALLBACK - GEMINI NAO AUTENTICOU]**\n\n"
                "A `GEMINI_API_KEY` parece inválida ou sem permissão. Verifique a chave configurada.\n\n"
            )
        else:
            fallback_prefix = f"⚠️ **[MODO FALLBACK - ERRO GEMINI]**\n\n*Erro: {error_msg}*\n\n"

        logger.warning(f"Falha no Gemini ({error_msg}). Entrando em modo FALLBACK (Simulação).")
        # Fallback: Tenta extrair a última mensagem do usuário e rodar simulação
        last_user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_msg = m["content"]
                break
        
        return fallback_prefix + run_simulation(last_user_msg)
