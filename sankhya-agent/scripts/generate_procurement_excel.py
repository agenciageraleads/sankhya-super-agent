import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from mcp_server.domains.procurement.services.sankhya_adapter import SankhyaProcurementService
from mcp_server.utils import sankhya

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("excel-generator")

def generate_procurement_excel(output_dir: str = "outputs"):
    """
    Gera uma planilha Excel com sugestões de compra baseada nas skills de Giro e Financeiro.
    Inclui colunas para feedback do usuário.
    """
    
    # 1. Inicializar Serviço
    service = SankhyaProcurementService(domain_path="mcp_server/domains/procurement")
    
    # Datas para análise (últimos 90 dias)
    fin_date = datetime.now()
    ini_date = fin_date - timedelta(days=90)
    ini_str = ini_date.strftime("%d/%m/%Y")
    fin_str = fin_date.strftime("%d/%m/%Y")

    logger.info(f"Iniciando análise de compras para o período: {ini_str} a {fin_str}")

    # 2. Executar Skills de Inteligência
    try:
        # A. Análise Direta de Giro (TGFGIR)
        # CODREL=2535 detectado nos logs.
        giro_data = service.get_giro_data(codrel=2535)
        
        # B. Análise Financeira (Contexto)
        financial_data = service.get_financial_procurement_balance(dias_horizonte=30)
        
    except Exception as e:
        logger.error(f"Erro ao executar skills: {e}")
        return

    # 3. Processar Dados para o Excel
    rows = []
    
    financeiro_summary = financial_data.get("saude_financeira", {})
    est_summary = financial_data.get("saude_estoque", {})

    logger.info(f"Processando {len(giro_data)} registros de Giro Direct.")

    for item in giro_data:
        codprod = item.get("CODPROD")
        descricao = item.get("DESCRPROD")
        giro_dia = float(item.get("GIRODIARIO", 0) or 0)
        estoque_atual = float(item.get("ESTOQUE", 0) or 0)
        sugestao_sistema = float(item.get("SUGCOMPRA", 0) or 0)
        est_min = float(item.get("ESTMIN", 0) or 0)
        lead_time = float(item.get("LEADTIME", 0) or 0)
        
        # Filtro Estratégico do Usuário:
        # "Focar naqueles que tiveram venda (giro) e estao com estoque baixo"
        if giro_dia <= 0 and estoque_atual > 0:
            continue # Pula sem giro (por enquanto)

        # Lógica de Sugestão e Motivo do Agente
        sugestao_agente = sugestao_sistema # Confia no sistema inicialmente
        motivo_agente = []

        # Regra 1: Ruptura Iminente
        dias_cobertura = (estoque_atual / giro_dia) if giro_dia > 0 else 999
        
        if dias_cobertura < lead_time:
            motivo_agente.append(f"⚠️ RUPTURA: Cobertura ({dias_cobertura:.1f}d) menor que Lead Time ({lead_time}d).")
        
        # Regra 2: Estoque Crítico
        if estoque_atual < est_min:
            motivo_agente.append(f"📉 ABAIXO MÍNIMO: {estoque_atual} < {est_min}.")

        # Regra 3: Consistência Financeira
        if financeiro_summary.get("aviso_pressao") == "ALTA" and sugestao_agente > 1000: # Valor alto arbitrário
             motivo_agente.append("💰 CAIXA: Avaliar parcelamento (Pressão Alta).")

        # Classificação de Cores para o Excel
        row_color = ""
        if dias_cobertura == 0:
            row_color = "#FF9999" # Vermelho Claro (Ruptura Total)
        elif dias_cobertura < lead_time:
            row_color = "#FFFFCC" # Amarelo Claro (Alerta)
        
        rows.append({
            "Código": codprod,
            "Produto": descricao,
            "Empresa": item.get("CODEMP"),
            "Giro Diário": giro_dia,
            "Estoque Atual": estoque_atual,
            "Dias Cobertura": round(dias_cobertura, 1),
            "Sugestão Sistema": sugestao_sistema,
            "Sugestão Agente": sugestao_agente,
            "Motivo Agente": " | ".join(motivo_agente),
            "Sua Decisão (Qtd)": "",
            "Seu Motivo": "",
            "_COLOR": row_color # Campo auxiliar para formatação
        })

    # 4. Criar DataFrame e Salvar Excel
    if not rows:
        logger.warning("Nenhum dado encontrado para gerar a planilha.")
        # Fallback para criar arquivo vazio com header
        rows.append({"Mensagem": "Nenhum dado encontrado na TGFGIR para o filtro aplicado."})

    df = pd.DataFrame(rows)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"Analise_Giro_Estrategica_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        # Aba Principal
        sheet_name = 'Análise de Giro'
        display_cols = [c for c in df.columns if c != "_COLOR"]
        df[display_cols].to_excel(writer, sheet_name=sheet_name, index=False)
        
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # Formatos
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        input_fmt = workbook.add_format({'bg_color': '#E0FFFF', 'border': 1}) # Ciano claro para input
        
        # Formatos de Alerta
        red_fmt = workbook.add_format({'bg_color': '#FF9999', 'border': 1})
        yellow_fmt = workbook.add_format({'bg_color': '#FFFFCC', 'border': 1})
        
        # Aplicar formatos iterando
        for row_idx, row_data in df.iterrows():
            row_color_code = row_data.get("_COLOR", "")
            cell_fmt = None
            
            if row_color_code == "#FF9999":
                cell_fmt = red_fmt
            elif row_color_code == "#FFFFCC":
                cell_fmt = yellow_fmt
            
            # Aplica a linha inteira (exceto inputs que têm cor própria)
            if cell_fmt:
                 for col_idx, col_name in enumerate(display_cols):
                     if col_name not in ["Sua Decisão (Qtd)", "Seu Motivo"]:
                        worksheet.write(row_idx + 1, col_idx, row_data[col_name], cell_fmt)

        # Formatação de Colunas
        for col_num, value in enumerate(display_cols):
            worksheet.write(0, col_num, value, header_fmt)
            if value in ["Sua Decisão (Qtd)", "Seu Motivo"]:
                worksheet.set_column(col_num, col_num, 20, input_fmt)
            else:
                 worksheet.set_column(col_num, col_num, 15)
                 
        # Aba de Legenda
        worksheet_legend = workbook.add_worksheet('Legenda')
        worksheet_legend.write(0, 0, "Legenda de Cores", header_fmt)
        worksheet_legend.write(1, 0, "Ruptura Total (Estoque Zero ou Insuficiente)", red_fmt)
        worksheet_legend.write(2, 0, "Alerta de Estoque Baixo (Menor que Lead Time)", yellow_fmt)
        worksheet_legend.write(3, 0, "Entrada de Dados (Seu Feedback)", input_fmt)

    logger.info(f"Planilha de Giro gerada: {filepath}")
    return filepath

if __name__ == "__main__":
    generate_procurement_excel()
