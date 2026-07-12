import streamlit as st
import datetime
impimport streamlit as st
import datetime
import os
import json

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sistema IMLA", layout="wide")

# 2. SISTEMA DE BANCO DE DADOS
ARQUIVO_BANCO = "banco_iml.json"

def carregar_banco():
    if os.path.exists(ARQUIVO_BANCO):
        with open(ARQUIVO_BANCO, "r") as f:
            return json.load(f)
    return {
        "usuarios": {},
        "nucleos_dados": {
            "Cozinha e Nutrição": {"atualizacoes": [], "tarefas": [], "drive": "#"},
            "Comunicação": {"atualizacoes": [], "tarefas": [], "drive": "#"},
            "Captação de Recursos": {"atualizacoes": [], "tarefas": [], "drive": "#"},
            "Pedagógico": {"atualizacoes": [], "tarefas": [], "drive": "#"},
            "Financeiro": {"atualizacoes": [], "tarefas": [], "drive": "#"},
            "Apadrinhamento": {"atualizacoes": [], "tarefas": [], "drive": "#"}
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
if "nucleo_selecionado" not in st.session_state: st.session_state.nucleo_selecionado = None

# 3. CSS ESTILO APPLE
st.markdown("""
    <style>
    /* Reset e Fundo */
    .stApp { background-color: #f5f5f7; }
    
    /* Hero Section */
    .hero-container { text-align: center; padding: 100px 20px; }
    .hero-title { font-size: 3.5rem; font-weight: 600; color: #1d1d1f; margin-bottom: 10px; }
    
    /* Logo Discreta */
    .logo-header { position: absolute; top: 20px; left: 20px; font-weight: bold; color: #1d1d1f; font-size: 1.2rem; }
    
    /* Cards Modernos */
    .nucleus-card { 
        background: white; padding: 25px; border-radius: 18px; text-align: center; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: 0.3s; cursor: pointer; border: 1px solid #e0e0e0;
    }
    .nucleus-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ÁREA PÚBLICA (LOGIN)
# ==========================================
if st.session_state.usuario_logado is None:
    # Logo Discreta
    st.markdown("<div class='logo-header'>IMLA</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='hero-container'><h1 class='hero-title'>Sistema IMLA</h1><p>Conectando propósitos.</p></div>", unsafe_allow_html=True)
    
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", type="primary"):
            user = st.session_state.usuarios.get(email)
            if user and user.get("senha") == senha:
                st.session_state.usuario_logado = user
                st.rerun()
            else: st.error("Credenciais inválidas.")

# ==========================================
# ÁREA PRIVADA
# ==========================================
else:
    # Header minimalista
    col_h1, col_h2 = st.columns([1, 1])
    with col_h1: st.write("IMLA")
    with col_h2: 
        if st.button("Sair"):
            st.session_state.usuario_logado = None
            st.rerun()

    # Se nenhum núcleo selecionado, mostra a "Home" de navegação
    if st.session_state.nucleo_selecionado is None:
        st.markdown("### Acesse todos os núcleos")
        st.caption("Escolha e clique")
        
        cols = st.columns(3)
        nucleos = list(st.session_state.nucleos_dados.keys())
        for i, nucleo in enumerate(nucleos):
            with cols[i % 3]:
                if st.button(f"**{nucleo}**", key=f"btn_{nucleo}"):
                    st.session_state.nucleo_selecionado = nucleo
                    st.rerun()
    
    # Se núcleo selecionado, mostra conteúdo
    else:
        n_sel = st.session_state.nucleo_selecionado
        if st.button("← Voltar"):
            st.session_state.nucleo_selecionado = None
            st.rerun()
            
        st.title(n_sel)
        
        # Correção de Erros (Defensive Coding)
        aba_feed, aba_tarefas, aba_solicitacoes = st.tabs(["Atualizações", "Demandas", "Solicitações"])
        
        with aba_feed:
            # Proteção contra KeyError
            usuario = st.session_state.usuario_logado
            if usuario and usuario.get("nucleo") == n_sel:
                with st.form("form_update", clear_on_submit=True):
                    texto = st.text_area("Nova atualização:")
                    if st.form_submit_button("Publicar"):
                        st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {
                            "texto": texto, 
                            "autor": usuario.get("nome", "Usuário"), 
                            "data": datetime.datetime.now().strftime("%d/%m/%Y")
                        })
                        salvar_banco()
                        st.rerun()
            
            for p in st.session_state.nucleos_dados[n_sel]["atualizacoes"]:
                st.markdown(f"**{p.get('autor')}**: {p.get('texto')}")

        with aba_tarefas:
            # Correção de erro de loop (TypeError)
            lista_tarefas = st.session_state.nucleos_dados[n_sel].get("tarefas", [])
            
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: st.write("A Fazer")
            with col_t2: st.write("Fazendo")
            with col_t3: st.write("Feito")
            
            # Validação: só renderiza se for dicionário válido
            for idx, t in enumerate(lista_tarefas):
                if isinstance(t, dict): # Proteção extra
                    status = t.get("status", "criado")
                    titulo = t.get("titulo", "Sem título")
                    if status == "criado":
                        with col_t1: st.info(titulo)
                    elif status == "fazendo":
                        with col_t2: st.warning(titulo)
                    elif status == "feito":
                        with col_t3: st.success(titulo)
import json
import base64

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Sistema IMLA",
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
            "Cozinha e Nutrição": {"atualizacoes": [], "tarefas": [], "drive": "#", "planilha": "#"},
            "Comunicação": {"atualizacoes": [], "tarefas": [], "drive": "#", "planilha": "#"},
            "Captação de Recursos": {"atualizacoes": [], "tarefas": [], "drive": "#", "planilha": "#"},
            "Pedagógico": {"atualizacoes": [], "tarefas": [], "drive": "#", "planilha": "#"},
            "Financeiro": {"atualizacoes": [], "tarefas": [], "drive": "#", "planilha": "#"},
            "Apadrinhamento": {"atualizacoes": [], "tarefas": [], "drive": "#", "planilha": "#"}
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

# 3. CSS CUSTOMIZADO (Banner, Trello Cards, Organograma)
def injetar_estilos():
    st.markdown("""
        <style>
        .stApp { background: #f4f5f7 !important; }
        .banner-img { width: 100%; height: 300px; object-fit: cover; border-radius: 15px; margin-bottom: 20px; }
        
        /* Organograma Estilo Árvore */
        .node-circle { width: 60px; height: 60px; border-radius: 50%; background: #ffffff; border: 2px solid #333; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 24px; }
        .node-label { text-align: center; margin-top: 8px; font-weight: 600; font-size: 12px; color: #333; }
        
        /* Estilo Trello */
        .trello-column { background: #ebecf0; padding: 15px; border-radius: 10px; min-height: 400px; }
        .trello-card { background: white; padding: 15px; border-radius: 5px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# ÁREA PÚBLICA (LOGIN/CADASTRO)
# ==========================================
if st.session_state.usuario_logado is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.modo_tela == "login":
            st.title("Sistema IMLA")
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                # Busca usuário pelo email
                user = st.session_state.usuarios.get(email)
                if user and user["senha"] == senha:
                    st.session_state.usuario_logado = user
                    st.rerun()
                else: st.error("Email ou senha incorretos.")
            if st.button("Criar Conta"):
                st.session_state.modo_tela = "cadastro"
                st.rerun()
        else:
            st.title("Cadastro")
            nome = st.text_input("Nome Completo")
            email = st.text_input("Email")
            nucleo = st.selectbox("Seu Núcleo", list(st.session_state.nucleos_dados.keys()))
            senha = st.text_input("Senha", type="password")
            confirm = st.text_input("Confirmar Senha", type="password")
            
            if st.button("Finalizar Cadastro"):
                if senha == confirm:
                    st.session_state.usuarios[email] = {"nome": nome, "email": email, "nucleo": nucleo, "senha": senha}
                    salvar_banco()
                    st.session_state.modo_tela = "login"
                    st.success("Conta criada! Pode logar.")
                    st.rerun()
                else: st.error("As senhas não conferem.")

# ==========================================
# ÁREA PRIVADA (SISTEMA IMLA)
# ==========================================
else:
    injetar_estilos()
    
    # 1. BANNER
    if os.path.exists("IMG_3985.JPG"):
        st.image("IMG_3985.JPG", use_container_width=True)
    
    st.title("Sistema IMLA")
    
    # 2. ORGANOGRAMA (Ecossistema)
    st.markdown("### Organograma")
    cols = st.columns(6)
    icones = ["🍳", "📣", "📚", "🤝", "💰", "💌"]
    for i, (nome, icone) in enumerate(zip(st.session_state.nucleos_dados.keys(), icones)):
        with cols[i]:
            st.markdown(f"<div class='node-circle'>{icone}</div><div class='node-label'>{nome}</div>", unsafe_allow_html=True)
            if st.button("Selecionar", key=f"sel_{nome}"):
                st.session_state.nucleo_selecionado = nome
                st.rerun()
    
    st.divider()
    n_sel = st.session_state.nucleo_selecionado
    st.subheader(f"Núcleo Selecionado: {n_sel}")

    aba_feed, aba_tarefas, aba_solicitacoes = st.tabs(["Atualizações", "Demandas", "Solicitações"])

    # ABA FEED
    with aba_feed:
        if st.session_state.usuario_logado['nucleo'] == n_sel:
            with st.form("form_update"):
                texto = st.text_area("Nova atualização:")
                if st.form_submit_button("Publicar"):
                    st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {
                        "texto": texto, 
                        "autor": st.session_state.usuario_logado['nome'], 
                        "data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    })
                    salvar_banco()
                    st.rerun()
        
        for p in st.session_state.nucleos_dados[n_sel]["atualizacoes"]:
            st.markdown(f"**{p['autor']}** <small>({p['data']})</small><br>{p['texto']}<hr>", unsafe_allow_html=True)

    # ABA TAREFAS (TRELLO STYLE)
    with aba_tarefas:
        # Só o membro do núcleo pode adicionar
        if st.session_state.usuario_logado['nucleo'] == n_sel:
            nova_t = st.text_input("Criar nova demanda:")
            if st.button("Adicionar Tarefa"):
                st.session_state.nucleos_dados[n_sel]["tarefas"].append({
                    "titulo": nova_t,
                    "status": "criado",
                    "autor": st.session_state.usuario_logado['nome'],
                    "data": datetime.datetime.now().strftime("%d/%m %H:%M")
                })
                salvar_banco()
                st.rerun()

        cols_t = st.columns(3)
        status_map = [("criado", "A Fazer", cols_t[0]), ("fazendo", "Fazendo", cols_t[1]), ("feito", "Feito", cols_t[2])]
        
        for s_key, s_label, col in status_map:
            with col:
                st.markdown(f"### {s_label}")
                for idx, t in enumerate(st.session_state.nucleos_dados[n_sel]["tarefas"]):
                    if t["status"] == s_key:
                        with st.container():
                            st.markdown(f"""
                                <div class='trello-card'>
                                    <b>{t['titulo']}</b><br>
                                    <small>Por: {t['autor']} | {t['data']}</small>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Apenas membro do núcleo pode editar o status
                            if st.session_state.usuario_logado['nucleo'] == n_sel:
                                novo_status = st.selectbox("Mover para:", ["criado", "fazendo", "feito"], index=["criado", "fazendo", "feito"].index(s_key), key=f"sel_{idx}")
                                if novo_status != s_key:
                                    t["status"] = novo_status
                                    salvar_banco()
                                    st.rerun()

    # ABA SOLICITAÇÕES
    with aba_solicitacoes:
        # Apenas Comunicação pode enviar
        if st.session_state.usuario_logado['nucleo'] == "Comunicação":
            with st.form("form_solicitacao"):
                dest = st.selectbox("Para qual núcleo?", list(st.session_state.nucleos_dados.keys()))
                assunto = st.text_input("Assunto:")
                msg = st.text_area("Mensagem:")
                if st.form_submit_button("Enviar"):
                    st.session_state.caixa_entrada[dest].append({
                        "assunto": assunto, 
                        "msg": msg, 
                        "de": st.session_state.usuario_logado['nome'],
                        "data": datetime.datetime.now().strftime("%d/%m")
                    })
                    salvar_banco()
                    st.success("Enviado com sucesso!")
        
        # Leitura da caixa de entrada
        st.write(f"### Caixa de Entrada - {n_sel}")
        if st.session_state.usuario_logado['nucleo'] == n_sel:
            for m in reversed(st.session_state.caixa_entrada[n_sel]):
                st.info(f"**{m['assunto']}** (De: {m['de']})\n\n{m['msg']} \n\n<small>{m['data']}</small>")
        else:
            st.warning("🔒 Restrito aos membros deste núcleo.")
