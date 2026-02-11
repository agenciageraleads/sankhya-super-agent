"""
Agente Especialista em Impacto de Produção e Duplicidade
Gerado para: analisar duplicidade e impacto em processos produtivos de matéria prima para os códigos 17364, 153363 e 17756
"""
import logging
try:
    from utils import sankhya, format_as_markdown_table
except ImportError:
    from mcp_server.utils import sankhya, format_as_markdown_table

logger = logging.getLogger("skill-production-impact")

def diagnose_production_impact_issue(limit: int = 10) -> str:
    """Analisa duplicidade de produtos e seu impacto em fórmulas de produção e estoque."""
    pids = [17364, 153363, 17756]
    if not pids or pids == [0]: return "⚠️ Nenhum ID de produto fornecido para análise."
    
    ids_str = ", ".join(map(str, pids))
    
    # 1. Dados Básicos e Cadastro
    sql_cad = f"SELECT CODPROD, DESCRPROD, MARCA, ATIVO FROM TGFPRO WHERE CODPROD IN ({ids_str})"
    cadastro = sankhya.execute_query(sql_cad)
    
    # 2. Uso em Fórmulas de Produção (TGFICP)
    sql_prod = f"""
    SELECT I.CODMATPRIMA as CODPROD, P.DESCRPROD as PROD_FINAL, I.QTDMISTURA, I.CODPROD as COD_PAI
    FROM TGFICP I
    JOIN TGFPRO P ON I.CODPROD = P.CODPROD
    WHERE I.CODMATPRIMA IN ({ids_str})
    """
    producao = sankhya.execute_query(sql_prod)
    
    # 3. Saldo de Estoque
    sql_est = f"SELECT CODPROD, SUM(ESTOQUE - RESERVADO) as SALDO_DISPONIVEL FROM TGFEST WHERE CODPROD IN ({ids_str}) GROUP BY CODPROD"
    estoque = sankhya.execute_query(sql_est)
    
    res = f"### 🏭 Relatório de Impacto de Produção e Duplicidade\n\n"
    res += "**1. Cadastro dos Produtos:**\n" + format_as_markdown_table(cadastro)
    
    if producao:
        res += "\n\n**⚠️ Vínculos em Fórmulas de Produção (Onde é usado):**\n" + format_as_markdown_table(producao)
    else:
        res += "\n\n✅ **Nenhum vínculo em fórmulas de produção encontrado para estes códigos.**"
        
    res += "\n\n**📦 Posição de Estoque:**\n" + format_as_markdown_table(estoque)
    
    res += "\n\n---\n### 💡 Plano de Ação para Unificação:\n"
    res += "1. **Escolha o 'Pai':** Identifique qual dos códigos tem o cadastro mais completo ou maior giro.\n"
    res += "2. **Transfira o Estoque:** Use uma nota de 'Transferência entre Produtos' (Geralmente TOP 800 ou similar) para mover o saldo dos secundários para o principal.\n"
    if producao:
        res += "3. **Atualize as Fórmulas:** Você precisará alterar manualmente os registros na tela 'Composição de Produto' (TGFICP) trocando os códigos secundários pelo principal.\n"
    res += "4. **Inative os Duplicados:** Após transferir saldo e atualizar fórmulas, mude o campo 'Ativo' para 'Não' nos códigos que serão descartados subtitua-os pelo principal em compras futuras."
    
    return res
