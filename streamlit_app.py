import streamlit as st
import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Instituto Mãe Lalu - Hub Operacional",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização básica de cores e contraste (Turquesa #59c2d1 e Verde #92c83e)
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #59c2d1; color: white; border-radius: 8px; border: none; font-weight: bold;
    }
    div.stButton > button:first-child:hover { background-color: #92c83e; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. INICIALIZAÇÃO DO BANCO DE DADOS TEMPORÁRIO (Session State)
# Isso garante que as mensagens e atualizações persistam enquanto o app estiver aberto
if "nucleos_dados" not in st.session_state:
    st.session_state.nucleos_dados = {
        "Cozinha e Nutrição": {"atualizacoes": [], "tarefas": ["Revisar estoque de secos", "Planejar cardápio da próxima semana"], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Comunicação": {"atualizacoes": [], "tarefas": ["Produzir folheto impresso (folder) do novo projeto"], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Captação de Recursos": {"atualizacoes": [], "tarefas": ["Mapear editais de julho", "Preparar relatório para doadores"], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Pedagógico": {"atualizacoes": [], "tarefas": ["Organizar cronograma de oficinas", "Reunião de alinhamento com professores"], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"},
        "Financeiro": {"atualizacoes": [], "tarefas": ["Fechar fluxo de caixa", "Conciliação bancária semanal"], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"}
    }

if "caixa_entrada" not in st.session_state:
    st.session_state.caixa_entrada = {nucleo: [] for nucleo in st.session_state.nucleos_dados.keys()}

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

# 3. ÁREA DE LOGIN NA BARRA LATERAL
st.sidebar.title("🔐 Acesso ao Sistema")
if st.session_state.usuario_logado is None:
    nucleo_login = st.sidebar.selectbox("Selecione o seu Núcleo:", list(st.session_state.nucleos_dados.keys()))
    nome_pessoa = st.sidebar.text_input("Seu Nome:")
    if st.sidebar.button("Entrar"):
        if nome_pessoa.strip() != "":
            st.session_state.usuario_logado = {"nucleo": nucleo_login, "nome": nome_pessoa}
            st.rerun()
        else:
            st.sidebar.error("Por favor, digite seu nome.")
else:
    st.sidebar.success(f"Logado como: {st.session_state.usuario_logado['nome']}")
    st.sidebar.info(f"Setor ativo: {st.session_state.usuario_logado['nucleo']}")
    if st.sidebar.button("Sair / Trocar Núcleo"):
        st.session_state.usuario_logado = None
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.write("⚡ *Dica: Outros núcleos ativos ficam destacados em VERDE no painel central.*")


# 4. TELA PRINCIPAL
st.title("Hub Operacional - Instituto Mãe Lalu")
st.write("Central de gerenciamento, integração e comunicação entre setores.")
st.divider()

# 5. MAPA MENTAL INTERATIVO (Simulado com Grid Visual Dinâmico)
st.subheader("🗺️ Organograma Interativo dos Núcleos")
st.write("Clique no botão de um núcleo para abrir o painel operacional dele logo abaixo:")

# Definindo cores dos botões de acordo com o login (Verde se o núcleo estiver ativo)
def obter_estilo_botao(nome_nucleo):
    if st.session_state.usuario_logado and st.session_state.usuario_logado['nucleo'] == nome_nucleo:
        return f"🟢 {nome_nucleo} (Ativo)"
    return f"🔵 {nome_nucleo}"

# Layout do Mapa Mental
col_esq, col_centro, col_dir = st.columns([2, 2, 2])

with col_esq:
    btn_cozinha = st.button(obter_estilo_botao("Cozinha e Nutrição"), use_container_width=True)
    btn_comunicacao = st.button(obter_estilo_botao("Comunicação"), use_container_width=True)

with col_centro:
    # Símbolo Central da Logo representado visualmente
    st.markdown("""
        <div style='text-align: center; background-color: #eef9fa; padding: 25px; border-radius: 50%; border: 4px solid #59c2d1; margin: 10px 0;'>
            <h3 style='margin:0; color:#1c4e56;'>🕊️</h3>
            <strong style='color:#1c4e56; font-size:14px;'>INSTITUTO<br>MÃE LALU</strong>
        </div>
    """, unsafe_allow_html=True)

with col_dir:
    btn_captacao = st.button(obter_estilo_botao("Captação de Recursos"), use_container_width=True)
    btn_pedagogico = st.button(obter_estilo_botao("Pedagógico"), use_container_width=True)

# Linha inferior para manter a simetria do mapa mental em volta do centro
st.columns([2, 2, 2])[1].button(obter_estilo_botao("Financeiro"), use_container_width=True)

st.divider()


# 6. CONTROLE DE NÚCLEO SELECIONADO
# Verifica qual botão do mapa mental foi clicado. Se nenhum foi clicado, mostra o do usuário logado.
if "nucleo_selecionado" not in st.session_state:
    st.session_state.nucleo_selecionado = "Comunicação"

if btn_cozinha: st.session_state.nucleo_selecionado = "Cozinha e Nutrição"
if btn_comunicacao: st.session_state.nucleo_selecionado = "Comunicação"
if btn_captacao: st.session_state.nucleo_selecionado = "Captação de Recursos"
if btn_pedagogico: st.session_state.nucleo_selecionado = "Pedagógico"
if btn_financ_click := st.session_state.get('Financeiro'): # Captura o botão inferior de forma simplificada
    pass 

# Exibição do Painel do Núcleo Selecionado
n_sel = st.session_state.nucleo_selecionado
st.header(f"📍 Setor: {n_sel}")

# Abas internas de utilidades do Núcleo
aba_feed, aba_tarefas, aba_botoes, aba_solicitacoes = st.tabs([
    "📢 Atualizações do Núcleo", 
    "📝 Tarefas Internas", 
    "🔗 Links e Documentos", 
    "📩 Enviar Solicitação Interna"
])

# ABA 1: FEED DE ATUALIZAÇÕES COM DATA E HORA
with aba_feed:
    st.subheader("O que está acontecendo neste núcleo")
    
    # Permitir postar se o usuário estiver logado
    if st.session_state.usuario_logado:
        with st.form(f"form_post_{n_sel}"):
            texto_post = st.text_area("Postar uma atualização no feed:")
            enviar_post = st.form_submit_button("Publicar Atualização")
            if enviar_post and texto_post.strip() != "":
                agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                autor = f"{st.session_state.usuario_logado['nome']} ({st.session_state.usuario_logado['nucleo']})"
                st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {"texto": texto_post, "data": agora, "autor": autor})
                st.success("Atualização publicada!")
                st.rerun()
    else:
        st.warning("Faça login na barra lateral para postar atualizações.")
        
    # Exibição do Feed
    posts = st.session_state.nucleos_dados[n_sel]["atualizacoes"]
    if posts:
        for p in posts:
            st.info(f"⏱️ **{p['data']}** - Por: {p['autor']}\n\n{p['texto']}")
    else:
        st.write("Nenhuma atualização postada recentemente neste núcleo.")

# ABA 2: ANOTAÇÕES E TAREFAS DO PRÓPRIO NÚCLEO
with aba_tarefas:
    st.subheader("Lista de Afazeres do Setor")
    nova_tarefa = st.text_input("Adicionar nova demanda interna:", key=f"add_{n_sel}")
    if st.button("Adicionar Tarefa", key=f"btn_add_{n_sel}"):
        if nova_tarefa.strip() != "":
            st.session_state.nucleos_dados[n_sel]["tarefas"].append(nova_tarefa)
            st.rerun()
            
    for t in st.session_state.nucleos_dados[n_sel]["tarefas"]:
        st.checkbox(t, value=False, key=f"check_{n_sel}_{t}")

# ABA 3: BOTÕES FÍSICOS (LINKS DIRETOS)
with aba_botoes:
    st.subheader("Documentos Oficiais e Cronogramas")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.link_button("📂 Acessar Google Drive do Setor", st.session_state.nucleos_dados[n_sel]["drive"], use_container_width=True)
    with col_b2:
        st.link_button("📊 Ver Planilhas e Cronogramas", st.session_state.nucleos_dados[n_sel]["planilha"], use_container_width=True)

# ABA 4: SISTEMA DE SOLICITAÇÃO ESTILO EMAIL INTERNO
with aba_solicitacoes:
    st.subheader(f"Enviar uma demanda/solicitação para o núcleo: {n_sel}")
    if st.session_state.usuario_logado:
        with st.form(f"solicitacao_{n_sel}"):
            assunto = st.text_input("Assunto da Solicitação:")
            mensagem = st.text_area("Descrição detalhada do pedido:")
            enviar_sol = st.form_submit_button("Enviar Mensagem")
            if enviar_sol and assunto.strip() != "" and mensagem.strip() != "":
                agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                remetente = f"{st.session_state.usuario_logado['nome']} ({st.session_state.usuario_logado['nucleo']})"
                
                # Guarda na caixa de entrada do destino
                st.session_state.caixa_entrada[n_sel].append({
                    "assunto": assunto, "mensagem": mensagem, "data": agora, "de": remetente
                })
                st.success(f"Solicitação enviada com sucesso para o núcleo {n_sel}!")
    else:
        st.warning("Faça login na barra lateral para conseguir enviar solicitações.")

    # Exibe as mensagens recebidas se o usuário logado pertencer a este núcleo
    st.divider()
    st.subheader("📥 Caixa de Entrada de Solicitações Recebidas")
    mensagens = st.session_state.caixa_entrada[n_sel]
    if mensagens:
        for m in mensagens:
            with st.expander(f"📩 {m['assunto']} (Enviado por: {m['de']}) - {m['data']}"):
                st.write(m['mensagem'])
    else:
        st.write("Nenhuma solicitação externa recebida até o momento.")
