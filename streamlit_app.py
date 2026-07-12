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

# 2. SISTEMA DE BANCO DE DADOS (Persistência em JSON)
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
        "caixa_entrada": {
            "Cozinha e Nutrição": [], "Comunicação": [], "Captação de Recursos": [], 
            "Pedagógico": [], "Financeiro": [], "Apadrinhamento": []
        }
    }

def salvar_banco():
    dados = {
        "usuarios": st.session_state.usuarios,
        "nucleos_dados": st.session_state.nucleos_dados,
        "caixa_entrada": st.session_state.caixa_entrada
    }
    with open(ARQUIVO_BANCO, "w") as f:
        json.dump(dados, f)

# Inicializa estados carregando do JSON
if "dados_carregados" not in st.session_state:
    dados = carregar_banco()
    st.session_state.usuarios = dados["usuarios"]
    st.session_state.nucleos_dados = dados["nucleos_dados"]
    st.session_state.caixa_entrada = dados["caixa_entrada"]
    st.session_state.dados_carregados = True

if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "modo_tela" not in st.session_state: st.session_state.modo_tela = "login"
if "nucleo_selecionado" not in st.session_state: st.session_state.nucleo_selecionado = "Comunicação"

# 3. FUNÇÃO PARA CARREGAR IMAGEM DE FUNDO NO LOGIN
def set_background(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.8)), url(data:image/jpeg;base64,{encoded_string});
                background-size: cover; background-position: center; background-attachment: fixed;
            }}
            header {{visibility: hidden;}}
            </style>
            """, unsafe_allow_html=True)

# ==========================================
# ÁREA PÚBLICA (LOGIN COMPACTO E BRANCO)
# ==========================================
if st.session_state.usuario_logado is None:
    set_background("IMG_3987.JPG") 

    # CSS Específico para forçar o texto branco e layout compacto no card
    st.markdown("""
        <style>
        .login-container { margin-top: -30px; }
        .stTextInput>div>div>input { 
            background-color: rgba(255, 255, 255, 0.1) !important; 
            border: 1px solid rgba(255,255,255,0.4) !important; 
            color: white !important; 
        }
        .stSelectbox>div>div>div { background-color: rgba(255, 255, 255, 0.1) !important; color: white !important; }
        p, span, label, h2, h4 { color: white !important; }
        .stButton>button { border-radius: 12px; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.2, 1, 1.2])
    
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.write("") # Margem mínima
        
        caminho_logo = "Logotipo Principal 01 (1).png"
        if os.path.exists(caminho_logo):
            st.image(caminho_logo, use_container_width=True)
        else:
            st.markdown("<h2 style='text-align:center;'>Mãe Lalu</h2>", unsafe_allow_html=True)
        
        if st.session_state.modo_tela == "login":
            st.markdown("<h4 style='text-align:center; font-size:18px;'>Acesso ao Hub</h4>", unsafe_allow_html=True)
            usuario_login = st.text_input("Seu Nome:")
            senha_login = st.text_input("Senha:", type="password")
            
            if st.button("Entrar", use_container_width=True):
                if usuario_login in st.session_state.usuarios:
                    if st.session_state.usuarios[usuario_login]["senha"] == senha_login:
                        st.session_state.usuario_logado = st.session_state.usuarios[usuario_login]
                        st.session_state.nucleo_selecionado = st.session_state.usuarios[usuario_login]["nucleo"]
                        st.rerun()
                    else: st.error("Senha incorreta.")
                else: st.error("Usuário não encontrado.")
            
            st.markdown("<p style='text-align:center; font-size:12px; margin-top:10px;'>Ainda não tem acesso?</p>", unsafe_allow_html=True)
            if st.button("Criar nova conta", use_container_width=True):
                st.session_state.modo_tela = "cadastro"
                st.rerun()

        else:
            st.markdown("<h4 style='text-align:center; font-size:18px;'>Novo Cadastro</h4>", unsafe_allow_html=True)
            novo_nome = st.text_input("Nome Completo:")
            novo_nucleo = st.selectbox("Seu Núcleo:", list(st.session_state.nucleos_dados.keys()))
            nova_senha = st.text_input("Crie uma Senha:", type="password")
            
            if st.button("Finalizar Cadastro", use_container_width=True):
                if novo_nome.strip() and nova_senha.strip():
                    if novo_nome in st.session_state.usuarios:
                        st.warning("Usuário já existe.")
                    else:
                        st.session_state.usuarios[novo_nome] = {"nome": novo_nome, "nucleo": novo_nucleo, "senha": nova_senha}
                        salvar_banco() # Salva no JSON imediatamente
                        st.success("Cadastro realizado!")
                        st.session_state.modo_tela = "login"
                        st.rerun()
                else: st.error("Preencha tudo.")

            if st.button("Voltar", use_container_width=True):
                st.session_state.modo_tela = "login"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# ÁREA PRIVADA (ESTÉTICA MINIMALISTA)
# ==========================================
else:
    st.markdown("""
        <style>
        .stApp { background: #fafafa !important; }
        header {visibility: visible;}
        h1 { font-weight: 600 !important; font-family: -apple-system, BlinkMacSystemFont, sans-serif !important; color: #1d1d1f !important; }
        h2, h3, h4, p, span { color: #1d1d1f !important; font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;}
        
        /* Estilo dos Botões da Árvore de Navegação */
        div.stButton > button:first-child {
            background-color: transparent; border: none; box-shadow: none; padding: 10px;
            color: #1d1d1f !important; border-radius: 15px; transition: 0.2s;
        }
        div.stButton > button:first-child:hover { background-color: rgba(0,0,0,0.05); }
        div.stButton > button:first-child p { font-size: 13px !important; margin: 0; font-weight: 500;}
        
        /* Cards Estilo Apple para o Feed */
        .apple-card {
            background: #ffffff; border-radius: 20px; padding: 25px; margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
            border: 1px solid rgba(0,0,0,0.02);
        }
        .card-tag { font-size: 11px; font-weight: 700; color: #59c2d1; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 5px;}
        .card-title { font-size: 18px; font-weight: 600; margin-bottom: 10px;}
        .card-text { font-size: 14px; color: #515154; line-height: 1.5;}
        </style>
    """, unsafe_allow_html=True)

    # CABEÇALHO / LOGOUT
    col_topo1, col_topo2 = st.columns([8, 2])
    with col_topo1: st.title("Hub Operacional")
    with col_topo2:
        st.write("")
        if st.button("Sair"):
            st.session_state.usuario_logado = None
            st.rerun()

    st.markdown("<p style='font-size: 22px; font-weight: 500; margin-top: -15px; color: #86868b !important;'>Organograma Interativo.</p>", unsafe_allow_html=True)

    def set_nucleo(n): st.session_state.nucleo_selecionado = n

    # ÁRVORE GENEALÓGICA / MENU ESTILO APPLE ICONS
    st.write("")
    
    # Nível 1 - Central (Logo)
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        if os.path.exists("Logotipo Principal 01 (1).png"):
            st.image("Logotipo Principal 01 (1).png", use_container_width=True)
    st.write("")

    # Nível 2 - Núcleos (Ícones Grandes + Texto Embaixo)
    # A quebra de linha \n no botão gera o visual de ícone em cima e texto embaixo
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("🍳\nCozinha", use_container_width=True): set_nucleo("Cozinha e Nutrição")
    with col2:
        if st.button("📣\nComunicação", use_container_width=True): set_nucleo("Comunicação")
    with col3:
        if st.button("📚\nPedagógico", use_container_width=True): set_nucleo("Pedagógico")
    with col4:
        if st.button("🤝\nCaptação", use_container_width=True): set_nucleo("Captação de Recursos")
    with col5:
        if st.button("💰\nFinanceiro", use_container_width=True): set_nucleo("Financeiro")
    with col6:
        if st.button("💌\nApadrinhamento", use_container_width=True): set_nucleo("Apadrinhamento")

    st.divider()

    n_sel = st.session_state.nucleo_selecionado
    st.markdown(f"<h2 style='font-size: 32px;'>{n_sel}</h2>", unsafe_allow_html=True)

    aba_feed, aba_tarefas, aba_solicitacoes = st.tabs(["As novidades", "Demandas", "Solicitações"])

    # ABA 1: FEED ESTILO CARDS
    with aba_feed:
        if st.session_state.usuario_logado['nucleo'] == n_sel:
            with st.form("form_novo"):
                texto = st.text_area("Compartilhar algo novo:")
                if st.form_submit_button("Publicar") and texto.strip():
                    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    autor = st.session_state.usuario_logado['nome']
                    st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {"texto": texto, "data": agora, "autor": autor})
                    salvar_banco()
                    st.rerun()
        
        st.write("<br>", unsafe_allow_html=True)
        col_c1, col_c2, col_c3 = st.columns(3)
        posts = st.session_state.nucleos_dados[n_sel]["atualizacoes"]
        
        # Distribui os posts em 3 colunas simulando os produtos da Apple
        for i, p in enumerate(posts):
            col = [col_c1, col_c2, col_c3][i % 3]
            with col:
                st.markdown(f"""
                <div class='apple-card'>
                    <div class='card-tag'>NOVO</div>
                    <div class='card-title'>{p['autor']}</div>
                    <div class='card-text'>{p['texto']}</div>
                    <div style='font-size: 10px; color: #86868b; margin-top: 15px;'>{p['data']}</div>
                </div>
                """, unsafe_allow_html=True)

    # ABA 2: TAREFAS E LINKS
    with aba_tarefas:
        c_link1, c_link2 = st.columns(2)
        c_link1.link_button("📂 Acessar Drive", st.session_state.nucleos_dados[n_sel]["drive"])
        c_link2.link_button("📊 Cronogramas", st.session_state.nucleos_dados[n_sel]["planilha"])
        st.divider()
        
        if st.session_state.usuario_logado['nucleo'] == n_sel:
            nova_tarefa = st.text_input("Adicionar demanda:", key="add_t")
            if st.button("Salvar Tarefa"):
                st.session_state.nucleos_dados[n_sel]["tarefas"].append(nova_tarefa)
                salvar_banco()
                st.rerun()
                    
        for t in st.session_state.nucleos_dados[n_sel]["tarefas"]:
            st.checkbox(t, key=f"check_{t}")

    # ABA 3: SOLICITAÇÕES
    with aba_solicitacoes:
        with st.form("form_sol"):
            dest = st.selectbox("Para qual núcleo?", list(st.session_state.nucleos_dados.keys()))
            assunto = st.text_input("Assunto:")
            msg = st.text_area("Mensagem:")
            if st.form_submit_button("Enviar") and assunto.strip():
                agora = datetime.datetime.now().strftime("%d/%m/%Y")
                remetente = st.session_state.usuario_logado['nome']
                st.session_state.caixa_entrada[dest].append({"assunto": assunto, "mensagem": msg, "data": agora, "de": remetente})
                salvar_banco()
                st.success("Enviado com sucesso!")

        st.write("### Caixa de Entrada")
        if st.session_state.usuario_logado['nucleo'] == n_sel:
            for m in reversed(st.session_state.caixa_entrada[n_sel]):
                with st.expander(f"📩 {m['assunto']} (De: {m['de']})"):
                    st.write(m['mensagem'])
        else:
            st.error("🔒 Restrito aos membros deste núcleo.")
