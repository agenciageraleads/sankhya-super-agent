
import logging
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from mcp_server.domains.procurement.services.sankhya_adapter import SankhyaProcurementService

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("strategic-report")

STATE_FILE = "mcp_server/domains/procurement/knowledge/supplier_state.json"
MIN_ORDER_DEFAULT = 1500.0 # Valor mínimo padrão para análise diária

def load_supplier_state() -> Dict[str, Any]:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_supplier_state(state: Dict[str, Any]):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

def check_analysis_frequency(cod_parc: str, current_value: float, state: Dict[str, Any]) -> str:
    """
    Verifica se o fornecedor deve ser analisado hoje.
    Retorna: 'ANALYZE', 'SKIP_RECENT', 'SKIP_LOW_VALUE'
    """
    if str(cod_parc) not in state:
        return 'ANALYZE'
    
    supplier_info = state[str(cod_parc)]
    last_date_str = supplier_info.get("last_analysis_date")
    min_order = supplier_info.get("average_min_order", MIN_ORDER_DEFAULT)
    
    if not last_date_str:
        return 'ANALYZE'
        
    last_date = datetime.fromisoformat(last_date_str)
    days_since = (datetime.now() - last_date).days
    
    # Se valor atual é alto (acima do pedido mínimo), analisa sempre
    if current_value >= min_order:
        return 'ANALYZE'
        
    # Se valor é baixo e foi analisado recentemente (< 3 dias), pula
    if days_since < 3:
        return 'SKIP_RECENT'
        
    return 'ANALYZE' # Passou tempo suficiente, analisa novamente

def generate_strategic_report(output_dir: str = "outputs"):
    """
    Gera relatório estratégico focado em oportunidades de compra agrupadas por Fornecedor.
    Inclui lógica de frequência de análise e aprendizado de estado.
    """
    
    service = SankhyaProcurementService(domain_path="mcp_server/domains/procurement")

    try:
        # A. Buscar Oportunidades Agrupadas (usando histórico real)
        # Atenção: queries_opportunities_by_supplier.sql deve estar usando a lógica de histórico (TIPMOV='O')
        opportunities = service.get_opportunities(codrel=2535)
    except Exception as e:
        logger.error(f"Erro ao buscar oportunidades: {e}")
        return

    # B. Buscar Contexto de Família (Estoque Agregado)
    try:
        group_stock_map = service.get_group_stock_summary(codrel=2535)
    except Exception as e:
        logger.warning(f"Não foi possível carregar contexto de família: {e}")
        group_stock_map = {}

    supplier_state = load_supplier_state()
    
    report_data = [] # Lista final para o Excel
    supplier_details = {} # Detalhes dos itens para as abas
    
    logger.info(f"Analisando {len(opportunities)} fornecedores potenciais...")

    today_str = datetime.now().isoformat()

    for opp in opportunities:
        cod_parc = opp.get("CODPARCFORN")
        nome_parc = opp.get("FORNECEDOR")
        vlr_total = float(opp.get("VLR_TOTAL_SUGESTAO", 0) or 0)
        ruptura_count = int(opp.get("ITENS_RUPTURA", 0) or 0)
        
        # Lógica de Decisão de Análise
        decision = check_analysis_frequency(cod_parc, vlr_total, supplier_state)
        
        # Se tiver ruptura, SEMPRE analisa (Prioridade Crítica)
        if ruptura_count > 0:
            decision = 'ANALYZE_CRITICAL'
            
        status_final = "VALIDAR PEDIDO"
        if vlr_total < MIN_ORDER_DEFAULT:
            status_final = "ABAIXO MINIMO"
        if decision == 'SKIP_RECENT':
            status_final = "PROCESSADO RECENTEMENTE (IGNORAR)"
            
        # Monta linha do relatório resumo
        row = {
            "CODPARCFORN": cod_parc,
            "FORNECEDOR": nome_parc,
            "VLR_TOTAL_SUGESTAO": vlr_total,
            "MIX_PRODUTOS": opp.get("MIX_PRODUTOS"),
            "ITENS_RUPTURA": ruptura_count,
            "STATUS_ANALISE": status_final,
            "DECISAO_SISTEMA": decision
        }
        report_data.append(row)
        
        # Se a decisão for analisar, busca os detalhes e atualiza estado
        if decision in ['ANALYZE', 'ANALYZE_CRITICAL']:
            # Busca itens detalhados deste fornecedor (já vem ordenado por nome do SQL)
            raw_details = service.get_supplier_items(codparc=cod_parc)
            processed_details = []
            
            for item in raw_details:
                giro_dia = float(item.get("GIRODIARIO", 0) or 0)
                estoque = float(item.get("ESTOQUE", 0) or 0)
                est_min = float(item.get("ESTMIN", 0) or 0)
                sugestao = float(item.get("SUGCOMPRA", 0) or 0)
                custo = float(item.get("CUSTOGER", 0) or 0)
                lead_time = float(item.get("LEADTIME", 0) or 0)
                cod_grupo = item.get("CODGRUPOPROD")
                
                # Regra de Exclusão: Cobertura > 90 dias
                dias_cobertura = (estoque / giro_dia) if giro_dia > 0 else 999
                if dias_cobertura > 90 and estoque > 0 and giro_dia > 0:
                    continue 

                # Contexto de Família
                estoque_familia = group_stock_map.get(cod_grupo, 0)
                
                # Montagem da Explicação (Raciocínio)
                motivo = []
                if estoque == 0:
                    motivo.append("RUPTURA TOTAL (Estoque Zero)")
                elif dias_cobertura < lead_time:
                    motivo.append(f"ALERTA (Cob. {dias_cobertura:.1f}d < Lead {lead_time}d)")
                elif estoque < est_min:
                    motivo.append(f"ABAIXO MÍNIMO ({estoque} < {est_min})")
                
                if giro_dia == 0 and sugestao > 0:
                    motivo.append("REPOSIÇÃO ESTOQUE MÍNIMO (Sem giro recente)")
                
                # Enrich Item
                item["VALOR_SUGESTAO"] = round(sugestao * custo, 2)
                item["DIAS_COBERTURA"] = round(dias_cobertura, 1) if dias_cobertura < 999 else "INF"
                item["ESTOQUE_FAMILIA"] = estoque_familia
                item["MOTIVO_AGENTE"] = " | ".join(motivo)
                
                # Flag de Alerta: Se tem muito estoque na família mas sistema pede compra deste
                # "VERIFICAR": Significa que você tem produtos similares parados. Antes de comprar este, verifique se pode substituir.
                if (estoque_familia > (estoque * 5) and estoque_familia > 100):
                     item["ALERTA_FAMILIA"] = "⚠️ SUBSTITUIÇÃO? (Estoque Alto na Família)"
                else:
                     item["ALERTA_FAMILIA"] = "OK"

                processed_details.append(item)

            if processed_details:
                supplier_details[nome_parc] = processed_details
            
            # Atualiza Estado
            entry = supplier_state.get(str(cod_parc), {})
            entry.update({
                "last_analysis_date": today_str,
                "last_total_value": vlr_total
            })
            supplier_state[str(cod_parc)] = entry

    # Salva estado atualizado
    save_supplier_state(supplier_state)

    # Gerar Excel
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"Analise_Compras_Fornecedor_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    filepath = os.path.join(output_dir, filename)

    # Ordenação Consistente: Ruptura DESC, Valor Total DESC
    report_data.sort(key=lambda x: (x['ITENS_RUPTURA'], x['VLR_TOTAL_SUGESTAO']), reverse=True)

    df_summary = pd.DataFrame(report_data)

    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Formatos
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        money_fmt = workbook.add_format({'num_format': 'R$ #,##0.00'})
        green_fmt = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        red_fmt = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        yellow_fmt = workbook.add_format({'bg_color': '#FFFFCC'})
        
        # 1. Aba Resumo
        summary_sheet = "Visão Geral"
        df_summary.to_excel(writer, sheet_name=summary_sheet, index=False)
        ws_summary = writer.sheets[summary_sheet]
        ws_summary.freeze_panes(1, 0)
        ws_summary.set_column('A:A', 10) # CODPARCFORN
        ws_summary.set_column('B:B', 40) # FORNECEDOR
        ws_summary.set_column('C:C', 20, money_fmt) # VLR_TOTAL_SUGESTAO
        ws_summary.set_column('D:D', 15) # MIX_PRODUTOS
        ws_summary.set_column('E:E', 15) # ITENS_RUPTURA
        ws_summary.set_column('F:F', 30) # STATUS_ANALISE
        ws_summary.set_column('G:G', 20) # DECISAO_SISTEMA

        # Formatação Condicional para o Resumo
        ws_summary.conditional_format('F2:F' + str(len(df_summary) + 1),
                                      {'type': 'text', 'criteria': 'containing', 'value': 'VALIDAR PEDIDO', 'format': green_fmt})
        ws_summary.conditional_format('F2:F' + str(len(df_summary) + 1),
                                      {'type': 'text', 'criteria': 'containing', 'value': 'ABAIXO MINIMO', 'format': yellow_fmt})
        ws_summary.conditional_format('F2:F' + str(len(df_summary) + 1),
                                      {'type': 'text', 'criteria': 'containing', 'value': 'PROCESSADO RECENTEMENTE', 'format': yellow_fmt})

        # 2. Abas Detalhadas por Fornecedor (Máximo 30 abas para não sobrecarregar)
        analyzed_count = 0
        for rep in report_data: # Iterar sobre report_data que já está ordenado
            supp_name = str(rep.get("FORNECEDOR"))
            # Limita o nome da aba a 30 caracteres e remove caracteres especiais
            safe_name = "".join([c for c in supp_name if c.isalnum() or c in (' ', '-', '_')])[:30]
            # Substitui espaços por underscores para nomes de aba mais limpos
            safe_name = safe_name.replace(' ', '_')
            
            if supp_name in supplier_details:
                details = supplier_details[supp_name]
                if not details: continue
                
                # Filtragem e Processamento Específico
                filtered_details = []
                total_sugestao_aba = 0

                for row in details:
                    # Filtro 1: Cobertura Infinita (> 90 dias)
                    # Se tem estoque e giro zero, ou estoque alto demais, ignora sugestão de compra (vai para relatório de sobra)
                    if isinstance(row.get("DIAS_COBERTURA"), (int, float)) and row.get("DIAS_COBERTURA") > 90:
                        continue
                    if row.get("DIAS_COBERTURA") == "INF": # Giro Zero com Estoque > 0
                        continue

                    # Filtro 2: Regra Soprano GIII
                    # Se Fornecedor/Marca é SOPRANO e é Disjuntor, só aceita se tiver GIII na descrição
                    if "SOPRANO" in supp_name.upper() or "SOPRANO" in str(row.get("MARCA", "")).upper():
                        desc = str(row.get("DESCRPROD", "")).upper()
                        if "DISJ" in desc and "GIII" not in desc:
                             continue # Ignora Disjuntor Soprano antigo (fora de linha)

                    filtered_details.append(row)
                    total_sugestao_aba += float(row.get("VALOR_SUGESTAO", 0))

                if not filtered_details: continue # Se filtrou tudo, não gera aba

                df_det = pd.DataFrame(filtered_details)
                
                # Colunas Finais (Renomeadas para Clareza)
                api_cols_map = {
                    "CODPROD": "Cód.",
                    "DESCRPROD": "Produto",
                    "MARCA": "Marca/Linha",
                    "SUGCOMPRA": "Qtd Sug.",
                    "VALOR_SUGESTAO": "Valor Total (R$)",
                    "GIRODIARIO": "Giro Dia",
                    "ESTOQUE": "Estoque Atual",
                    "DIAS_COBERTURA": "Cobertura (Dias)",
                    "ALERTA_FAMILIA": "Análise de Similaridade (Família)"
                }
                
                df_det.rename(columns=api_cols_map, inplace=True)
                final_cols = [c for c in api_cols_map.values() if c in df_det.columns]
                
                # Escreve dados (Começando na linha 2)
                df_det[final_cols].to_excel(writer, sheet_name=safe_name, startrow=1, index=False)
                
                # Cabeçalho com Total
                ws_det = writer.sheets[safe_name]
                ws_det.write(0, 5, "TOTAL SUGESTÃO:", header_fmt)
                ws_det.write(0, 6, total_sugestao_aba, money_fmt)

                # Formatação Visual Detalhada
                ws_det.freeze_panes(2, 0)
                ws_det.set_column('B:B', 45) # Produto
                ws_det.set_column('C:C', 15) # Marca
                ws_det.set_column('E:E', 18, money_fmt) # Valor
                ws_det.set_column('I:I', 30) # Análise Família
                
                # Cores nas Linhas (Baseado em Ruptura/Alerta)
                # Iterar sobre as linhas escritas
                for row_idx, row_data in df_det.iterrows():
                    excel_row = row_idx + 2 # Header ocupa 2 linhas (1 do total + 1 do df)
                    
                    # Se Ruptura (Estoque ~ 0) -> Vermelho Claro
                    est = float(row_data.get("Estoque Atual", 0))
                    if est <= 0:
                        ws_det.set_row(excel_row, None, red_fmt)
                    
                    # Se Alerta Família (Substituição) -> Amarelo
                    alerta = str(row_data.get("Análise de Similaridade (Família)", ""))
                    if "SUBSTITUIÇÃO" in alerta:
                         try:
                             col_idx = list(df_det.columns).index("Análise de Similaridade (Família)")
                             ws_det.write(excel_row, col_idx, alerta, yellow_fmt)
                         except:
                             pass
                
                analyzed_count += 1
                if analyzed_count >= 30: break

    logger.info(f"Relatório de Frequência gerado: {filepath}")
    return filepath

if __name__ == "__main__":
    generate_strategic_report()
