import streamlit as st
import datetime
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Instituto Mãe Lalu - Hub Operacional",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. FORÇAR TEMA BRANCO E CORES DA INSTITUIÇÃO (Ignora o Dark Mode do navegador)
st.markdown("""
    <style>
    /* Fundo branco e texto escuro para o app inteiro */
    .stApp { background-color: #ffffff !important; }
    .stApp, p, h1, h2, h3, h4, h5, h6, span, label, div, li { color: #1c4e56 !important; }
    
    /* Barra lateral */
    [data-testid="stSidebar"] { background-color: #f7fbfb !important; border-right: 2px solid #eef9fa; }
    
    /* Botões Padrão - Turquesa e Verde */
    div.stButton > button:first-child {
        background-color: #ffffff; 
        color: #59c2d1 !important; 
        border-radius: 20px; 
        border: 2px solid #59c2d1; 
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover { 
        background-color: #92c83e; 
        color: #ffffff !important;
        border-color: #92c83e;
    }
    
    /* Botões Ativos (Verdes) */
    .botao-ativo > button:first-child {
        background-color: #92c83e !important;
        color: white !important;
        border: 2px solid #92c83e !important;
    }
    
    /* Caixa de texto com fundo branco */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #ffffff !important;
        color: #1c4e56 !important;
        border: 1px solid #59c2d1 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. BANCO DE DADOS TEMPORÁRIO (Agora com Senhas e Apadrinhamento)
if "nucleos_dados" not in st.session_state:
    st.session_state.nucleos_dados = {
        "Cozinha e Nutrição": {"senha": "senha123", "atualizacoes": [], "tarefas": ["Revisar estoque", "Planejar cardápio"], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Comunicação": {"senha": "senha123", "atualizacoes": [], "tarefas": ["Produzir folheto"], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Captação de Recursos": {"senha": "senha123", "atualizacoes": [], "tarefas": ["Mapear editais"], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Pedagógico": {"senha": "senha123", "atualizacoes": [], "tarefas": ["Cronograma de oficinas"], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Financeiro": {"senha": "senha123", "atualizacoes": [], "tarefas": ["Fechar fluxo de caixa"], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Apadrinhamento": {"senha": "senha123", "atualizacoes": [], "tarefas": ["Revisar fichas de padrinhos", "Enviar cartas de agradecimento"], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"}
    }

if "caixa_entrada" not in st.session_state:
    st.session_state.caixa_entrada = {nucleo: [] for nucleo in st.session_state.nucleos_dados.keys()}

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

# 4. SISTEMA DE LOGIN COM SENHA (BARRA LATERAL)
st.sidebar.title("🔐 Acesso ao Sistema")
if st.session_state.usuario_logado is None:
    nucleo_login = st.sidebar.selectbox("Selecione o seu Núcleo:", list(st.session_state.nucleos_dados.keys()))
    nome_pessoa = st.sidebar.text_input("Seu Nome:")
    senha_digitada = st.sidebar.text_input("Senha do Núcleo:", type="password") # Campo oculto
    
    if st.sidebar.button("Entrar"):
        if nome_pessoa.strip() == "":
            st.sidebar.error("Por favor, digite seu nome.")
        elif senha_digitada == st.session_state.nucleos_dados[nucleo_login]["senha"]:
            st.session_state.usuario_logado = {"nucleo": nucleo_login, "nome": nome_pessoa}
            st.rerun()
        else:
            st.sidebar.error("Senha incorreta!")
else:
    st.sidebar.success(f"Logado como: {st.session_state.usuario_logado['nome']}")
    st.sidebar.info(f"Setor ativo: {st.session_state.usuario_logado['nucleo']}")
    if st.sidebar.button("Sair / Trocar Núcleo"):
        st.session_state.usuario_logado = None
        st.rerun()

# 5. CABEÇALHO
st.title("Hub Operacional - Instituto Mãe Lalu")
st.divider()

# 6. MAPA MENTAL INTERATIVO
st.markdown("<h3 style='text-align: center;'>🗺️ Organograma Interativo</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Clique em um núcleo para ver seus detalhes</p>", unsafe_allow_html=True)

# Lógica para gerenciar cliques nos botões do mapa mental
if "nucleo_selecionado" not in st.session_state:
    st.session_state.nucleo_selecionado = "Comunicação"

def definir_nucleo(nome):
    st.session_state.nucleo_selecionado = nome

# Estrutura do Mapa Mental (3 Colunas)
col_esq, col_centro, col_dir = st.columns([1.5, 2, 1.5], gap="large")

with col_esq:
    st.write("") # Espaçamento
    if st.button("🍳 Cozinha e Nutrição", use_container_width=True): definir_nucleo("Cozinha e Nutrição")
    st.write("")
    if st.button("📣 Comunicação", use_container_width=True): definir_nucleo("Comunicação")
    st.write("")
    if st.button("📚 Pedagógico", use_container_width=True): definir_nucleo("Pedagógico")

with col_centro:
    # Mostra a logo original no centro do mapa mental
    caminho_logo = "Logotipo Principal 01 (1).png"
    if os.path.exists(caminho_logo):
        st.image(caminho_logo, use_container_width=True)
    else:
        st.markdown("<div style='text-align:center; padding:50px; background:#eef9fa; border-radius:20px;'><h1 style='color:#59c2d1;'>Mãe Lalu</h1></div>", unsafe_allow_html=True)

with col_dir:
    st.write("")
    if st.button("🤝 Captação de Recursos", use_container_width=True): definir_nucleo("Captação de Recursos")
    st.write("")
    if st.button("💰 Financeiro", use_container_width=True): definir_nucleo("Financeiro") # Corrigido e clicável
    st.write("")
    if st.button("💌 Apadrinhamento", use_container_width=True): definir_nucleo("Apadrinhamento")

st.divider()

# 7. EXIBIÇÃO DO PAINEL DO NÚCLEO SELECIONADO
n_sel = st.session_state.nucleo_selecionado
st.header(f"📍 Visualizando Setor: {n_sel}")

aba_feed, aba_tarefas, aba_botoes, aba_solicitacoes = st.tabs([
    "📢 Atualizações", 
    "📝 Tarefas Internas", 
    "🔗 Links", 
    "📩 Solicitações"
])

# ABA 1: FEED DE ATUALIZAÇÕES
with aba_feed:
    if st.session_state.usuario_logado and st.session_state.usuario_logado['nucleo'] == n_sel:
        with st.form(f"form_post_{n_sel}"):
            texto_post = st.text_area("Postar uma atualização no feed do seu setor:")
            if st.form_submit_button("Publicar") and texto_post.strip() != "":
                agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                autor = f"{st.session_state.usuario_logado['nome']} ({n_sel})"
                st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {"texto": texto_post, "data": agora, "autor": autor})
                st.success("Publicado!")
                st.rerun()
    elif st.session_state.usuario_logado:
        st.info("Você só pode postar atualizações no feed do seu próprio núcleo.")

    posts = st.session_state.nucleos_dados[n_sel]["atualizacoes"]
    if posts:
        for p in posts:
            st.info(f"⏱️ **{p['data']}** - Por: {p['autor']}\n\n{p['texto']}")
    else:
        st.write("Nenhuma atualização postada.")

# ABA 2: TAREFAS
with aba_tarefas:
    # Apenas o núcleo logado pode adicionar tarefas para si mesmo
    if st.session_state.usuario_logado and st.session_state.usuario_logado['nucleo'] == n_sel:
        nova_tarefa = st.text_input("Adicionar nova demanda interna:", key=f"add_{n_sel}")
        if st.button("Adicionar Tarefa", key=f"btn_add_{n_sel}"):
            if nova_tarefa.strip() != "":
                st.session_state.nucleos_dados[n_sel]["tarefas"].append(nova_tarefa)
                st.rerun()
                
    for t in st.session_state.nucleos_dados[n_sel]["tarefas"]:
        st.checkbox(t, value=False, key=f"check_{n_sel}_{t}")

# ABA 3: LINKS (BOTÕES FÍSICOS)
with aba_botoes:
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.link_button("📂 Acessar Google Drive do Setor", st.session_state.nucleos_dados[n_sel]["drive"], use_container_width=True)
    with col_b2:
        st.link_button("📊 Ver Planilhas e Cronogramas", st.session_state.nucleos_dados[n_sel]["planilha"], use_container_width=True)

# ABA 4: SISTEMA DE SOLICITAÇÕES COM SEGURANÇA
with aba_solicitacoes:
    st.subheader("Enviar uma solicitação intersetorial")
    
    if st.session_state.usuario_logado:
        with st.form(f"solicitacao_{n_sel}"):
            # NOVO: Escolher para quem enviar a mensagem
            nucleo_destino = st.selectbox("Para qual núcleo você quer enviar?", list(st.session_state.nucleos_dados.keys()))
            assunto = st.text_input("Assunto:")
            mensagem = st.text_area("Mensagem detalhada:")
            
            if st.form_submit_button("Enviar Mensagem") and assunto.strip() != "" and mensagem.strip() != "":
                agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                remetente = f"{st.session_state.usuario_logado['nome']} ({st.session_state.usuario_logado['nucleo']})"
                
                st.session_state.caixa_entrada[nucleo_destino].append({
                    "assunto": assunto, "mensagem": mensagem, "data": agora, "de": remetente
                })
                st.success(f"Enviado com sucesso para {nucleo_destino}!")
    else:
        st.warning("Faça login para enviar solicitações.")

    st.divider()
    
    # SEGURANÇA: Apenas quem está logado NESTE núcleo pode ler as mensagens
    st.subheader(f"📥 Caixa de Entrada - {n_sel}")
    if st.session_state.usuario_logado and st.session_state.usuario_logado['nucleo'] == n_sel:
        mensagens = st.session_state.caixa_entrada[n_sel]
        if mensagens:
            for m in reversed(mensagens):
                with st.expander(f"📩 {m['assunto']} (De: {m['de']}) - {m['data']}"):
                    st.write(m['mensagem'])
        else:
            st.write("Caixa de entrada vazia.")
    else:
        st.error(f"🔒 Acesso Restrito. Apenas membros logados no núcleo '{n_sel}' podem visualizar estas mensagens.")
