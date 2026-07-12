import streamlit as st
import os

st.set_page_config(
    page_title="Instituto Mãe Lalu - Painel Interno",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cores da identidade visual: Turquesa (#59c2d1) e Verde (#92c83e)
st.markdown(f"""
    <style>
    div.stButton > button:first-child {{
        background-color: #92c83e;
        color: white;
        border-radius: 8px;
        border: none;
    }}
    div.stButton > button:first-child:hover {{
        background-color: #59c2d1;
        color: white;
    }}
    a {{ color: #59c2d1 !important; }}
    [data-testid="stSidebar"] {{
        background-color: #f7fbfb;
    }}
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("Instituto Mãe Lalu")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Navegação")

st.title("Hub Operacional - Instituto Mãe Lalu")
st.write("Bem-vindo ao nosso sistema interno integrado.")

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("<div style='background-color: #eef9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #59c2d1;'><h4>🔧 Manutenção</h4><p style='font-size: 24px; font-weight: bold;'>3 Pendentes</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div style='background-color: #f4faf0; padding: 20px; border-radius: 10px; border-left: 5px solid #92c83e;'><h4>📣 Comunicação</h4><p style='font-size: 24px; font-weight: bold;'>Acessar Tarefas</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown("<div style='background-color: #eef9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #59c2d1;'><h4>📑 Editais</h4><p style='font-size: 24px; font-weight: bold;'>2 em Andamento</p></div>", unsafe_allow_html=True)
