import streamlit as st
import datetime
import os
import json
import base64

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Instituto Mãe Lalu",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. SISTEMA DE BANCO DE DADOS
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
    dados = {
        "usuarios": st.session_state.usuarios,
        "nucleos_dados": st.session_state.nucleos_dados,
        "caixa_entrada": st.session_state.caixa_entrada
    }
    with open(ARQUIVO_BANCO, "w") as f:
        json.dump(dados, f)

# Inicialização de estado
if "dados_carregados" not in st.session_state:
    dados = carregar_banco()
    st.session_state.usuarios = dados["usuarios"]
    st.session_state.nucleos_dados = dados["nucleos_dados"]
    st.session_state.caixa_entrada = dados["caixa_entrada"]
    st.session_state.dados_carregados = True

if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "modo_tela" not in st.session_state: st.session_state.modo_tela = "login"
if "nucleo_selecionado" not in st.session_state: st.session_state.nucleo_selecionado = "Comunicação"

# FUNÇÃO BACKGROUND LOGIN
def set_background(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            .stApp {{ background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.8)), url(data:image/jpeg;base64,{encoded_string});
            background-size: cover; background-position: center; background-attachment: fixed; }}
            header {{visibility: hidden;}}
            </style>
        """, unsafe_allow_html=True)

# CSS GERAL E APPLE STYLE
st.markdown("""
    <style>
    /* Estilo Geral Apple */
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600&display=swap');
    * { font-family: -apple-system, BlinkMacSystemFont, sans-serif !important; }
    
    .stApp { background: #fafafa !important; }
    
    /* Logo no canto superior */
    .logo-header { position: fixed; top: 15px; left: 20px; z-index: 1000; font-weight: 600; color: #1d1d1f; font-size: 18px; }
    
    /* Cards */
    .apple-card { background: #ffffff; border-radius: 20px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); border: 1px solid rgba(0,0,0,0.02); }
    .card-tag { font-size: 11px; font-weight: 700; color: #59c2d1; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 5px;}
    .card-title { font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #1d1d1f;}
    .card-text { font-size: 14px; color: #515154; line-height: 1.5;}

    /* Inputs Login */
    .stTextInput>div>div>input { background-color: #ffffff !important; border-radius: 12px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ÁREA PÚBLICA (LOGIN)
# ==========================================
if st.session_state.usuario_logado is None:
    set_background("IMG_3987.JPG")
    
    col1, col2, col3 = st.columns([1.2, 1, 1.2])
    with col2:
        caminho_logo = "Logotipo Principal 01 (1).png"
        if os.path.exists(caminho_logo): st.image(caminho_logo, use_container_width=True)
        
        if st.session_state.modo_tela == "login":
            st.markdown("<h4 style='text-align:center; color:white;'>Acesso ao sistema IMLA</h4>", unsafe_allow_html=True)
            email = st.text_input("Email:")
            senha = st.text_input("Senha:", type="password")
            if st.button("Entrar", use_container_width=True):
                user = st.session_state.usuarios.get(email)
                if user and user.get("senha") == senha:
                    st.session_state.usuario_logado = user
                    st.session_state.nucleo_selecionado = user.get("nucleo")
                    st.rerun()
                else: st.error("Email ou senha incorretos.")
            if st.button("Criar nova conta", use_container_width=True):
                st.session_state.modo_tela = "cadastro"
                st.rerun()
        else:
            st.markdown("<h4 style='text-align:center; color:white;'>Novo Cadastro</h4>", unsafe_allow_html=True)
            n_mail = st.text_input("Email:")
            n_nuc = st.selectbox("Seu Núcleo:", list(st.session_state.nucleos_dados.keys()))
            n_pas = st.text_input("Senha:", type="password")
            if st.button("Finalizar", use_container_width=True):
                st.session_state.usuarios[n_mail] = {"email": n_mail, "nucleo": n_nuc, "senha": n_pas}
                salvar_banco()
                st.session_state.modo_tela = "login"
                st.rerun()

# ==========================================
# ÁREA PRIVADA (SISTEMA)
# ==========================================
else:
    # Logo discreta no topo
    st.markdown("<div class='logo-header'>IMLA</div>", unsafe_allow_html=True)
    
    # Header
    col_topo1, col_topo2 = st.columns([8, 2])
    with col_topo1: st.title("Hub Operacional")
    with col_topo2:
        if st.button("Sair"):
            st.session_state.usuario_logado = None
            st.rerun()

    st.markdown("<p style='font-size: 22px; font-weight: 500; margin-top: -15px; color: #86868b !important;'>Escolha e clique.</p>", unsafe_allow_html=True)

    # Organograma
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    botoes = [("🍳", "Cozinha"), ("📣", "Comunicação"), ("📚", "Pedagógico"), ("🤝", "Captação"), ("💰", "Financeiro"), ("💌", "Apadrinhamento")]
    nucleos_map = ["Cozinha e Nutrição", "Comunicação", "Pedagógico", "Captação de Recursos", "Financeiro", "Apadrinhamento"]
    
    for i, col in enumerate([col1, col2, col3, col4, col5, col6]):
        with col:
            if st.button(f"{botoes[i][0]}\n{botoes[i][1]}", use_container_width=True):
                st.session_state.nucleo_selecionado = nucleos_map[i]
                st.rerun()

    st.divider()

    n_sel = st.session_state.nucleo_selecionado
    st.markdown(f"<h2 style='font-size: 32px;'>{n_sel}</h2>", unsafe_allow_html=True)

    aba_feed, aba_tarefas, aba_solicitacoes = st.tabs(["As novidades", "Demandas", "Solicitações"])

    with aba_feed:
        if st.session_state.usuario_logado.get('nucleo') == n_sel:
            with st.form("form_novo", clear_on_submit=True):
                texto = st.text_area("Compartilhar algo novo:")
                if st.form_submit_button("Publicar") and texto.strip():
                    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {"texto": texto, "data": agora, "autor": st.session_state.usuario_logado.get('email')})
                    salvar_banco()
                    st.rerun()
        
        posts = st.session_state.nucleos_dados[n_sel].get("atualizacoes", [])
        for p in posts:
            st.markdown(f"""
            <div class='apple-card'>
                <div class='card-tag'>NOVO</div>
                <div class='card-title'>{p.get('autor')}</div>
                <div class='card-text'>{p.get('texto')}</div>
                <div style='font-size: 10px; color: #86868b; margin-top: 15px;'>{p.get('data')}</div>
            </div>
            """, unsafe_allow_html=True)

    with aba_tarefas:
        c_link1, c_link2 = st.columns(2)
        c_link1.link_button("📂 Acessar Drive", st.session_state.nucleos_dados[n_sel].get("drive", "#"))
        c_link2.link_button("📊 Cronogramas", st.session_state.nucleos_dados[n_sel].get("planilha", "#"))
        st.divider()
        
        if st.session_state.usuario_logado.get('nucleo') == n_sel:
            nova_t = st.text_input("Adicionar demanda:", key="add_t")
            if st.button("Salvar Tarefa"):
                st.session_state.nucleos_dados[n_sel]["tarefas"].append(nova_t)
                salvar_banco()
                st.rerun()
                    
        for t in st.session_state.nucleos_dados[n_sel].get("tarefas", []):
            st.checkbox(t, key=f"check_{t}")

    with aba_solicitacoes:
        with st.form("form_sol", clear_on_submit=True):
            dest = st.selectbox("Para qual núcleo?", list(st.session_state.nucleos_dados.keys()))
            assunto = st.text_input("Assunto:")
            msg = st.text_area("Mensagem:")
            if st.form_submit_button("Enviar") and assunto.strip():
                st.session_state.caixa_entrada[dest].append({"assunto": assunto, "mensagem": msg, "data": datetime.datetime.now().strftime("%d/%m/%Y"), "de": st.session_state.usuario_logado.get('email')})
                salvar_banco()
                st.success("Enviado!")

        st.write("### Caixa de Entrada")
        if st.session_state.usuario_logado.get('nucleo') == n_sel:
            for m in reversed(st.session_state.caixa_entrada.get(n_sel, [])):
                with st.expander(f"📩 {m.get('assunto')} (De: {m.get('de')})"):
                    st.write(m.get('mensagem'))
        else:
            st.error("🔒 Restrito aos membros deste núcleo.")
