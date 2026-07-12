import streamlit as st
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
