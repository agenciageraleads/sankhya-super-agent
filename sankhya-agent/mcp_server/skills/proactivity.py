import logging
import re
from typing import List, Dict, Any, Optional

# Singleton das ferramentas e utilitários
try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

logger = logging.getLogger("skill-proactivity")


def investigate_system_behavior(subject: str) -> str:
    """
    Realiza uma investigação profunda e proativa sobre uma tabela, campo ou processo do Sankhya.
    Combina: Metadados do DB + Documentação da Knowledge Base + Amostragem de Dados Reais.
    """
    # Late imports para evitar circularidade
    try:
        from tools import search_solutions, describe_entity
    except ImportError:
        from mcp_server.tools import search_solutions, describe_entity

    report = [f"# 🔍 Relatório de Investigação Proativa: {subject}\n"]

    
    # 1. Identificar se o assunto contém uma tabela (formato TGFXXX, TSIXXX, AD_XXX, etc)
    # Buscamos por padrões comuns de tabelas do Sankhya
    patterns = [
        r"\b(TGF[A-Z0-9_]+)\b",
        r"\b(TSI[A-Z0-9_]+)\b",
        r"\b(AD_[A-Z0-9_]+)\b",
        r"\b(TDV[A-Z0-9_]+)\b",
        r"\b(TSW[A-Z0-9_]+)\b",
        r"\b([A-Z]{3}[A-Z0-9_]{2,})\b" # Fallback para qualquer palavra de >5 letras em maiúsculo (exceto stop words)
    ]
    
    table_name = None
    subject_upper = subject.upper()
    
    for p in patterns:
        match = re.search(p, subject_upper)
        if match:
            candidate = match.group(1)
            # Ignorar palavras comuns que podem casar com o padrão fallback
            if candidate not in ["QUERO", "ENTENDER", "TABELA", "COMO", "SOBRE"]:
                table_name = candidate
                break

    
    # 2. Busca na Knowledge Base (Sempre útil para contexto de negócio)
    report.append("## 📚 Documentação (Knowledge Base)")
    docs = search_solutions(subject)
    if "Nenhuma solução encontrada" in docs:
        # Se falhou com a query completa, tenta apenas com a tabela
        if table_name:
            docs = search_solutions(table_name)
    report.append(docs + "\n")
    
    # 3. Metadados do Banco de Dados (Se houver tabela identificada)
    if table_name:
        report.append(f"## 🏗️ Metadados da Tabela `{table_name}`")
        metadata = describe_entity(table_name)
        report.append(metadata + "\n")
        
        # 4. Amostragem de Dados Reais (Data Scan)
        # Executa um select limitado para ver o formato dos dados
        report.append(f"## 📋 Amostra de Dados Reais (Top 3)")
        try:
            # Oracle syntax: FETCH FIRST 3 ROWS ONLY (ou ROWNUM <= 3)
            # Usamos ROWNUM por ser compatível com versões mais antigas do Oracle/Sankhya
            sample_sql = f"SELECT * FROM {table_name} WHERE ROWNUM <= 3"
            sample_data = sankhya.execute_query(sample_sql)
            
            if sample_data:
                report.append(format_as_markdown_table(sample_data))
            else:
                report.append("*Nenhum dado encontrado para amostragem.*")
        except Exception as e:
            report.append(f"⚠️ Não foi possível obter amostra: {str(e)}")
    
    report.append("\n---\n*Investigação concluída de forma autônoma pelo Agente.*")
    return "\n".join(report)
