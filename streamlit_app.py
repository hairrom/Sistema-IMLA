import streamlit as st

st.set_page_config(
    page_title="Instituto Mãe Lalu - Painel Interno",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização com cores da identidade (Turquesa #59c2d1 e Verde #92c83e) e correção de contraste
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #92c83e;
        color: white;
        border-radius: 8px;
        border: none;
    }
    div.stButton > button:first-child:hover {
        background-color: #59c2d1;
        color: white;
    }
    a { color: #59c2d1 !important; }
    
    /* Cores dos cards com texto escuro fixo */
    .card-manutencao { background-color: #eef9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #59c2d1; color: #1c4e56; }
    .card-comunicacao { background-color: #f4faf0; padding: 20px; border-radius: 10px; border-left: 5px solid #92c83e; color: #3b5912; }
    .card-editais { background-color: #eef9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #59c2d1; color: #1c4e56; }
    </style>
""", unsafe_allow_html=True)

st.title("Hub Operacional - Instituto Mãe Lalu")
st.write("Bem-vindo ao nosso sistema interno integrado. Use o menu lateral para navegar entre os setores.")

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("<div class='card-manutencao'><h4 style='margin:0; color:#1c4e56;'>🔧 Manutenção</h4><p style='font-size: 24px; font-weight: bold; margin:10px 0 0 0;'>3 Atividades</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div class='card-comunicacao'><h4 style='margin:0; color:#3b5912;'>📣 Comunicação</h4><p style='font-size: 24px; font-weight: bold; margin:10px 0 0 0;'>Acessar Drive e Tarefas</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown("<div class='card-editais'><h4 style='margin:0; color:#1c4e56;'>📑 Editais</h4><p style='font-size: 24px; font-weight: bold; margin:10px 0 0 0;'>2 em Andamento</p></div>", unsafe_allow_html=True)
