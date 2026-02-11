"""
Motor de Auto-Aprendizado (Learning Engine) do SSA.
Permite que o agente aprenda e evolua as regras de negócio do grupo.
"""
import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("learning-engine")
RULES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "knowledge", "business_rules.json")

def propose_new_rule(rule_id: str, condition: str, description: str, category: str = "mapping_rules") -> str:
    """
    Propõe a criação ou atualização de uma regra de negócio baseada no aprendizado.
    """
    try:
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            rules = json.load(f)
        
        # Cria a estrutura de 'proposed_rules' se não existir
        if "proposed_rules" not in rules:
            rules["proposed_rules"] = []
            
        new_proposal = {
            "id": rule_id,
            "condition": condition,
            "description": description,
            "status": "pending_approval"
        }
        
        # Verifica se já existe
        if any(r['id'] == rule_id for r in rules["proposed_rules"]):
            return f"💡 A regra '{rule_id}' já está na fila de aprendizado para sua aprovação."
            
        rules["proposed_rules"].append(new_proposal)
        
        with open(RULES_PATH, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=4)
            
        return f"🧠 **Novo Aprendizado:** Detectei um padrão e propus a regra `{rule_id}`.\n" + \
               f"_{description}_\n\n" + \
               "Deseja aprovar este aprendizado para as próximas análises?"

    except Exception as e:
        return f"Erro ao processar aprendizado: {str(e)}"

def approve_rule(rule_id: str) -> str:
    """Move uma regra da fila de proposta para a produção."""
    try:
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            rules = json.load(f)
            
        proposal = next((r for r in rules.get("proposed_rules", []) if r['id'] == rule_id), None)
        
        if not proposal:
            return "❌ Proposta não encontrada."
            
        # Move para mapping_rules
        rules["mapping_rules"].append({
            "id": proposal["id"],
            "condition": proposal["condition"],
            "description": proposal["description"]
        })
        
        # Remove da fila
        rules["proposed_rules"] = [r for r in rules["proposed_rules"] if r['id'] != rule_id]
        
        with open(RULES_PATH, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=4)
            
        return f"✅ **Unanimidade Confirmada:** A regra `{rule_id}` agora faz parte do meu DNA oficial."
        
    except Exception as e:
        return f"Erro ao aprovar regra: {str(e)}"
