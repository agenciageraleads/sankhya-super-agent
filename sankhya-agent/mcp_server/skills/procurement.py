import logging
import re
from typing import List, Dict, Any, Optional

# Singleton das ferramentas
try:
    from utils import sankhya
except ImportError:
    from mcp_server.utils import sankhya


logger = logging.getLogger("skill-procurement")

# Cores mapeadas conforme padrões encontrados no banco
COLOR_TOKENS = {"AZ", "AM", "PT", "VD", "VM", "BC", "CZ", "MR", "BR", "VD/AM", "AZUL", "CINZA", "BRANCO", "PRETO", "VERMELHO", "VERDE", "AMARELO"}
# Embalagens e volumes que devem ser ignorados na "base" do nome
IGNORE_TOKENS = {"ROLO", "100MT", "BOBINA", "MT", "M", "UN", "CX", "KG"}

def _tokenize_product_name(name: str) -> Dict[str, Any]:
    """
    Quebra o nome do produto em: Base (nome limpo), Cor (identificada) e Outros.
    Ex: 'CABO FLEXIVEL 2,5MM AZ (ROLO 100MT)' 
    -> Base: 'CABO FLEXIVEL 2,5MM', Color: 'AZ'
    """
    clean_name = name.upper().replace("(", "").replace(")", "").replace("-", " ")
    parts = clean_name.split()
    
    found_color = None
    base_parts = []
    
    for part in parts:
        if part in COLOR_TOKENS:
            found_color = part
        elif part in IGNORE_TOKENS or re.match(r"^\d+MT", part):
            continue
        else:
            base_parts.append(part)
            
    return {
        "base": " ".join(base_parts),
        "color": found_color
    }

def get_similar_products_stock(prod_id: int, base_name: str, group_id: int, color: Optional[str]) -> List[Dict[str, Any]]:
    """
    Busca produtos do mesmo grupo e base que possuem a mesma cor.
    """
    # Filtro base por grupo
    sql = f"""
    SELECT P.CODPROD, P.DESCRPROD, (E.ESTOQUE - E.RESERVADO) as SALDO
    FROM TGFPRO P
    JOIN TGFEST E ON P.CODPROD = E.CODPROD
    WHERE P.CODGRUPOPROD = {group_id}
    AND P.CODPROD <> {prod_id}
    AND P.ATIVO = 'S'
    """
    
    potential_matches = sankhya.execute_query(sql)
    confirmed_alternatives = []
    
    for rival in potential_matches:
        rival_meta = _tokenize_product_name(rival['DESCRPROD'])
        
        # Só é alternativa se:
        # 1. Mesma cor (ou ambos sem cor)
        # 2. Base do nome similar (ex: contém a base do original)
        if rival_meta['color'] == color:
            # Verifica se as 3 primeiras palavras da base batem (mais robusto que substring)
            orig_base_words = base_name.split()[:3]
            rival_base_words = rival_meta['base'].split()[:3]
            
            if orig_base_words == rival_base_words:
                confirmed_alternatives.append({
                    "id": rival['CODPROD'],
                    "name": rival['DESCRPROD'],
                    "saldo": float(rival['SALDO'])
                })
                
    return confirmed_alternatives

def get_product_purchasing_dossier(product_ids: List[int]) -> str:
    """
    Gera um dossiê de compras refinado considerando produtos alternativos (mesma cor/grupo).
    """
    if not product_ids:
        return "⚠️ Lista de IDs de produtos vazia."
        
    ids_str = ",".join(map(str, product_ids))
    
    # Queries base
    sql_main = f"""
    SELECT P.CODPROD, P.DESCRPROD, P.CODGRUPOPROD, SUM(E.ESTOQUE - E.RESERVADO) as SALDO
    FROM TGFPRO P
    JOIN TGFEST E ON P.CODPROD = E.CODPROD
    WHERE P.CODPROD IN ({ids_str})
    GROUP BY P.CODPROD, P.DESCRPROD, P.CODGRUPOPROD
    """
    
    sql_sales = f"""
    SELECT I.CODPROD, SUM(I.QTDNEG) as QTD_VENDIDA_90D
    FROM TGFITE I 
    JOIN TGFCAB C ON I.NUNOTA = C.NUNOTA
    WHERE I.CODPROD IN ({ids_str})
    AND C.DTNEG >= SYSDATE - 90
    AND C.TIPMOV = 'V' AND C.STATUSNOTA = 'L'
    GROUP BY I.CODPROD
    """
    
    main_items = sankhya.execute_query(sql_main)
    sales_map = {r['CODPROD']: float(r['QTD_VENDIDA_90D']) for r in sankhya.execute_query(sql_sales)}
    
    report = []
    for item in main_items:
        pid = item['CODPROD']
        name = item['DESCRPROD']
        group = item['CODGRUPOPROD']
        saldo = float(item['SALDO'])
        
        # Tokeniza para similaridade
        meta = _tokenize_product_name(name)
        alternatives = get_similar_products_stock(pid, meta['base'], group, meta['color'])
        saldo_alt = sum(a['saldo'] for a in alternatives)
        
        # Giro
        vendas_90d = sales_map.get(pid, 0)
        giro_dia = vendas_90d / 90
        cobertura = int(saldo / giro_dia) if giro_dia > 0 else 999
        
        # Regra de Decisão
        status = "🟢 OK"
        sugestao = "Nível Adequado"
        
        if cobertura < 15:
            if saldo_alt > (giro_dia * 30):
                status = "🔵 ALTERNAT."
                sugestao = f"Usar alternativo (Saldo: {saldo_alt:.0f} un)"
            else:
                status = "🔴 CRÍTICO"
                sugestao = f"Comprar Reposição (Giro: {giro_dia:.1f}/dia)"
        elif cobertura < 30:
            status = "🟡 ATENÇÃO"
            sugestao = "Acompanhar estoque"

        report.append({
            "Código": pid,
            "Produto": name[:40], # Corta para caber na tabela
            "Saldo": saldo,
            "Giro/Dia": f"{giro_dia:.1f}",
            "Cobertura": f"{cobertura}d",
            "Saldo Alt. (Mesma Cor)": f"{saldo_alt:.0f}",
            "Status": status,
            "Sugestão": sugestao
        })

    # Renderização da tabela
    if not report: return "Sem dados."
    
    headers = list(report[0].keys())
    md = "## 📊 Dossiê de Compras com Alternativos (Mestra Cor)\n\n"
    md += "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for r in report:
        md += "| " + " | ".join(str(v) for v in r.values()) + " |\n"
        
    return md

def generate_purchase_suggestion(criteria: str = "curva_a") -> str:
    """Ferramenta de entrada para o Agente."""
    if criteria == "curva_a":
        sql = "SELECT CODPROD FROM (SELECT CODPROD, SUM(QTDNEG) as V FROM TGFITE I JOIN TGFCAB C ON I.NUNOTA=C.NUNOTA WHERE C.DTNEG > SYSDATE-90 AND C.TIPMOV='V' GROUP BY CODPROD ORDER BY V DESC) WHERE ROWNUM <= 15"
        ids = [r['CODPROD'] for r in sankhya.execute_query(sql)]
        return get_product_purchasing_dossier(ids)
    return get_product_purchasing_dossier([int(x) for x in criteria.split(",")])

