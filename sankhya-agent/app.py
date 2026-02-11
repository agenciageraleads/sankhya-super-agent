import streamlit as st
import logging
import json
import plotly.io as pio
import os
import subprocess
from agent_client import run_conversation

# Configuração da página
st.set_page_config(
    page_title="Sankhya Super Agent",
    page_icon="🤖",
    layout="wide"
)

# Inicializa sessão de chat se não existir
if "messages" not in st.session_state:
    st.session_state.messages = []

def render_assistant_response(content):
    """Renderiza a resposta, detectando e plotando gráficos se presentes."""
    # Procura por blocos de código com marcação de gráfico ou JSON puro
    chunks = content.split("```")
    for chunk in chunks:
        chunk = chunk.strip()
        if chunk.startswith("json-chart"):
            try:
                # Remove a tag 'json-chart' e converte para dict
                chart_data = json.loads(chunk.replace("json-chart", "").strip())
                st.plotly_chart(chart_data, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao renderizar gráfico: {str(e)}")
        elif chunk.startswith("plotly"):
             # Suporte a Plotly JSON direto
             try:
                chart_json = chunk.replace("plotly", "").strip()
                fig = pio.from_json(chart_json)
                st.plotly_chart(fig, use_container_width=True)
             except:
                 st.code(chunk)
        else:
            st.markdown(chunk)

# Título e Sidebar
st.title("🤖 Sankhya Super Agent (SSA)")
st.caption("Assistente Inteligente para ERP Sankhya - Portal Distribuidora")

with st.sidebar:
    st.header("🕵️ Monitoramento Ativo")
    
    # Exibição de Alertas Proativos do Background Worker
    ALERTS_PATH = "knowledge/active_alerts.json"
    if os.path.exists(ALERTS_PATH):
        try:
            with open(ALERTS_PATH, "r", encoding="utf-8") as f:
                alert_data = json.load(f)
            st.success(f"Última varredura: {alert_data['last_run']}")
            st.markdown(alert_data['report'])
        except:
            st.info("Aguardando primeiros alertas...")
    else:
        st.info("Vigia em standby. Use os Watchers para iniciar.")

    st.divider()
    st.header("🧠 Aprendizado do SSA")
    
    # Notificação de Regras Propostas
    RULES_PATH = "knowledge/business_rules.json"
    if os.path.exists(RULES_PATH):
        try:
            with open(RULES_PATH, "r", encoding="utf-8") as f:
                rules = json.load(f)
            proposals = rules.get("proposed_rules", [])
            if proposals:
                st.warning(f"🔔 {len(proposals)} novo(s) aprendizado(s) pendente(s)!")
                if st.button("Ver Aprendizados"):
                    st.session_state.messages.append({"role": "user", "content": "Quais são as novas regras que você aprendeu e precisa que eu aprove?"})
                    st.rerun()
            else:
                st.success("Cérebro atualizado!")
        except:
            pass
            
    st.divider()
    st.header("Ferramentas")
    st.markdown("""
    - **📊 BI:** Gráficos de vendas e estoque
    - **👀 Watchers:** Alertas proativos
    - **🛠️ Factory:** Criação de agentes
    """)
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# Exibe histórico de mensagens da sessão
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                render_assistant_response(message["content"])
            else:
                st.markdown(message["content"])

# Input do usuário
if prompt := st.chat_input("Como posso ajudar com o Sankhya hoje?"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
        if m["role"] in ["user", "assistant"]
    ]

    with st.chat_message("assistant"):
        with st.spinner("Consultando inteligência Sankhya..."):
            try:
                response = run_conversation(api_messages)
                render_assistant_response(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Erro ao processar: {str(e)}")
