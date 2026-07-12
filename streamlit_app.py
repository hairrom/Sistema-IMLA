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
        "nucleos_dados": {
            "Cozinha e Nutrição": {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
            "Comunicação": {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
            "Captação de Recursos": {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
            "Pedagógico": {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
            "Financeiro": {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
            "Apadrinhamento": {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"}
        },
        "caixa_entrada": {n: [] for n in ["Cozinha e Nutrição", "Comunicação", "Captação de Recursos", "Pedagógico", "Financeiro", "Apadrinhamento"]}
    }

def salvar_banco():
    with open(ARQUIVO_BANCO, "w") as f:
        json.dump({
            "usuarios": st.session_state.usuarios,
            "nucleos_dados": st.session_state.nucleos_dados,
            "caixa_entrada": st.session_state.caixa_entrada
        }, f)

# INICIALIZAÇÃO
if "dados_carregados" not in st.session_state:
    dados = carregar_banco()
    st.session_state.usuarios = dados["usuarios"]
    st.session_state.nucleos_dados = dados["nucleos_dados"]
    st.session_state.caixa_entrada = dados["caixa_entrada"]
    st.session_state.dados_carregados = True

if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "modo_tela" not in st.session_state: st.session_state.modo_tela = "login"
if "nucleo_selecionado" not in st.session_state: st.session_state.nucleo_selecionado = "Comunicação"

# CSS ESTILO APPLE
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600&display=swap');
    * { font-family: -apple-system, BlinkMacSystemFont, sans-serif !important; }
    
    /* Ilha Flutuante */
    .floating-nav {
        position: sticky; top: 10px; z-index: 1000;
        background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.3); border-radius: 50px;
        padding: 15px 30px; display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    }
    
    /* Banner */
    .banner-container { border-radius: 25px; overflow: hidden; margin-bottom: 30px; }
    
    .apple-card { background: #ffffff; border-radius: 25px; padding: 25px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# LÓGICA DE LOGIN
if st.session_state.usuario_logado is None:
    # Fundo Login
    if os.path.exists("IMG_3987.JPG"):
        with open("IMG_3987.JPG", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f"<style>.stApp {{background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.7)), url(data:image/jpeg;base64,{b64}); background-size: cover;}}</style>", unsafe_allow_html=True)
    
    col_c = st.columns([1, 0.8, 1])
    with col_c[1]:
        st.markdown("<h1 style='color:white; text-align:center;'>Sistema IMLA</h1>", unsafe_allow_html=True)
        
        if st.session_state.modo_tela == "login":
            email = st.text_input("Seu melhor e-mail:")
            senha = st.text_input("Senha:", type="password")
            if st.button("Entrar", use_container_width=True):
                user = st.session_state.usuarios.get(email)
                if user and user.get("senha") == senha:
                    st.session_state.usuario_logado = user
                    st.rerun()
                else: st.error("Credenciais incorretas.")
            if st.button("Criar conta"): st.session_state.modo_tela = "cadastro"; st.rerun()
        
        else: # TELA CADASTRO
            nome = st.text_input("Nome Completo:")
            email = st.text_input("Seu melhor e-mail:")
            nucleo = st.selectbox("Núcleo que pertence:", list(st.session_state.nucleos_dados.keys()))
            senha = st.text_input("Senha:", type="password")
            conf_senha = st.text_input("Confirme sua senha:", type="password")
            
            if st.button("Finalizar Cadastro"):
                if senha == conf_senha:
                    st.session_state.usuarios[email] = {"nome": nome, "email": email, "nucleo": nucleo, "senha": senha}
                    salvar_banco()
                    st.session_state.modo_tela = "login"
                    st.rerun()
                else: st.error("As senhas não coincidem.")
            if st.button("Voltar"): st.session_state.modo_tela = "login"; st.rerun()

# ÁREA PRIVADA
else:
    # Banner
    if os.path.exists("IMG_3985.JPG"):
        st.markdown("<div class='banner-container'>", unsafe_allow_html=True)
        st.image("IMG_3985.JPG", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Ilha Flutuante
    st.markdown("""<div class='floating-nav'>
        <div style='font-weight:bold; font-size: 20px;'>IMLA</div>
        <div style='display:flex; gap:20px;'><span>Pesquisar</span><span>Núcleos</span></div>
    </div>""", unsafe_allow_html=True)

    st.title("Hub Operacional")
    
    n_sel = st.session_state.nucleo_selecionado
    col_nav = st.columns(6)
    nucleos = ["Cozinha e Nutrição", "Comunicação", "Captação de Recursos", "Pedagógico", "Financeiro", "Apadrinhamento"]
    
    for i, col in enumerate(col_nav):
        with col:
            if st.button(nucleos[i], use_container_width=True):
                st.session_state.nucleo_selecionado = nucleos[i]
                st.rerun()

    st.divider()
    st.subheader(f"Área: {n_sel}")

    aba_feed, aba_tarefas, aba_solicitacoes = st.tabs(["Feed", "Demandas", "Solicitações"])

    with aba_feed:
        if st.session_state.usuario_logado['nucleo'] == n_sel:
            with st.form("pub", clear_on_submit=True):
                msg = st.text_area("O que está acontecendo?")
                if st.form_submit_button("Publicar"):
                    st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {
                        "texto": msg, 
                        "autor": st.session_state.usuario_logado['nome'], 
                        "data": datetime.datetime.now().strftime("%d/%m")
                    })
                    salvar_banco()
                    st.rerun()
        
        for p in st.session_state.nucleos_dados[n_sel].get("atualizacoes", []):
            st.markdown(f"""<div class='apple-card'>
                <div style='font-weight:600;'>{p['autor']}</div>
                <div style='color:#515154;'>{p['texto']}</div>
                <div style='font-size:10px; color:#86868b;'>{p['data']}</div>
            </div>""", unsafe_allow_html=True)

    with aba_tarefas:
        # Lógica de tarefas igual a anterior...
        st.link_button("📂 Drive", st.session_state.nucleos_dados[n_sel].get("drive", "#"))
        st.write("Demandas do núcleo...")

    with aba_solicitacoes:
        st.write("Caixa de entrada...")
