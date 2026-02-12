
import logging
import pandas as pd
import os
import json
from datetime import datetime

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("feedback-learner")

LEARNING_DB_PATH = "mcp_server/domains/procurement/knowledge/feedback_rules.json"

def process_procurement_feedback(file_path: str):
    """
    Lê a planilha de feedback do usuário e aprende novas regras de decisão.
    Baseado nas colunas 'Sua Decisão (Qtd)' e 'Seu Motivo'.
    """
    
    if not os.path.exists(file_path):
        logger.error(f"Arquivo não encontrado: {file_path}")
        return

    logger.info(f"Processando feedback do arquivo: {file_path}")
    
    try:
        df = pd.read_excel(file_path, sheet_name='Análise de Giro')
    except Exception as e:
        logger.error(f"Erro ao ler Excel: {e}")
        return

    # Filtrar apenas linhas onde o usuário tomou uma decisão diferente da sugestão
    # Ou onde preencheu um motivo
    feedback_rows = df[df['Sua Decisão (Qtd)'].notna() | df['Seu Motivo'].notna()]
    
    if feedback_rows.empty:
        logger.info("Nenhum feedback encontrado na planilha.")
        return

    new_rules = []

    for index, row in feedback_rows.iterrows():
        codprod = row['Código']
        produto = row['Produto']
        sugestao_agente = row['Sugestão Agente']
        decisao_usuario = row['Sua Decisão (Qtd)']
        motivo_usuario = str(row['Seu Motivo'])

        # Se decisão for vazia, assume que concordou com o Agente (se motivo vazio)
        # Mas aqui focamos na Divergência
        if pd.isna(decisao_usuario):
            continue

        diff = decisao_usuario - sugestao_agente
        action_type = "REDUCAO" if diff < 0 else "AUMENTO"
        
        logger.info(f"Aprendendo com {produto}: Usuário decidiu {decisao_usuario} vs Agente {sugestao_agente} ({action_type}). Motivo: {motivo_usuario}")

        # Estrutura da Regra Aprendida
        rule = {
            "timestamp": datetime.now().isoformat(),
            "trigger": {
                "codprod": codprod,
                "giro_dia": row['Giro Diário'],
                "estoque_atual": row['Estoque Atual'],
                "dias_cobertura": row['Dias Cobertura']
            },
            "action": {
                "type": action_type,
                "user_value": decisao_usuario,
                "agent_value": sugestao_agente,
                "justification_keyword": extract_keywords(motivo_usuario)
            },
            "original_reason": motivo_usuario
        }
        new_rules.append(rule)

    save_knowledge(new_rules)

def extract_keywords(text: str):
    """Extração simples de palavras-chave do motivo."""
    keywords = ["sazonal", "promoção", "fim de linha", "substituto", "erro", "estoque virtual", "caixa"]
    found = [k for k in keywords if k in text.lower()]
    return found if found else ["manual_override"]

def save_knowledge(new_rules: list):
    """Salva as regras aprendidas no 'cérebro' do agente."""
    if not os.path.exists(os.path.dirname(LEARNING_DB_PATH)):
        os.makedirs(os.path.dirname(LEARNING_DB_PATH))

    current_knowledge = []
    if os.path.exists(LEARNING_DB_PATH):
        try:
            with open(LEARNING_DB_PATH, 'r') as f:
                current_knowledge = json.load(f)
        except json.JSONDecodeError:
            current_knowledge = []
    
    current_knowledge.extend(new_rules)
    
    with open(LEARNING_DB_PATH, 'w') as f:
        json.dump(current_knowledge, f, indent=4)
        
    logger.info(f"{len(new_rules)} novas regras de compra aprendidas e salvas.")

if __name__ == "__main__":
    # Exemplo de uso: processar o último arquivo gerado (simulação)
    # Na prática, este script seria chamado quando o arquivo voltasse do WhatsApp
    import glob
    list_of_files = glob.glob('outputs/*.xlsx')
    if list_of_files:
        latest_file = max(list_of_files, key=os.path.getctime)
        process_procurement_feedback(latest_file)
