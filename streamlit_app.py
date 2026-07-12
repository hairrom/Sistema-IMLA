import streamlit as st
import datetime
import os
import json
import base64

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sistema IMLA", page_icon="🕊️", layout="wide")

# ARQUIVO DE BANCO DE DADOS
ARQUIVO_BANCO = "banco_iml.json"

def carregar_banco():
    if os.path.exists(ARQUIVO_BANCO):
        with open(ARQUIVO_BANCO, "r") as f:
            return json.load(f)
    return {
        "usuarios": {},
        "nucleos_dados": {n: {"atualizacoes": [], "tarefas": {"fazer": [], "progresso": [], "concluido": []}} 
                          for n in ["Cozinha e Nutrição", "Comunicação", "Captação de Recursos", "Pedagógico", "Financeiro", "Apadrinhamento"]}
    }

def salvar_banco():
    with open(ARQUIVO_BANCO, "w") as f:
        json.dump({"usuarios": st.session_state.usuarios, "nucleos_dados": st.session_state.nucleos_dados}, f)

# INICIALIZAÇÃO DE ESTADO
if "dados_iniciados" not in st.session_state:
    dados = carregar_banco()
    st.session_state.usuarios = dados["usuarios"]
    st.session_state.nucleos_dados = dados["nucleos_dados"]
    st.session_state.usuario_logado = None
    st.session_state.modo = "login"
    st.session_state.nucleo_selecionado = "Cozinha e Nutrição"
    st.session_state.dados_iniciados = True

# CSS ESTILO APPLE
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600&display=swap');
    * { font-family: -apple-system, BlinkMacSystemFont, sans-serif !important; }
    
    .top-nav {
        position: fixed; top: 0; left: 0; width: 100%; height: 60px;
        background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(20px);
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 30px; z-index: 1000; border-bottom: 1px solid rgba(0,0,0,0.1);
    }
    .banner { width: 100%; height: 200px; object-fit: cover; border-radius: 20px; margin-top: 70px; }
    .kanban-col { background: #f5f5f7; padding: 15px; border-radius: 15px; min-height: 300px; }
    .card { background: white; padding: 15px; border-radius: 10px; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# FLUXO DE LOGIN/CADASTRO
if st.session_state.usuario_logado is None:
    if st.session_state.modo == "login":
        st.title("Sistema IMLA")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            user = st.session_state.usuarios.get(email)
            if user and user['senha'] == senha:
                st.session_state.usuario_logado = user
                st.rerun()
        if st.button("Criar conta"): st.session_state.modo = "cadastro"; st.rerun()
    else:
        st.title("Cadastro")
        nome = st.text_input("Nome Completo")
        email = st.text_input("Seu melhor email")
        nucleo = st.selectbox("Núcleo que pertence", list(st.session_state.nucleos_dados.keys()))
        senha = st.text_input("Senha", type="password")
        conf = st.text_input("Confirmação de senha", type="password")
        if st.button("Finalizar"):
            if senha == conf:
                st.session_state.usuarios[email] = {"nome": nome, "email": email, "nucleo": nucleo, "senha": senha}
                salvar_banco()
                st.session_state.modo = "login"; st.rerun()
            else: st.error("Senhas não coincidem")
        if st.button("Voltar"): st.session_state.modo = "login"; st.rerun()

# SISTEMA INTERNO
else:
    # BARRA SUPERIOR
    with st.container():
        st.markdown('<div class="top-nav">', unsafe_allow_html=True)
        cols = st.columns([1, 6, 2])
        with cols[0]: st.write("### IMLA")
        with cols[1]:
            nav_cols = st.columns(len(st.session_state.nucleos_dados))
            for i, n in enumerate(st.session_state.nucleos_dados.keys()):
                if nav_cols[i].button(n): st.session_state.nucleo_selecionado = n; st.rerun()
        with cols[2]:
            with st.popover(f"👤 {st.session_state.usuario_logado['nome']}"):
                st.write(f"Núcleo: {st.session_state.usuario_logado['nucleo']}")
                if st.button("Sair"): st.session_state.usuario_logado = None; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # BANNER
    st.image("IMG_3985.JPG", use_container_width=True) # Certifique-se que o arquivo existe
    
    st.title(f"Área: {st.session_state.nucleo_selecionado}")
    
    # ABAS
    tab1, tab2, tab3 = st.tabs(["Feed", "Tarefas (Kanban)", "Solicitações"])
    
    with tab1:
        st.write("Atualizações recentes...")
        
    with tab2:
        # Acesso apenas para quem é do núcleo
        if st.session_state.usuario_logado['nucleo'] == st.session_state.nucleo_selecionado:
            nova = st.text_input("Criar nova tarefa")
            if st.button("Adicionar"):
                st.session_state.nucleos_dados[st.session_state.nucleo_selecionado]['tarefas']['fazer'].append(nova)
                salvar_banco()
        
        # COLUNAS KANBAN
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("### A Fazer")
            for t in st.session_state.nucleos_dados[st.session_state.nucleo_selecionado]['tarefas']['fazer']:
                st.markdown(f'<div class="card">{t}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown("### Em Progresso")
        with c3:
            st.markdown("### Concluído")

    with tab3:
        st.write("Caixa de entrada de solicitações...")
