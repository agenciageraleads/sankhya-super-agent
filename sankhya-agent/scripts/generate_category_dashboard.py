
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
        sugestao_sistema = float(item.get("SUGCOMPRA", 0) or 0)
        custo = float(item.get("CUSTOGER", 0) or 0)
        lead_time = float(item.get("LEADTIME", 0) or 0)
        
        # Inteligência de Compras Híbrida (Sistema + Agente)
        
        # 1. Cálculo de Cobertura Real
        dias_cobertura = (estoque / giro) if giro > 0 else 999
        if estoque > 0 and giro == 0:
            dias_cobertura = 9999 # Infinito (Sem giro recente)

        # 2. Definição da Sugestão Otimizada (Agente)
        sugestao_agente = sugestao_sistema
        obs_agente = ""
        status = "NEUTRO"
        cor = "AMARELO"
        acao = "MANTER"

        # Regra de Ouro: Cobertura Excessiva (> 120 dias)
        if dias_cobertura > 120:
            if sugestao_sistema > 0:
                sugestao_agente = 0
                obs_agente = f"SISTEMA PEDIU {int(sugestao_sistema)}, MAS COBERTURA É ALTA ({int(dias_cobertura)}d). SUGERIDO ZERO."
            status = "LIQUIDAR"
            cor = "VERMELHO"
            acao = "VENDER / PROMOÇÃO"
            if estoque > 0:
                total_overstock += (estoque * custo)

        # Regra de Ouro: Ruptura ou Baixa Cobertura (< Lead Time)
        elif dias_cobertura < lead_time:
            # Se sistema não pediu, Agente calcula necessidade
            if sugestao_sistema == 0 and giro > 0:
                # Necessidade = (Giro * (LeadTime + Margem 30%)) - Estoque
                necessidade = (giro * (lead_time * 1.3)) - estoque
                if necessidade > 0:
                    sugestao_agente = necessidade
                    obs_agente = f"SISTEMA ZERADO, MAS RISCO DE RUPTURA (Cob {dias_cobertura:.1f}d < Lead {lead_time}d). SUGERIDO {int(necessidade)}."
            
            status = "COMPRAR"
            cor = "VERDE"
            acao = f"COMPRAR {int(sugestao_agente)}"
            total_buy += (sugestao_agente * custo)
            
        else:
            # Zona de Conforto (Entre Lead Time e 120 dias)
            if sugestao_sistema > 0:
                 # Sistema pedindo reposição preventiva
                 status = "COMPRAR"
                 cor = "VERDE"
                 acao = f"COMPRAR {int(sugestao_sistema)}"
                 total_buy += (sugestao_sistema * custo)

        # Formatação do Valor
        cob_str = f"{dias_cobertura:.1f}" if dias_cobertura < 999 else "INF"
        if dias_cobertura == 9999: cob_str = "SEM GIRO"

        processed_items.append({
            "Código": item.get("CODPROD"),
            "Descrição": item.get("DESCRPROD"),
            "Marca": item.get("MARCA"),
            "Grupo": item.get("GRUPO"),
            "Macro Grupo": item.get("MACRO_GRUPO"),
            "Estoque": estoque,
            "Giro Diário": giro,
            "Cobertura (Dias)": cob_str,
            "Sugestão Sistema": sugestao_sistema,
            "Sugestão Otimizada": sugestao_agente,
            "Custo Unit.": custo,
            "Valor Sugestão": sugestao_agente * custo,
            "Valor Estoque": estoque * custo,
            "Status": status,
            "Ação Recomendada": acao,
            "Obs. Agente": obs_agente,
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
    
    # CRÍTICO: Resetar index para que iterrows coincida com a linha do Excel
    df.reset_index(drop=True, inplace=True)

    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        workbook = writer.book
        sheet_name = "Análise Categoria"
        
        # Formatos
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        money_fmt = workbook.add_format({'num_format': 'R$ #,##0.00'})
        green_fmt = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        red_fmt = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        yellow_fmt = workbook.add_format({'bg_color': '#FFFFCC'}) # Amarelo Manter
        yellow_alert_fmt = workbook.add_format({'bg_color': '#FFFF00', 'bold': True}) # Amarelo Alerta
        
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
        ws.set_column('C:E', 20) # Marca/Grupos
        ws.set_column('K:K', 15, money_fmt) # Valor Sugestão
        ws.set_column('L:L', 15, money_fmt) # Valor Estoque
        ws.set_column('M:N', 20) # Status/Ação

        # Aplicação das Cores
        # Com reset_index, row_idx agora é 0, 1, 2... correspondendo à ordem visual
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
    # Exemplo de uso:
    # 1. Gerar para uma MARCA específica (ex: SOPRANO, TRAMONTINA)
    generate_category_report("MARCA", "SOPRANO")
    generate_category_report("MARCA", "TRAMONTINA ELETRIA")

    # 2. Gerar para um MACRO GRUPO (ex: 'IN' se for o que tem no banco, ou busca textual 'GRUPO')
    # Como o usuário informou que Eletrodutos é um Macro, e vimos 'IN' no banco,
    # Vamos tentar buscar por descrição do GRUPO para ser mais assertivo agora.
    generate_category_report("GRUPO", "ELET") # Pega Eletrodutos, Eletrocalhas
    generate_category_report("GRUPO", "CABO") # Pega Fios e Cabos
    
    # Futuramente: Ler de um arquivo de configuração quais categorias monitorar.
