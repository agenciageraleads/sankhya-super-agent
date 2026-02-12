"""
Ferramentas MCP do Sankhya Super Agent.
As funções são definidas no escopo global para permitir testes unitários e importação.
"""
import os
import re
import json
import logging
import sqlite3
from typing import Optional, List, Dict, Any
import sys
import importlib
import pkgutil
import inspect
import pandas as pd
import plotly.express as px
import plotly.io as pio

# Adiciona o diretório atual ao path para garantir que utils seja encontrado
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

logger = logging.getLogger("ssa-tools")


# Caminho da knowledge base
KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")

def _env_truthy(name: str) -> bool:
    val = (os.getenv(name) or "").strip().lower()
    return val in {"1", "true", "yes", "y", "on"}

def _parse_csv_env(name: str) -> List[str]:
    raw = os.getenv(name) or ""
    items = [x.strip() for x in raw.split(",")]
    return [x for x in items if x]

def _write_guard_blocked_message(action: str, hint: str = "") -> str:
    extra = f"\n\n{hint}" if hint else ""
    return (
        f"❌ BLOQUEADO: operação de escrita ({action}) desabilitada por padrão.\n\n"
        "Para habilitar, defina `SSA_ENABLE_WRITE=1` e configure uma allowlist apropriada."
        f"{extra}"
    )


# =============================================================================
# VALIDAÇÃO DE SEGURANÇA SQL (CAMADA CRÍTICA)
# =============================================================================

# Palavras-chave DML/DDL que NUNCA devem ser executadas
_FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER",
    "CREATE", "REPLACE", "MERGE", "GRANT", "REVOKE",
    "EXEC", "EXECUTE", "CALL", "BEGIN", "DECLARE",
    "COMMIT", "ROLLBACK", "SAVEPOINT",
]

# Padrão regex para detectar palavras reservadas como tokens isolados
_FORBIDDEN_PATTERN = re.compile(
    r"\b(" + "|".join(_FORBIDDEN_KEYWORDS) + r")\b",
    re.IGNORECASE
)


def _strip_string_literals(sql: str) -> str:
    """Remove conteúdo entre aspas simples para não gerar falsos positivos."""
    return re.sub(r"'[^']*'", "''", sql)

def _normalize_sql_for_gateway(sql: str) -> str:
    """
    Normaliza SQL para execução no DbExplorer:
    - remove espaços extras nas bordas
    - remove ';' apenas quando estiver no final
    """
    cleaned = sql.strip()
    while cleaned.endswith(";"):
        cleaned = cleaned[:-1].rstrip()
    return cleaned


def validate_sql_safety(sql: str) -> Optional[str]:
    """
    Valida se a query SQL é segura para execução (somente leitura).
    """
    cleaned = _normalize_sql_for_gateway(sql)

    # Camada 1: Deve começar com SELECT ou WITH
    upper_start = cleaned.upper().lstrip()
    if not (upper_start.startswith("SELECT") or upper_start.startswith("WITH")):
        return "❌ BLOQUEADO: Apenas queries SELECT (ou WITH...SELECT) são permitidas."

    # Camada 2: Bloquear múltiplos statements via ponto-e-vírgula
    sanitized = _strip_string_literals(cleaned)
    if ";" in sanitized:
        return "❌ BLOQUEADO: Ponto-e-vírgula detectado. Apenas um statement por vez."

    # Camada 3: Bloquear comentários SQL
    if "--" in sanitized or "/*" in sanitized:
        return "❌ BLOQUEADO: Comentários SQL não são permitidos."

    # Camada 4: Buscar palavras-chave DML/DDL proibidas
    match = _FORBIDDEN_PATTERN.search(sanitized)
    if match:
        keyword = match.group(1).upper()
        return f"❌ BLOQUEADO: Comando proibido '{keyword}' detectado na query."

    return None


# =============================================================================
# IMPLEMENTAÇÃO DAS FERRAMENTAS (ESCOPO GLOBAL)
# =============================================================================

def run_sql_select(sql: str) -> str:
    """Executa SELECT com validação de segurança."""
    sql_to_run = _normalize_sql_for_gateway(sql)
    error = validate_sql_safety(sql_to_run)
    if error:
        return error

    try:
        result = sankhya.execute_query(sql_to_run)
        if not result:
            return "A consulta não retornou registros."
        return f"**{len(result)} registro(s) encontrado(s):**\n\n{format_as_markdown_table(result)}"
    except Exception as e:
        return f"❌ Erro ao executar SQL: {str(e)}"


def get_table_columns(table_name: str) -> str:
    """Consulta dicionário de dados (TDICAM ou ALL_TAB_COLUMNS)."""
    clean_name = re.sub(r"[^A-Za-z0-9_]", "", table_name).upper()

    # 1. Tenta TDICAM (Nativo Sankhya)
    sql_tdicam = f"""
    SELECT 
        CAMPO AS "Coluna", 
        DESCRICAO AS "Descricao", 
        TIPO AS "Tipo", 
        TAMANHO AS "Tamanho"
    FROM TDICAM 
    WHERE NOMETAB = '{clean_name}'
    ORDER BY ORDEM
    """
    try:
        result = sankhya.execute_query(sql_tdicam)
        if result:
            return f"**Colunas da tabela `{clean_name}` (TDICAM):**\n\n{format_as_markdown_table(result)}"
    except Exception:
        pass

    # 2. Fallback Oracle
    sql_oracle = f"""
    SELECT 
        COLUMN_NAME AS "Coluna",
        DATA_TYPE AS "Tipo",
        DATA_LENGTH AS "Tamanho",
        NULLABLE AS "Nulo"
    FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = '{clean_name}'
    ORDER BY COLUMN_ID
    """
    try:
        result = sankhya.execute_query(sql_oracle)
        if result:
            return f"**Colunas da tabela `{clean_name}` (Oracle):**\n\n{format_as_markdown_table(result)}"
        return f"Tabela `{clean_name}` não encontrada no dicionário de dados."
    except Exception as e:
        return f"❌ Erro ao consultar dicionário: {str(e)}"


def get_stock_info(codprod: int, codlocal: int = 10010000) -> str:
    """Consulta estoque atual de um produto."""
    sql = f"""
    SELECT
        P.CODPROD,
        P.DESCRPROD AS "Descricao",
        NVL(TRIM(P.MARCA), 'SEM MARCA') AS "Marca",
        P.CODVOL AS "Unidade",
        NVL(E.ESTOQUE, 0) AS "Saldo",
        NVL(C.CUSREP, 0) AS "CustoUnit",
        ROUND(NVL(E.ESTOQUE, 0) * NVL(C.CUSREP, 0), 2) AS "ValorEstoque"
    FROM TGFPRO P
    LEFT JOIN (
        SELECT CODPROD, SUM(ESTOQUE) AS ESTOQUE
        FROM TGFEST
        WHERE CODLOCAL = {int(codlocal)} AND CODEMP = 1
        GROUP BY CODPROD
    ) E ON P.CODPROD = E.CODPROD
    LEFT JOIN (
        SELECT C.CODPROD, C.CUSREP
        FROM TGFCUS C
        WHERE C.CODEMP = 1
          AND C.DHALTER = (SELECT MAX(X.DHALTER) FROM TGFCUS X WHERE X.CODPROD = C.CODPROD AND X.CODEMP = C.CODEMP)
    ) C ON P.CODPROD = C.CODPROD
    WHERE P.CODPROD = {int(codprod)}
    """
    try:
        result = sankhya.execute_query(sql)
        if not result:
            return f"Produto {codprod} não encontrado."
        return f"**Estoque do Produto {codprod}:**\n\n{format_as_markdown_table(result)}"
    except Exception as e:
        return f"❌ Erro ao consultar estoque: {str(e)}"


def get_partner_info(codparc: int) -> str:
    """Busca dados de um parceiro."""
    sql = f"""
    SELECT
        P.CODPARC,
        P.RAZAOSOCIAL AS "RazaoSocial",
        P.NOMEPARC AS "Fantasia",
        P.CGC_CPF AS "CNPJ_CPF",
        P.TIPPESSOA AS "Tipo",
        C.NOMECID AS "Cidade",
        C.UF,
        P.TELEFONE AS "Telefone",
        P.EMAIL
    FROM TGFPAR P
    LEFT JOIN TSICID C ON P.CODCID = C.CODCID
    WHERE P.CODPARC = {int(codparc)}
    """
    try:
        result = sankhya.execute_query(sql)
        if not result:
            return f"Parceiro {codparc} não encontrado."
        return f"**Parceiro {codparc}:**\n\n{format_as_markdown_table(result)}"
    except Exception as e:
        return f"❌ Erro ao consultar parceiro: {str(e)}"


def get_invoice_header(nunota: int) -> str:
    """Busca cabeçalho de nota."""
    sql = f"""
    SELECT
        C.NUNOTA,
        C.NUMNOTA AS "NumNota",
        C.DTNEG AS "DataNeg",
        P.NOMEPARC AS "Parceiro",
        T.DESCROPER AS "TOP",
        C.VLRNOTA AS "ValorTotal",
        C.STATUSNOTA AS "Status",
        C.PENDESSION AS "Pendente",
        U.NOMEUSU AS "Usuario"
    FROM TGFCAB C
    LEFT JOIN TGFPAR P ON C.CODPARC = P.CODPARC
    LEFT JOIN TGFTPV T ON C.CODTIPOPER = T.CODTIPOPER AND C.DHTIPOPER = T.DHALTER
    LEFT JOIN TSIUSU U ON C.CODUSU = U.CODUSU
    WHERE C.NUNOTA = {int(nunota)}
    """
    try:
        result = sankhya.execute_query(sql)
        if not result:
            return f"Nota {nunota} não encontrada."
        return f"**Nota {nunota}:**\n\n{format_as_markdown_table(result)}"
    except Exception as e:
        return f"❌ Erro ao consultar nota: {str(e)}"


def get_invoice_items(nunota: int) -> str:
    """Lista itens de uma nota."""
    sql = f"""
    SELECT
        I.SEQUENCIA AS "Seq",
        I.CODPROD,
        P.DESCRPROD AS "Produto",
        I.QTDNEG AS "Qtd",
        I.VLRUNIT AS "VlrUnit",
        I.VLRTOT AS "VlrTotal",
        I.CODVOL AS "Unidade"
    FROM TGFITE I
    JOIN TGFPRO P ON I.CODPROD = P.CODPROD
    WHERE I.NUNOTA = {int(nunota)}
    ORDER BY I.SEQUENCIA
    """
    try:
        result = sankhya.execute_query(sql)
        if not result:
            return f"Nenhum item encontrado para a nota {nunota}."
        return f"**Itens da Nota {nunota} ({len(result)} itens):**\n\n{format_as_markdown_table(result)}"
    except Exception as e:
        return f"❌ Erro ao consultar itens: {str(e)}"


def search_docs(query: str) -> str:
    """Pesquisa na knowledge base."""
    results = []
    query_lower = query.lower()

    for filename in os.listdir(KNOWLEDGE_DIR):
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        if not os.path.isfile(filepath):
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if query_lower in content.lower():
                lines = content.split("\n")
                snippets = []
                for i, line in enumerate(lines):
                    if query_lower in line.lower():
                        start = max(0, i - 1)
                        end = min(len(lines), i + 3)
                        snippet = "\n".join(lines[start:end])
                        snippets.append(snippet)
                        if len(snippets) >= 3:
                            break
                results.append(f"### 📄 {filename}\n\n" + "\n\n---\n\n".join(snippets))
        except Exception:
            continue

    if not results:
        return f"Nenhum resultado encontrado para '{query}' na base de conhecimento."
    return f"**Resultados para '{query}':**\n\n" + "\n\n".join(results)


def list_tables() -> str:
    """Lista tabelas mapeadas."""
    schema_path = os.path.join(KNOWLEDGE_DIR, "schema_map.json")
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        rows = [{"Tabela": k, "Descricao": v} for k, v in schema.items()]
        return f"**Tabelas do Sankhya ({len(rows)}):**\n\n{format_as_markdown_table(rows)}"
    except Exception as e:
        return f"❌ Erro ao ler schema_map.json: {str(e)}"


def test_connection() -> str:
    """Testa conexão."""
    try:
        result = sankhya.execute_query("SELECT 1 AS TESTE FROM DUAL")
        if result:
            return "✅ Conexão com o Gateway Sankhya estabelecida com sucesso!"
        return "⚠️ Conexão estabelecida, mas o resultado foi vazio."
    except Exception as e:
        return f"❌ Falha na conexão: {str(e)}"


# =============================================================================
# NOVAS FERRAMENTAS UNIVERSAIS (PHASE 2)
# =============================================================================

def get_daily_sales_report(days: int = 7, codemp_csv: str = "") -> str:
    """
    Gera relatório de vendas diárias (TGFCAB) com filtro opcional de empresas.
    Use para pedidos como "vendas de hoje", "relatório diário", "empresa 1 e 5".
    """
    try:
        days = int(days)
    except Exception:
        return "❌ Parâmetro `days` inválido. Informe um número inteiro."

    if days < 1:
        days = 1
    if days > 60:
        days = 60

    where_emp = ""
    scope_text = "Todas as empresas"
    if codemp_csv and codemp_csv.strip():
        cleaned = re.sub(r"[^0-9,]", "", codemp_csv)
        emp_ids = [x for x in cleaned.split(",") if x]
        if not emp_ids:
            return "❌ `codemp_csv` inválido. Exemplo esperado: `1,5`."
        where_emp = f" AND CODEMP IN ({', '.join(emp_ids)})"
        scope_text = f"Empresas: {', '.join(emp_ids)}"

    sql = f"""
    SELECT
        TO_CHAR(TRUNC(DTNEG), 'YYYY-MM-DD') AS "Data",
        CODEMP AS "Empresa",
        COUNT(*) AS "QtdNotas",
        ROUND(SUM(VLRNOTA), 2) AS "TotalVendas"
    FROM TGFCAB
    WHERE STATUSNOTA = 'L'
      AND TIPMOV = 'V'
      AND TRUNC(DTNEG) >= TRUNC(SYSDATE) - {days - 1}
      {where_emp}
    GROUP BY TRUNC(DTNEG), CODEMP
    ORDER BY TRUNC(DTNEG) DESC, CODEMP
    """

    try:
        rows = sankhya.execute_query(sql)
        if not rows:
            return "Nenhuma venda encontrada para o período/filtro informado."

        total = sum(float(r.get("TotalVendas") or 0) for r in rows)
        qtd_notas = sum(int(r.get("QtdNotas") or 0) for r in rows)
        header = (
            f"### 📅 Relatório de Vendas Diárias\n"
            f"- Período: últimos **{days} dia(s)**\n"
            f"- Escopo: **{scope_text}**\n"
            f"- Notas: **{qtd_notas}**\n"
            f"- Total: **R$ {total:,.2f}**\n\n"
        )
        return header + format_as_markdown_table(rows)
    except Exception as e:
        return f"❌ Erro ao gerar relatório diário: {str(e)}"

def call_sankhya_service(service_name: str, request_body: dict) -> str:
    """
    Executa qualquer serviço (Service Name) da API do Sankhya.
    Útil para operações específicas não cobertas por outras ferramentas (ex: faturar nota, cancelar).
    """
    if not _env_truthy("SSA_ENABLE_WRITE"):
        return _write_guard_blocked_message(
            action=f"call_sankhya_service -> {service_name}",
            hint="Se for realmente necessário, permita serviços específicos via `SSA_SERVICE_ALLOWLIST` (CSV).",
        )

    allowed_services = set(_parse_csv_env("SSA_SERVICE_ALLOWLIST"))
    if not allowed_services:
        return _write_guard_blocked_message(
            action=f"call_sankhya_service -> {service_name}",
            hint="Allowlist vazia: defina `SSA_SERVICE_ALLOWLIST=ServiceA,ServiceB` para liberar explicitamente.",
        )
    if service_name not in allowed_services:
        return (
            f"❌ BLOQUEADO: serviço `{service_name}` não está na allowlist.\n\n"
            f"Allowlist atual (`SSA_SERVICE_ALLOWLIST`): {', '.join(sorted(allowed_services))}"
        )

    try:
        result = sankhya.call_service(service_name, request_body)
        return f"✅ Serviço `{service_name}` executado com sucesso:\n\n```json\n{json.dumps(result, indent=2, ensure_ascii=False)}\n```"
    except Exception as e:
        return f"❌ Erro ao executar serviço `{service_name}`: {str(e)}"


def load_records(entity_name: str, criteria: str = "", fields: List[str] = None) -> str:
    """
    Consulta registros de qualquer entidade (Tabela) usando a API de Dados (loadRecords).
    Mais seguro e poderoso que SQL direto, pois aplica formatação e regras de negócio.
    
    Args:
        entity_name: Nome da entidade (ex: 'Parceiro', 'Produto', 'Usuario').
        criteria: Filtro SQL (Where clause), ex: "NOMEPARC LIKE '%SILVA%'".
        fields: Lista de campos a retornar. Se vazio, tenta trazer os principais.
    """
    try:
        # Monta o corpo da requisição loadRecords
        request_body = {
            "dataSet": {
                "rootEntity": entity_name,
                "includePresentationFields": "S",
                "offsetPage": "0",
                "criteria": {
                    "expression": { "$": criteria if criteria else "1=1" }
                },
                "entity": {
                    "fieldset": { "list": ", ".join(fields) if fields else "*" }
                }
            }
        }
        
        # Chama o serviço
        response = sankhya.call_service("CRUDServiceProvider.loadRecords", request_body)
        
        # Processa o retorno para tabela Markdown
        entities = response.get("responseBody", {}).get("entities", {}).get("entity", [])
        if not entities:
            return f"Nenhum registro encontrado para a entidade `{entity_name}` com o critério `{criteria}`."
            
        if isinstance(entities, dict): # Se for apenas 1 registro, a API retorna dict, não list
            entities = [entities]
            
        # Extrai dados planos para a tabela
        rows = []
        for ent in entities:
            row = {}
            # Campos diretos (ficam dentro de 'f0', 'f1' etc ou pelo nome se mapped)
            # A estrutura do loadRecords é complexa, varia conforme fields.
            # Simplificação: Tenta pegar os campos solicitados do retorno
            # O retorno geralmente é { "f0": { "$": "Valor" }, "CAMPO": { "$": "Valor" } }
            for k, v in ent.items():
                if isinstance(v, dict) and "$" in v:
                    row[k] = v["$"]
                else:
                    row[k] = str(v)
            rows.append(row)
            
        return f"**Resultados para `{entity_name}`:**\n\n{format_as_markdown_table(rows)}"
        
    except Exception as e:
        return f"❌ Erro ao consultar `{entity_name}`: {str(e)}"


def save_record(entity_name: str, values: dict, primary_key: dict = None) -> str:
    """
    Insere (INSERT) ou Atualiza (UPDATE) um registro em qualquer entidade.
    
    Args:
        entity_name: Nome da entidade (ex: 'Parceiro', 'Produto').
        values: Dicionário com campos e valores a salvar { "NOMEPARC": "Novo Cliente", ... }.
        primary_key: Dicionário com a PK (se for Update) { "CODPARC": 100 }. Se vazio, é Insert.
    """
    if not _env_truthy("SSA_ENABLE_WRITE"):
        return _write_guard_blocked_message(
            action=f"save_record -> {entity_name}",
            hint="Se for realmente necessário, permita entidades específicas via `SSA_WRITE_ENTITY_ALLOWLIST` (CSV).",
        )

    allowed_entities = set(_parse_csv_env("SSA_WRITE_ENTITY_ALLOWLIST"))
    if not allowed_entities:
        return _write_guard_blocked_message(
            action=f"save_record -> {entity_name}",
            hint="Allowlist vazia: defina `SSA_WRITE_ENTITY_ALLOWLIST=EntidadeA,EntidadeB` para liberar explicitamente.",
        )
    if entity_name not in allowed_entities:
        return (
            f"❌ BLOQUEADO: entidade `{entity_name}` não está na allowlist.\n\n"
            f"Allowlist atual (`SSA_WRITE_ENTITY_ALLOWLIST`): {', '.join(sorted(allowed_entities))}"
        )

    try:
        # Prepara os campos e valores
        # A API DatasetSP.save espera arrays alinhados de fields e values
        fields_list = list(values.keys())
        values_map = {}
        
        # O Sankhya espera values com chaves numéricas strings "0", "1", correspondendo ao índice no fields
        for i, field in enumerate(fields_list):
            values_map[str(i)] = str(values[field])
            
        record = { "values": values_map }
        
        if primary_key:
            record["pk"] = primary_key
            
        request_body = {
            "entityName": entity_name,
            "standAlone": False,
            "fields": fields_list,
            "records": [record]
        }
        
        # Chama o serviço
        san_result = sankhya.call_service("DatasetSP.save", request_body)
        
        # Tenta extrair a PK do registro salvo/criado
        saved_pk = san_result.get("responseBody", {}).get("total", "1") # Fallback
        result_msg = "Registro atualizado" if primary_key else "Registro criado"
        
        return f"✅ {result_msg} com sucesso na entidade `{entity_name}`.\nRetorno: {json.dumps(san_result, indent=2)}"
        
    except Exception as e:
        return f"❌ Erro ao salvar registro em `{entity_name}`: {str(e)}"


def search_solutions(query: str) -> str:
    """
    Busca soluções na Base de Conhecimento Sankhya (artigos oficiais indexados).
    Use isso quando encontrar erros (ex: ORA-xxxxx) ou tiver dúvidas de processo.
    """
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp_server", "knowledge.db")
    if not os.path.exists(db_path):
        return "⚠️ Base de conhecimento ainda não indexada. Execute o script `knowledge_indexer.py` primeiro."
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tenta extrair a mensagem "core" do erro
        clean_query = query.replace("Erro Funcional Sankhya:", "").replace("HttpServiceBroker:", "").replace(":", " ").replace("*", " ").replace('"', " ").strip()
        
        # Estratégia 1: Busca FTS "NEAR" (Palavras próximas) ou Phrase Match
        # Tenta buscar a frase exata primeiro (mais preciso)
        try:
            cursor.execute("""
                SELECT a.title, a.body, a.url 
                FROM articles_fts f 
                JOIN articles a ON a.id = f.rowid 
                WHERE articles_fts MATCH ? 
                ORDER BY f.rank 
                LIMIT 3
            """, (f'"{clean_query}"',))
            rows = cursor.fetchall()
        except:
            rows = []

        # Estratégia 2: Busca FTS "AND" (Todas as palavras presentes, qualquer ordem)
        if not rows:
            # Pega as 5 maiores palavras para montar a query
            words = [w for w in clean_query.split() if len(w) > 4]
            if words:
                fts_query = " AND ".join(words[:5])
                try:
                    cursor.execute("""
                        SELECT a.title, a.body, a.url 
                        FROM articles_fts f 
                        JOIN articles a ON a.id = f.rowid 
                        WHERE articles_fts MATCH ? 
                        ORDER BY f.rank 
                        LIMIT 3
                    """, (fts_query,))
                    rows = cursor.fetchall()
                except:
                    pass

        # Estratégia 3: Fallback LIKE (Palavras-chave isoladas - OR)
        if not rows:
            # Pega palavras com mais de 3 letras (aceita 'Erro', 'Nota', 'Série')
            keywords = [w for w in clean_query.split() if len(w) > 3]
            if keywords:
                # Tenta match com qualquer palavra-chave no título OU corpo (limitado a 3 termos para performance)
                like_clauses = []
                for kw in keywords[:3]:
                    like_clauses.append(f"title LIKE '%{kw}%'")
                    like_clauses.append(f"body LIKE '%{kw}%'") # Também busca no corpo para aumentar recall
                
                like_query = " OR ".join(like_clauses)
                
                cursor.execute(f"""
                    SELECT title, body, url 
                    FROM articles 
                    WHERE {like_query}
                    LIMIT 3
                """)
                rows = cursor.fetchall()

        conn.close()
        
        if not rows:
            return f"Nenhuma solução encontrada na base de conhecimento para: '{clean_query}'"
            
        results = []
        for title, body, url in rows:
            # Resume o corpo (primeiros 300 chars)
            snippet = body[:300] + "..." if len(body) > 300 else body
            results.append(f"### 📄 [{title}]({url})\n{snippet}\n\n[Ler artigo completo]({url})")
            
        return f"**Soluções Encontradas para '{clean_query}':**\n\n" + "\n\n---\n\n".join(results)
        
    except Exception as e:
        return f"❌ Erro ao buscar na Knowledge Base: {str(e)}"


def describe_entity(entity_name: str) -> str:
    """Lista os campos disponíveis em uma entidade (Dicionário de Dados)."""
    return get_table_columns(entity_name) # Reutiliza a função existente que já consulta TDICAM


# =============================================================================
# REGISTRO NO FAST MCP
# =============================================================================

# Registro centralizado de ferramentas para uso por diversos clientes (MCP, OpenAI, Streamlit)
GLOBAL_TOOL_REGISTRY = {}

def generate_chart_report(sql: str, chart_type: str = "bar", title: str = "Relatório SSA") -> str:
    """
    Gera um gráfico visual (BI) baseado em uma consulta SQL.
    Tipos suportados: 'bar', 'line', 'pie', 'scatter'.
    """
    sql_to_run = _normalize_sql_for_gateway(sql)
    error = validate_sql_safety(sql_to_run)
    if error: return error

    try:
        data = sankhya.execute_query(sql_to_run)
        if not data:
            return "A consulta não retornou dados para gerar o gráfico."
        
        df = pd.DataFrame(data)
        
        # Tenta identificar colunas numéricas e categóricas
        cols = df.columns.tolist()
        if not cols: return "Erro: Estrutura de dados inválida."
        
        x_col = cols[0]
        y_col = cols[1] if len(cols) > 1 else cols[0]
        
        if chart_type == "bar":
            fig = px.bar(df, x=x_col, y=y_col, title=title)
        elif chart_type == "line":
            fig = px.line(df, x=x_col, y=y_col, title=title)
        elif chart_type == "pie":
            fig = px.pie(df, names=x_col, values=y_col, title=title)
        else:
            fig = px.scatter(df, x=x_col, y=y_col, title=title)
            
        chart_json = pio.to_json(fig)
        return f"Gerando gráfico {chart_type} para seu pedido:\n\n```plotly\n{chart_json}\n```"
    except Exception as e:
        return f"Erro ao gerar gráfico: {str(e)}"

def register_tools(mcp=None):
    """
    Registra as ferramentas globais e skills dinâmicas.
    Se mcp for fornecido, registra no servidor FastMCP.
    Popula o GLOBAL_TOOL_REGISTRY.
    """
    global GLOBAL_TOOL_REGISTRY
    GLOBAL_TOOL_REGISTRY.clear() # Limpa o dicionário mantendo a mesma referência de objeto

    # 1. Ferramentas Core (Estáticas)
    core_tools = [
        run_sql_select, get_table_columns, get_stock_info, get_partner_info,
        get_invoice_header, get_invoice_items, search_docs, list_tables,
        test_connection, call_sankhya_service, load_records, save_record,
        search_solutions, describe_entity, generate_chart_report,
        get_daily_sales_report
    ]
    for tool_func in core_tools:
        GLOBAL_TOOL_REGISTRY[tool_func.__name__] = tool_func
        if mcp:
            mcp.tool()(tool_func)

    # 2. Carregamento Dinâmico de Skills
    skills_path = os.path.join(os.path.dirname(__file__), "skills")
    if not os.path.exists(skills_path):
        return

    if skills_path not in sys.path:
        sys.path.insert(0, skills_path)

    for loader, module_name, is_pkg in pkgutil.iter_modules([skills_path]):
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module)
            
            for name, func in inspect.getmembers(module, inspect.isfunction):
                # Só expõe funções definidas no próprio módulo da skill.
                if func.__module__ != module.__name__:
                    continue
                if not name.startswith("_") and func.__doc__:
                    #print(f"DEBUG: Registrando {name} de {module_name}")
                    GLOBAL_TOOL_REGISTRY[name] = func
                    if mcp:
                        mcp.tool()(func)
        except Exception as e:
            logger.error(f"Erro ao carregar skill {module_name}: {str(e)}")

def get_gemini_tools_schema() -> List[Dict]:
    """Gera declarações de função no formato Gemini baseado nas ferramentas registradas."""
    declarations = []
    for name, func in GLOBAL_TOOL_REGISTRY.items():
        # Gera schema baseado na assinatura e docstring
        sig = inspect.signature(func)
        params = {
            "type": "object",
            "properties": {},
            "required": []
        }

        for p_name, p_param in sig.parameters.items():
            # Inferência de tipo baseada na annotation ou convenção de nome
            p_type = "string"
            if p_param.annotation == int or p_name.startswith("cod") or p_name.startswith("nu"):
                p_type = "integer"
            elif p_param.annotation == List[str] or p_param.annotation == list:
                p_type = "array"

            prop_schema = {
                "type": p_type,
                "description": f"Parâmetro {p_name}"
            }
            # Gemini também exige "items" quando o tipo é array.
            if p_type == "array":
                prop_schema["items"] = {"type": "string"}

            params["properties"][p_name] = prop_schema
            if p_param.default == inspect.Parameter.empty:
                params["required"].append(p_name)

        declarations.append({
            "name": name,
            "description": (func.__doc__ or "Sem descrição").strip().split("\n")[0],
            "parameters": params
        })
    return declarations
