import streamlit as st
import datetime
import os
import base64

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Instituto Mãe Lalu",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="collapsed" # Esconde a barra lateral na tela de login
)

# 2. FUNÇÃO PARA CARREGAR IMAGEM DE FUNDO
def set_background(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.7)), url(data:image/jpeg;base64,{encoded_string});
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            /* Oculta o cabeçalho padrão do Streamlit na tela de login */
            header {{visibility: hidden;}}
            </style>
            """,
            unsafe_allow_html=True
        )

# 3. BANCO DE DADOS TEMPORÁRIO E ESTADOS
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {} # Dicionário para armazenar cadastros: { "nome_usuario": {"senha", "nucleo", "nome_completo"} }

if "nucleos_dados" not in st.session_state:
    st.session_state.nucleos_dados = {
        "Cozinha e Nutrição": {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Comunicação": {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Captação de Recursos": {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Pedagógico": {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Financeiro": {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Apadrinhamento": {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"}
    }

if "caixa_entrada" not in st.session_state:
    st.session_state.caixa_entrada = {nucleo: [] for nucleo in st.session_state.nucleos_dados.keys()}

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None
    
if "modo_tela" not in st.session_state:
    st.session_state.modo_tela = "login" # Pode ser "login" ou "cadastro"

# ==========================================
# ÁREA PÚBLICA (TELA DE LOGIN/CADASTRO ESTILO APPLE)
# ==========================================
if st.session_state.usuario_logado is None:
    # Aplica o fundo fotográfico apenas na tela de login
    # Nota: Certifique-se de que o nome do arquivo bate exatamente (diferencia maiúsculas e minúsculas)
    set_background("IMG_3987.JPG") 

    # Centraliza o conteúdo com colunas
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.write("")
        st.write("")
        st.write("")
        
        # Container principal estilo "Glassmorphism" / Cartão Branco
        st.markdown("""
            <style>
            .login-card {
                background-color: rgba(255, 255, 255, 0.95);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }
            .stTextInput>div>div>input { background-color: #f7fbfb !important; border: 1px solid #59c2d1 !important; color: #1c4e56 !important; }
            </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            # Logo
            caminho_logo = "Logotipo Principal 01 (1).png"
            if os.path.exists(caminho_logo):
                st.image(caminho_logo, use_container_width=True)
            else:
                st.markdown("<h2 style='text-align:center; color:#59c2d1;'>Mãe Lalu</h2>", unsafe_allow_html=True)
            
            st.divider()

            # TELA DE LOGIN
            if st.session_state.modo_tela == "login":
                st.markdown("<h4 style='text-align:center; color:#1c4e56;'>Acesso ao Hub</h4>", unsafe_allow_html=True)
                usuario_login = st.text_input("Usuário (Seu Nome):")
                senha_login = st.text_input("Senha:", type="password")
                
                if st.button("Entrar", use_container_width=True):
                    if usuario_login in st.session_state.usuarios:
                        if st.session_state.usuarios[usuario_login]["senha"] == senha_login:
                            st.session_state.usuario_logado = st.session_state.usuarios[usuario_login]
                            st.rerun()
                        else:
                            st.error("Senha incorreta.")
                    else:
                        st.error("Usuário não encontrado. Cadastre-se abaixo.")
                
                st.write("")
                st.markdown("<p style='text-align:center; color:#1c4e56;'>Ainda não tem acesso?</p>", unsafe_allow_html=True)
                if st.button("Criar nova conta", use_container_width=True):
                    st.session_state.modo_tela = "cadastro"
                    st.rerun()

            # TELA DE CADASTRO
            else:
                st.markdown("<h4 style='text-align:center; color:#1c4e56;'>Novo Cadastro</h4>", unsafe_allow_html=True)
                novo_nome = st.text_input("Nome Completo / Usuário:")
                novo_nucleo = st.selectbox("Selecione seu Núcleo:", list(st.session_state.nucleos_dados.keys()))
                nova_senha = st.text_input("Crie uma Senha:", type="password")
                
                if st.button("Finalizar Cadastro", use_container_width=True):
                    if novo_nome.strip() != "" and nova_senha.strip() != "":
                        if novo_nome in st.session_state.usuarios:
                            st.warning("Este nome de usuário já existe. Tente fazer login ou use um nome diferente.")
                        else:
                            # Salva o novo usuário
                            st.session_state.usuarios[novo_nome] = {
                                "nome": novo_nome,
                                "nucleo": novo_nucleo,
                                "senha": nova_senha
                            }
                            st.success("Cadastro realizado! Faça seu login.")
                            st.session_state.modo_tela = "login"
                            st.rerun()
                    else:
                        st.error("Preencha todos os campos.")

                st.write("")
                if st.button("Voltar para o Login", use_container_width=True):
                    st.session_state.modo_tela = "login"
                    st.rerun()


# ==========================================
# ÁREA PRIVADA (O SISTEMA COMPLETO)
# ==========================================
else:
    # Remove a imagem de fundo escura e volta para o tema branco/claro
    st.markdown("""
        <style>
        .stApp { background: #ffffff !important; }
        header {visibility: visible;}
        div.stButton > button:first-child {
            background-color: #ffffff; color: #59c2d1 !important; border-radius: 20px; border: 2px solid #59c2d1; font-weight: bold;
        }
        div.stButton > button:first-child:hover { background-color: #92c83e; color: #ffffff !important; border-color: #92c83e; }
        </style>
    """, unsafe_allow_html=True)

    # BARRA LATERAL (Agora que está logado)
    st.sidebar.title("🔐 Hub Operacional")
    st.sidebar.success(f"Logado como: {st.session_state.usuario_logado['nome']}")
    st.sidebar.info(f"Setor ativo: {st.session_state.usuario_logado['nucleo']}")
    if st.sidebar.button("Sair do Sistema"):
        st.session_state.usuario_logado = None
        st.session_state.modo_tela = "login"
        st.rerun()

    # MAPA MENTAL INTERATIVO (Restante do sistema que você já tinha)
    st.title("Hub Operacional - Instituto Mãe Lalu")
    st.divider()

    st.markdown("<h3 style='text-align: center;'>🗺️ Organograma Interativo</h3>", unsafe_allow_html=True)
    
    if "nucleo_selecionado" not in st.session_state:
        st.session_state.nucleo_selecionado = st.session_state.usuario_logado['nucleo']

    def definir_nucleo(nome):
        st.session_state.nucleo_selecionado = nome

    col_esq, col_centro, col_dir = st.columns([1.5, 2, 1.5], gap="large")

    with col_esq:
        st.write("") 
        if st.button("🍳 Cozinha e Nutrição", use_container_width=True): definir_nucleo("Cozinha e Nutrição")
        st.write("")
        if st.button("📣 Comunicação", use_container_width=True): definir_nucleo("Comunicação")
        st.write("")
        if st.button("📚 Pedagógico", use_container_width=True): definir_nucleo("Pedagógico")

    with col_centro:
        caminho_logo = "Logotipo Principal 01 (1).png"
        if os.path.exists(caminho_logo):
            st.image(caminho_logo, use_container_width=True)

    with col_dir:
        st.write("")
        if st.button("🤝 Captação de Recursos", use_container_width=True): definir_nucleo("Captação de Recursos")
        st.write("")
        if st.button("💰 Financeiro", use_container_width=True): definir_nucleo("Financeiro") 
        st.write("")
        if st.button("💌 Apadrinhamento", use_container_width=True): definir_nucleo("Apadrinhamento")

    st.divider()

    # PAINEL DO NÚCLEO SELECIONADO
    n_sel = st.session_state.nucleo_selecionado
    st.header(f"📍 Visualizando Setor: {n_sel}")

    aba_feed, aba_tarefas, aba_botoes, aba_solicitacoes = st.tabs(["📢 Atualizações", "📝 Tarefas", "🔗 Links", "📩 Solicitações"])

    with aba_feed:
        if st.session_state.usuario_logado['nucleo'] == n_sel:
            with st.form(f"form_post_{n_sel}"):
                texto_post = st.text_area("Postar uma atualização:")
                if st.form_submit_button("Publicar") and texto_post.strip() != "":
                    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    autor = f"{st.session_state.usuario_logado['nome']} ({n_sel})"
                    st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {"texto": texto_post, "data": agora, "autor": autor})
                    st.rerun()
        
        for p in st.session_state.nucleos_dados[n_sel]["atualizacoes"]:
            st.info(f"⏱️ **{p['data']}** - Por: {p['autor']}\n\n{p['texto']}")

    with aba_tarefas:
        if st.session_state.usuario_logado['nucleo'] == n_sel:
            nova_tarefa = st.text_input("Adicionar demanda:", key=f"add_{n_sel}")
            if st.button("Adicionar Tarefa"):
                if nova_tarefa.strip():
                    st.session_state.nucleos_dados[n_sel]["tarefas"].append(nova_tarefa)
                    st.rerun()
                    
        for t in st.session_state.nucleos_dados[n_sel]["tarefas"]:
            st.checkbox(t, value=False, key=f"check_{n_sel}_{t}")

    with aba_botoes:
        c1, c2 = st.columns(2)
        c1.link_button("📂 Drive", st.session_state.nucleos_dados[n_sel]["drive"], use_container_width=True)
        c2.link_button("📊 Planilhas", st.session_state.nucleos_dados[n_sel]["planilha"], use_container_width=True)

    with aba_solicitacoes:
        with st.form(f"solicitacao_{n_sel}"):
            nucleo_destino = st.selectbox("Para qual núcleo?", list(st.session_state.nucleos_dados.keys()))
            assunto = st.text_input("Assunto:")
            mensagem = st.text_area("Mensagem:")
            if st.form_submit_button("Enviar") and assunto.strip():
                agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                remetente = f"{st.session_state.usuario_logado['nome']} ({st.session_state.usuario_logado['nucleo']})"
                st.session_state.caixa_entrada[nucleo_destino].append({"assunto": assunto, "mensagem": mensagem, "data": agora, "de": remetente})
                st.success("Enviado!")

        st.divider()
        st.subheader(f"📥 Caixa de Entrada - {n_sel}")
        if st.session_state.usuario_logado['nucleo'] == n_sel:
            for m in reversed(st.session_state.caixa_entrada[n_sel]):
                with st.expander(f"📩 {m['assunto']} (De: {m['de']})"):
                    st.write(m['mensagem'])
        else:
            st.error("🔒 Acesso Restrito ao núcleo.")
