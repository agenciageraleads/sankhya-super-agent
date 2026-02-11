import logging
import os
import re
import ast
from typing import List, Dict, Any, Optional

try:
    from utils import sankhya
except ImportError:
    from mcp_server.utils import sankhya

logger = logging.getLogger("skill-orchestrator")

# Configurações de Segurança para Geração de Código
ALLOWED_MODULES = {"logging", "utils", "mcp_server", "math", "statistics", "typing", "re", "json"}
FORBIDDEN_FUNCTIONS = {"eval", "exec", "open", "breakpoint"}

def _validate_generated_code(code: str) -> Optional[str]:
    """
    Realiza uma análise estática (AST) no código gerado para garantir segurança.
    Retorna None se for seguro, ou uma mensagem de erro se detectar algo suspeito.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Erro de sintaxe no código gerado: {str(e)}"

    for node in ast.walk(tree):
        # 1. Validar Imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = []
            if isinstance(node, ast.Import):
                modules = [n.name.split('.')[0] for n in node.names]
            else:
                if node.module:
                    modules = [node.module.split('.')[0]]
            
            for mod in modules:
                if mod not in ALLOWED_MODULES:
                    return f"❌ SEGURANÇA: O módulo '{mod}' não é permitido em agentes automáticos."

        # 2. Validar Funções Perigosas
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_FUNCTIONS:
                    return f"❌ SEGURANÇA: A função '{node.func.id}' é proibida por motivos de segurança."
            elif isinstance(node.func, ast.Attribute):
                # Bloqueia acesso a dunder methods perigosos ou atributos do sistema
                if node.func.attr.startswith("__") or node.func.attr in {"system", "popen", "remove", "rmdir"}:
                    return f"❌ SEGURANÇA: Chamada de atributo suspeito detectada: {node.func.attr}"

    return None

def create_agent_skill(description: str) -> str:
    """
    Cria uma nova agente (skill) especializada. 
    Detecta intenção de IDs (codprod, nunota) para gerar ferramentas de diagnóstico.
    """
    logger.info(f"Iniciando criação de agente para: {description}")
    
    # 1. Extração de Metadados da Descrição
    keywords = [w.upper() for w in description.split() if len(w) > 3]
    ids = re.findall(r'\b\d{4,}\b', description) # Detecta números com 4+ dígitos (IDs)
    
    if not keywords:
        return "⚠️ Descrição muito curta para identificar o propósito do agente."
        
    # 2. Descoberta de Tabelas
    like_clauses = " OR ".join([f"UPPER(DESCRTAB) LIKE '%{kw}%' OR NOMETAB LIKE '%{kw}%'" for kw in keywords[:3]])
    sql_discovery = f"SELECT NOMETAB, DESCRTAB FROM TDDTAB WHERE ({like_clauses}) AND ROWNUM <= 5"
    
    try:
        tables = sankhya.execute_query(sql_discovery)
        if not tables:
            # Fallback se não achar nada: procura tabelas core se houver palavras como 'produto' ou 'nota'
            if "PROD" in description.upper():
                tables = [{"NOMETAB": "TGFPRO", "DESCRTAB": "Produtos"}]
            elif "NOTA" in description.upper() or "LANC" in description.upper():
                tables = [{"NOMETAB": "TGFCAB", "DESCRTAB": "Cabeçalho de Notas"}]
            else:
                return f"❌ Não identifiquei tabelas para '{description}'. Tente ser mais específico (mencione 'produto', 'nota', 'estoque')."
            
        target_table = tables[0]['NOMETAB']
        agent_name = target_table.lower().replace(" ", "_")
        if "PROD" in description.upper() or "MATERIA" in description.upper():
             agent_name = "production_impact"
             
        file_path = os.path.join(os.path.dirname(__file__), f"{agent_name}_helper.py")
        
        # 3. Inteligência de Geração de Código (Advanced)
        id_list = ", ".join(ids) if ids else "0"
        desc_upper = description.upper()
        
        if any(x in desc_upper for x in ["MATERIA", "MATÉRIA", "COMPOSI", "COMPOSIÇ"]):
            # Código especializado para análise de duplicidade e impacto em produção
            code = f'''"""
Agente Especialista em Impacto de Produção e Duplicidade
Gerado para: {description}
"""
import logging
try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

logger = logging.getLogger("skill-production-impact")

def diagnose_{agent_name}_issue(limit: int = 10) -> str:
    """Analisa duplicidade de produtos e seu impacto em fórmulas de produção e estoque."""
    pids = [{id_list}]
    if not pids or pids == [0]: return "⚠️ Nenhum ID de produto fornecido para análise."
    
    ids_str = ", ".join(map(str, pids))
    
    # 1. Dados Básicos e Cadastro
    sql_cad = f"SELECT CODPROD, DESCRPROD, MARCA, ATIVO FROM TGFPRO WHERE CODPROD IN ({{ids_str}})"
    cadastro = sankhya.execute_query(sql_cad)
    
    # 2. Uso em Fórmulas de Produção (TGFICP)
    sql_prod = f"""
    SELECT I.CODMATPRIMA as CODPROD, P.DESCRPROD as PROD_FINAL, I.QTDMISTURA, I.CODPROD as COD_PAI
    FROM TGFICP I
    JOIN TGFPRO P ON I.CODPROD = P.CODPROD
    WHERE I.CODMATPRIMA IN ({{ids_str}})
    """
    producao = sankhya.execute_query(sql_prod)
    
    # 3. Saldo de Estoque
    sql_est = f"SELECT CODPROD, SUM(ESTOQUE - RESERVADO) as SALDO_DISPONIVEL FROM TGFEST WHERE CODPROD IN ({{ids_str}}) GROUP BY CODPROD"
    estoque = sankhya.execute_query(sql_est)
    
    res = f"### 🏭 Relatório de Impacto de Produção e Duplicidade\\n\\n"
    res += "**1. Cadastro dos Produtos:**\\n" + format_as_markdown_table(cadastro)
    
    if producao:
        res += "\\n\\n**⚠️ Vínculos em Fórmulas de Produção (Onde é usado):**\\n" + format_as_markdown_table(producao)
    else:
        res += "\\n\\n✅ **Nenhum vínculo em fórmulas de produção encontrado para estes códigos.**"
        
    res += "\\n\\n**📦 Posição de Estoque:**\\n" + format_as_markdown_table(estoque)
    
    res += "\\n\\n---\\n### 💡 Plano de Ação para Unificação:\\n"
    res += "1. **Escolha o 'Pai':** Identifique qual dos códigos tem o cadastro mais completo ou maior giro.\\n"
    res += "2. **Transfira o Estoque:** Use uma nota de 'Transferência entre Produtos' (Geralmente TOP 800 ou similar) para mover o saldo dos secundários para o principal.\\n"
    if producao:
        res += "3. **Atualize as Fórmulas:** Você precisará alterar manualmente os registros na tela 'Composição de Produto' (TGFICP) trocando os códigos secundários pelo principal.\\n"
    res += "4. **Inative os Duplicados:** Após transferir saldo e atualizar fórmulas, mude o campo 'Ativo' para 'Não' nos códigos que serão descartados subtitua-os pelo principal em compras futuras."
    
    return res
'''
        else:
            # Fallback para query genérica inteligente
            filter_logic = f"WHERE ROWNUM <= {{limit}}"
            if ids:
                id_list = ", ".join(ids)
                id_col = "CODPROD" if "PRO" in target_table or "EST" in target_table else "NUNOTA"
                filter_logic = f"WHERE {id_col} IN ({id_list})"

            code = f'''
import logging
try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

def diagnose_{agent_name}_issue(limit: int = 10) -> str:
    """Diagnóstico genérico de {target_table}."""
    sql = "SELECT * FROM {target_table} {filter_logic}"
    return format_as_markdown_table(sankhya.execute_query(sql))
'''
        # 4. Validação e Escrita
        security_error = _validate_generated_code(code)
        if security_error: return security_error

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        return f"✅ **Agente de Diagnóstico `{agent_name}` criado!**\n\n" + \
               f"**Foco:** Analisar {target_table} para os IDs {', '.join(ids) if ids else 'recentes'}.\n" + \
               f"Use a ferramenta `diagnose_{agent_name}_issue` para ver o relatório."
               
    except Exception as e:
        return f"❌ Erro na orquestração: {str(e)}"
