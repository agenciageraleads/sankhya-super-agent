
import logging
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any
from mcp_server.domains.procurement.services.sankhya_adapter import SankhyaProcurementService

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("category-dashboard")

def generate_category_report(target_type: str, target_name: str, output_dir: str = "outputs"):
    """
    Gera um relatório de análise de categoria (Marca ou Macro Grupo).
    Foco: Buy (Verde), Hold (Amarelo), Sell (Vermelho).
    """
    service = SankhyaProcurementService(domain_path="mcp_server/domains/procurement")

    logger.info(f"Gerando análise para {target_type}: {target_name}...")
    
    try:
        items = service.get_full_category_analysis(target_type, target_name)
    except Exception as e:
        logger.error(f"Erro ao buscar dados: {e}")
        return

    if not items:
        logger.warning(f"Nenhum item encontrado para {target_name}.")
        return

    processed_items = []
    
    total_buy = 0.0
    total_overstock = 0.0
    
    for item in items:
        estoque = float(item.get("ESTOQUE", 0) or 0)
        giro = float(item.get("GIRODIARIO", 0) or 0)
        sugestao = float(item.get("SUGCOMPRA", 0) or 0)
        custo = float(item.get("CUSTOGER", 0) or 0)
        lead_time = float(item.get("LEADTIME", 0) or 0)
        
        # Cálculo de Cobertura
        dias_cobertura = (estoque / giro) if giro > 0 else 999
        if estoque > 0 and giro == 0:
            dias_cobertura = 9999 # Infinito
            
        # Classificação de Status (Buy/Hold/Sell)
        status = "NEUTRO"
        cor = "AMARELO"
        acao = "MANTER"
        
        # 1. Verde: Precisamos Comprar
        if sugestao > 0:
            status = "COMPRAR"
            cor = "VERDE"
            acao = f"COMPRAR {int(sugestao)}"
            total_buy += (sugestao * custo)
            
        # 2. Vermelho: Excesso de Estoque (Sell)
        # Critério: Cobertura > 120 dias ou Infinito (sem giro)
        elif dias_cobertura > 120 or dias_cobertura == 9999:
            status = "LIQUIDAR"
            cor = "VERMELHO"
            acao = "VENDER / PROMOÇÃO"
            if estoque > 0:
                total_overstock += (estoque * custo)

        # Formatação do Valor
        cob_str = f"{dias_cobertura:.1f}" if dias_cobertura < 999 else "INF"
        if dias_cobertura == 9999: cob_str = "SEM GIRO"

        processed_items.append({
            "Código": item.get("CODPROD"),
            "Descrição": item.get("DESCRPROD"),
            "Marca": item.get("MARCA"),
            "Macro Grupo": item.get("MACRO_GRUPO"),
            "Estoque": estoque,
            "Giro Diário": giro,
            "Cobertura (Dias)": cob_str,
            "Sugestão Compra": sugestao,
            "Custo Unit.": custo,
            "Valor Sugestão": sugestao * custo,
            "Valor Estoque": estoque * custo,
            "Status": status,
            "Ação Recomendada": acao,
            "_COR": cor 
        })

    # Gerar Excel
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    safe_name = "".join([c for c in target_name if c.isalnum() or c in (' ', '-', '_')])
    filename = f"Analise_{target_type}_{safe_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    filepath = os.path.join(output_dir, filename)

    df = pd.DataFrame(processed_items)
    
    # Ordenar: Primeiro os verdes (urgência), depois vermelhos (problema), depois amarelos
    # Mapeamento para sort
    priority_map = {"VERDE": 1, "VERMELHO": 2, "AMARELO": 3}
    df['_PRIORITY'] = df['_COR'].map(priority_map)
    df.sort_values(by=['_PRIORITY', 'Descrição'], inplace=True)
    df.drop(columns=['_PRIORITY'], inplace=True)

    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        workbook = writer.book
        sheet_name = "Análise Categoria"
        
        # Formatos
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        money_fmt = workbook.add_format({'num_format': 'R$ #,##0.00'})
        green_fmt = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        red_fmt = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        yellow_fmt = workbook.add_format({'bg_color': '#FFFFCC'})
        
        df_export = df.drop(columns=['_COR'])
        df_export.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)
        
        ws = writer.sheets[sheet_name]
        ws.freeze_panes(3, 0)
        
        # Cabeçalho de Resumo
        ws.write(0, 0, f"ANÁLISE DE {target_type}: {target_name}", header_fmt)
        ws.write(0, 4, "TOTAL SUGESTÃO COMPRA:", header_fmt)
        ws.write(0, 5, total_buy, money_fmt)
        ws.write(0, 7, "CAPITAL PARADO (CRÍTICO):", header_fmt)
        ws.write(0, 8, total_overstock, money_fmt)
        
        # Largura Colunas
        ws.set_column('B:B', 40) # Descrição
        ws.set_column('J:J', 15, money_fmt) # Valor Sugestão
        ws.set_column('K:K', 15, money_fmt) # Valor Estoque
        ws.set_column('L:M', 20) # Status/Ação

        # Aplicação das Cores
        for row_idx, row_data in df.iterrows():
            excel_row = row_idx + 3 # Header (2 filas) + 1 (0-based)
            cor_ref = row_data['_COR']
            
            fmt = None
            if cor_ref == "VERDE": fmt = green_fmt
            elif cor_ref == "VERMELHO": fmt = red_fmt
            elif cor_ref == "AMARELO": fmt = yellow_fmt
            
            if fmt:
                ws.set_row(excel_row, None, fmt)

    logger.info(f"Relatório gerado: {filepath}")
    return filepath

if __name__ == "__main__":
    # Exemplo de execução baseada no pedido do usuário
    # "Soprano" (Marca) e "Eletrodutos" (Macro Grupo)
    generate_category_report("MACRO_GRUPO", "ELETRODUTOS")
    generate_category_report("MARCA", "SOPRANO")
