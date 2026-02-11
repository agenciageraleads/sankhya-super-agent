import ast
import datetime as dt
import json
import logging
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

try:
    from utils import sankhya
except ImportError:
    from mcp_server.utils import sankhya

logger = logging.getLogger("skill-orchestrator")


ALLOWED_MODULES = {"logging", "utils", "mcp_server", "math", "statistics", "typing", "re", "json"}
FORBIDDEN_FUNCTIONS = {"eval", "exec", "open", "breakpoint"}

SKILLS_DIR = os.path.dirname(__file__)
FACTORY_DIR = os.path.join(SKILLS_DIR, "_factory")
PROPOSALS_DIR = os.path.join(FACTORY_DIR, "proposals")
BACKUPS_DIR = os.path.join(FACTORY_DIR, "backups")


def _ensure_factory_dirs() -> None:
    os.makedirs(PROPOSALS_DIR, exist_ok=True)
    os.makedirs(BACKUPS_DIR, exist_ok=True)


def _validate_generated_code(code: str) -> Optional[str]:
    """
    Valida o código gerado por AST para bloquear imports e chamadas perigosas.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Erro de sintaxe no código gerado: {str(e)}"

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules: List[str] = []
            if isinstance(node, ast.Import):
                modules = [n.name.split(".")[0] for n in node.names]
            elif node.module:
                modules = [node.module.split(".")[0]]
            for mod in modules:
                if mod not in ALLOWED_MODULES:
                    return f"❌ SEGURANÇA: O módulo '{mod}' não é permitido em agentes automáticos."

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_FUNCTIONS:
                return f"❌ SEGURANÇA: A função '{node.func.id}' é proibida por motivos de segurança."
            if isinstance(node.func, ast.Attribute):
                if node.func.attr.startswith("__") or node.func.attr in {"system", "popen", "remove", "rmdir"}:
                    return f"❌ SEGURANÇA: Chamada de atributo suspeito detectada: {node.func.attr}"

    return None


def _discover_target_table(description: str, keywords: List[str]) -> Optional[str]:
    like_clauses = " OR ".join(
        [f"UPPER(DESCRTAB) LIKE '%{kw}%' OR NOMETAB LIKE '%{kw}%'" for kw in keywords[:3]]
    )
    sql_discovery = f"SELECT NOMETAB, DESCRTAB FROM TDDTAB WHERE ({like_clauses}) AND ROWNUM <= 5"
    try:
        tables = sankhya.execute_query(sql_discovery)
        if tables:
            return tables[0].get("NOMETAB")
    except Exception:
        pass

    desc_upper = description.upper()
    if "PROD" in desc_upper:
        return "TGFPRO"
    if "NOTA" in desc_upper or "LANC" in desc_upper:
        return "TGFCAB"
    return None


def _derive_agent_name(description: str, target_table: str) -> str:
    desc_upper = description.upper()
    if any(x in desc_upper for x in ["MATERIA", "MATÉRIA", "COMPOSI", "COMPOSIÇ"]):
        return "production_impact"
    return re.sub(r"[^a-z0-9_]+", "_", target_table.lower()).strip("_")


def _build_skill_code(description: str, target_table: str, agent_name: str, ids: List[str]) -> Tuple[str, str]:
    ids_expr = ", ".join(ids) if ids else "0"
    desc_upper = description.upper()
    fn_name = f"diagnose_{agent_name}_issue"

    if any(x in desc_upper for x in ["MATERIA", "MATÉRIA", "COMPOSI", "COMPOSIÇ"]):
        code = f'''"""
Agente Especialista em Impacto de Producao e Duplicidade
Gerado para: {description}
"""
import logging
try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

logger = logging.getLogger("skill-production-impact")

def {fn_name}(limit: int = 10) -> str:
    """Analisa duplicidade de produtos e seu impacto em formulas de producao e estoque."""
    pids = [{ids_expr}]
    if not pids or pids == [0]:
        return "⚠️ Nenhum ID de produto fornecido para analise."

    ids_str = ", ".join(map(str, pids))
    sql_cad = f"SELECT CODPROD, DESCRPROD, MARCA, ATIVO FROM TGFPRO WHERE CODPROD IN ({{ids_str}})"
    cadastro = sankhya.execute_query(sql_cad)

    sql_prod = f"""
    SELECT I.CODMATPRIMA as CODPROD, P.DESCRPROD as PROD_FINAL, I.QTDMISTURA, I.CODPROD as COD_PAI
    FROM TGFICP I
    JOIN TGFPRO P ON I.CODPROD = P.CODPROD
    WHERE I.CODMATPRIMA IN ({{ids_str}})
    """
    producao = sankhya.execute_query(sql_prod)

    sql_est = f"SELECT CODPROD, SUM(ESTOQUE - RESERVADO) as SALDO_DISPONIVEL FROM TGFEST WHERE CODPROD IN ({{ids_str}}) GROUP BY CODPROD"
    estoque = sankhya.execute_query(sql_est)

    res = "### Relatorio de Impacto de Producao e Duplicidade\\n\\n"
    res += "**1. Cadastro dos Produtos:**\\n" + format_as_markdown_table(cadastro)
    if producao:
        res += "\\n\\n**Vinculos em Formulas de Producao:**\\n" + format_as_markdown_table(producao)
    else:
        res += "\\n\\nNenhum vinculo em formulas de producao encontrado."
    res += "\\n\\n**Posicao de Estoque:**\\n" + format_as_markdown_table(estoque)
    return res
'''
        return fn_name, code

    filter_logic = "WHERE ROWNUM <= {limit}"
    if ids:
        id_col = "CODPROD" if "PRO" in target_table or "EST" in target_table else "NUNOTA"
        filter_logic = f"WHERE {id_col} IN ({', '.join(ids)})"

    code = f'''"""
Agente de diagnostico automatico para {target_table}
Gerado para: {description}
"""
try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

def {fn_name}(limit: int = 10) -> str:
    """Diagnostico generico para {target_table}."""
    sql = "SELECT * FROM {target_table} {filter_logic}"
    return format_as_markdown_table(sankhya.execute_query(sql))
'''
    return fn_name, code


def _proposal_paths(proposal_id: str) -> Tuple[str, str]:
    return (
        os.path.join(PROPOSALS_DIR, f"{proposal_id}.json"),
        os.path.join(PROPOSALS_DIR, f"{proposal_id}.py"),
    )


def _write_proposal(proposal: Dict[str, Any], code: str) -> None:
    meta_path, code_path = _proposal_paths(proposal["proposal_id"])
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(proposal, f, indent=2, ensure_ascii=False)
    with open(code_path, "w", encoding="utf-8") as f:
        f.write(code)


def _read_proposal(proposal_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    meta_path, code_path = _proposal_paths(proposal_id)
    if not os.path.exists(meta_path) or not os.path.exists(code_path):
        return None, None
    with open(meta_path, "r", encoding="utf-8") as f:
        proposal = json.load(f)
    with open(code_path, "r", encoding="utf-8") as f:
        code = f.read()
    return proposal, code


def _snapshot_existing(skill_filename: str, proposal_id: str) -> Optional[str]:
    target_path = os.path.join(SKILLS_DIR, skill_filename)
    if not os.path.exists(target_path):
        return None
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{skill_filename}.{ts}.{proposal_id}.bak"
    backup_path = os.path.join(BACKUPS_DIR, backup_name)
    shutil.copy2(target_path, backup_path)
    return backup_path


def _latest_backup(skill_filename: str) -> Optional[str]:
    if not os.path.exists(BACKUPS_DIR):
        return None
    matches = [
        os.path.join(BACKUPS_DIR, f)
        for f in os.listdir(BACKUPS_DIR)
        if f.startswith(skill_filename + ".") and f.endswith(".bak")
    ]
    if not matches:
        return None
    matches.sort()
    return matches[-1]


def propose_tool(description: str) -> str:
    """
    Etapa 1 - Propoe uma nova tool/skill sem publicar.
    Gera codigo + metadata em mcp_server/skills/_factory/proposals.
    """
    _ensure_factory_dirs()
    keywords = [w.upper() for w in re.findall(r"[A-Za-zÀ-ÿ0-9_]+", description) if len(w) > 3]
    ids = re.findall(r"\b\d{4,}\b", description)

    if not keywords:
        return "⚠️ Descrição muito curta para identificar o propósito da tool."

    target_table = _discover_target_table(description, keywords)
    if not target_table:
        return "❌ Não identifiquei tabela alvo. Tente mencionar domínio (produto, nota, estoque, financeiro)."

    agent_name = _derive_agent_name(description, target_table)
    skill_filename = f"{agent_name}_helper.py"
    function_name, code = _build_skill_code(description, target_table, agent_name, ids)

    security_error = _validate_generated_code(code)
    if security_error:
        return security_error

    proposal_id = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    proposal = {
        "proposal_id": proposal_id,
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        "status": "draft",
        "description": description,
        "target_table": target_table,
        "agent_name": agent_name,
        "skill_filename": skill_filename,
        "function_name": function_name,
    }
    _write_proposal(proposal, code)

    return (
        f"✅ Proposta criada: `{proposal_id}`\n"
        f"- Arquivo alvo: `{skill_filename}`\n"
        f"- Função: `{function_name}`\n"
        f"- Tabela foco: `{target_table}`\n\n"
        f"Use `review_tool_proposal('{proposal_id}')` para revisar e `publish_tool_proposal('{proposal_id}')` para publicar."
    )


def review_tool_proposal(proposal_id: str) -> str:
    """
    Etapa 2 - Revisa proposta existente (metadata + preview + segurança).
    """
    proposal, code = _read_proposal(proposal_id)
    if not proposal or code is None:
        return f"❌ Proposta `{proposal_id}` não encontrada."

    security_error = _validate_generated_code(code)
    preview = "\n".join(code.splitlines()[:40])
    status = proposal.get("status", "draft")

    report = [
        f"### Revisão da Proposta `{proposal_id}`",
        f"- Status: **{status}**",
        f"- Arquivo alvo: `{proposal.get('skill_filename')}`",
        f"- Função: `{proposal.get('function_name')}`",
        f"- Tabela foco: `{proposal.get('target_table')}`",
    ]
    if security_error:
        report.append(f"- Segurança: **REPROVADO** ({security_error})")
    else:
        report.append("- Segurança: **OK**")

    report.append("\n#### Preview (primeiras linhas)\n```python\n" + preview + "\n```")
    return "\n".join(report)


def publish_tool_proposal(proposal_id: str) -> str:
    """
    Etapa 3 - Publica proposta draft no diretório oficial de skills.
    """
    _ensure_factory_dirs()
    proposal, code = _read_proposal(proposal_id)
    if not proposal or code is None:
        return f"❌ Proposta `{proposal_id}` não encontrada."

    security_error = _validate_generated_code(code)
    if security_error:
        return f"❌ Publicação bloqueada por segurança: {security_error}"

    skill_filename = proposal["skill_filename"]
    target_path = os.path.join(SKILLS_DIR, skill_filename)
    backup_path = _snapshot_existing(skill_filename, proposal_id)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(code)

    proposal["status"] = "published"
    proposal["published_at"] = dt.datetime.now().isoformat(timespec="seconds")
    proposal["published_path"] = target_path
    if backup_path:
        proposal["backup_path"] = backup_path
    _write_proposal(proposal, code)

    msg = (
        f"✅ Proposta `{proposal_id}` publicada em `{skill_filename}`.\n"
        f"Ferramenta disponível: `{proposal['function_name']}`."
    )
    if backup_path:
        msg += f"\nBackup criado em `{backup_path}`."
    return msg


def rollback_tool(skill_filename: str) -> str:
    """
    Etapa 4 - Restaura a versão anterior da skill a partir do backup mais recente.
    """
    _ensure_factory_dirs()
    if not skill_filename.endswith(".py"):
        skill_filename = f"{skill_filename}.py"

    backup = _latest_backup(skill_filename)
    if not backup:
        return f"❌ Nenhum backup encontrado para `{skill_filename}`."

    target_path = os.path.join(SKILLS_DIR, skill_filename)
    shutil.copy2(backup, target_path)
    return f"✅ Rollback concluído para `{skill_filename}` usando backup `{os.path.basename(backup)}`."


def list_tool_proposals(status: str = "all") -> str:
    """
    Lista propostas da factory (all, draft, published).
    """
    _ensure_factory_dirs()
    rows: List[Dict[str, Any]] = []
    for filename in sorted(os.listdir(PROPOSALS_DIR)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(PROPOSALS_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                item = json.load(f)
            item_status = item.get("status", "draft")
            if status != "all" and item_status != status:
                continue
            rows.append(
                {
                    "proposal_id": item.get("proposal_id"),
                    "status": item_status,
                    "skill_filename": item.get("skill_filename"),
                    "function_name": item.get("function_name"),
                    "created_at": item.get("created_at"),
                }
            )
        except Exception:
            continue

    if not rows:
        return f"Nenhuma proposta encontrada para status `{status}`."

    lines = [f"### Propostas ({status})"]
    for r in rows:
        lines.append(
            f"- `{r['proposal_id']}` | {r['status']} | `{r['skill_filename']}` | `{r['function_name']}` | {r['created_at']}"
        )
    return "\n".join(lines)


def create_agent_skill(description: str) -> str:
    """
    Compatibilidade: cria e publica imediatamente (fluxo antigo).
    Recomendado usar o fluxo governado: propose/review/publish.
    """
    proposed = propose_tool(description)
    match = re.search(r"`(\d{14})`", proposed)
    if not match:
        return proposed
    proposal_id = match.group(1)
    published = publish_tool_proposal(proposal_id)
    return proposed + "\n\n" + published
