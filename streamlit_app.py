import streamlit as st
import datetime
from zoneinfo import ZoneInfo
import os
import json
import hashlib
import secrets

st.set_page_config(
    page_title="Sistema IMLA",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Constantes gerais -------------------------------------------------------
ARQUIVO_BANCO = "banco_iml.json"
LOGO_PATH = "Submarca 01.png"        # símbolo do Instituto (ícone, sem o nome escrito ao lado)
LOGIN_BG_PATH = "IMG_3987.JPG"       # foto de fundo da tela de login

NUCLEOS_INFO = {
    "Cozinha e Nutrição": "🍳",
    "Comunicação": "📣",
    "Pedagógico": "📚",
    "Captação de Recursos": "🤝",
    "Financeiro": "💰",
    "Apadrinhamento": "💌",
}

FUSO_BR = ZoneInfo("America/Bahia")


def agora_br() -> datetime.datetime:
    """Retorna a data/hora correta do Brasil (Bahia), independente do fuso do servidor."""
    return datetime.datetime.now(FUSO_BR)


# ============================================================================
# --- 2. SEGURANÇA: HASH DE SENHA --------------------------------------------
# ============================================================================
def hash_senha(senha: str, salt: str | None = None) -> tuple[str, str]:
    """Gera um hash seguro (PBKDF2-HMAC-SHA256) da senha. A senha em texto puro
    nunca é armazenada — apenas o salt e o hash resultante."""
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return salt, h.hex()


def verificar_senha(senha: str, salt: str, hash_esperado: str) -> bool:
    """Compara a senha digitada com o hash salvo, usando comparação de tempo
    constante (evita ataques de timing)."""
    _, h = hash_senha(senha, salt)
    return secrets.compare_digest(h, hash_esperado)


# ============================================================================
# --- 3. BANCO DE DADOS JSON (persistência local) ----------------------------
# ============================================================================
def estrutura_padrao_nucleo() -> dict:
    """Estrutura vazia de um núcleo recém-criado."""
    return {
        "atualizacoes": [],
        "tarefas": [],
        "lembretes": [],
        "drive": "https://drive.google.com",
        "planilha": "https://docs.google.com",
    }


def carregar_banco() -> dict:
    """Lê o banco JSON do disco (ou cria um novo) e aplica migrações de
    compatibilidade, garantindo que registros salvos por versões anteriores
    do sistema não quebrem o app atual."""
    if os.path.exists(ARQUIVO_BANCO):
        with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
            dados = json.load(f)
    else:
        dados = {
            "usuarios": {},
            "nucleos_dados": {n: estrutura_padrao_nucleo() for n in NUCLEOS_INFO},
            "caixa_entrada": {n: [] for n in NUCLEOS_INFO},
        }

    # --- Migração 1: todo usuário precisa ter "nome" e "email" antes de
    # qualquer outra parte do código tentar lê-los (evita KeyError). ---------
    for email, u in dados.get("usuarios", {}).items():
        u.setdefault("nome", (u.get("email") or email).split("@")[0].title())
        u.setdefault("email", email)

    # --- Migração 2: garante que todos os núcleos existam com a estrutura
    # completa, mesmo que o banco tenha sido criado por uma versão anterior. -
    dados.setdefault("nucleos_dados", {})
    dados.setdefault("caixa_entrada", {})
    for n in NUCLEOS_INFO:
        dados["nucleos_dados"].setdefault(n, estrutura_padrao_nucleo())
        dados["caixa_entrada"].setdefault(n, [])

        nd = dados["nucleos_dados"][n]
        nd.setdefault("atualizacoes", [])
        nd.setdefault("tarefas", [])
        nd.setdefault("lembretes", [])
        nd.setdefault("drive", "https://drive.google.com")
        nd.setdefault("planilha", "https://docs.google.com")

        for msg in dados["caixa_entrada"][n]:
            msg.setdefault("publica", False)

    return dados


def salvar_banco() -> None:
    """Persiste o estado atual da sessão de volta no arquivo JSON."""
    dados = {
        "usuarios": st.session_state.usuarios,
        "nucleos_dados": st.session_state.nucleos_dados,
        "caixa_entrada": st.session_state.caixa_entrada,
    }
    with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)


# ============================================================================
# --- 4. ESTADO DA SESSÃO (st.session_state) ---------------------------------
# ============================================================================
# Dados persistentes (carregados do JSON uma única vez por sessão do navegador)
if "dados_carregados" not in st.session_state:
    _dados = carregar_banco()
    st.session_state.usuarios = _dados["usuarios"]
    st.session_state.nucleos_dados = _dados["nucleos_dados"]
    st.session_state.caixa_entrada = _dados["caixa_entrada"]
    st.session_state.dados_carregados = True

# Estado de navegação / sessão do usuário
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None          # dict do usuário logado, ou None
if "modo_tela" not in st.session_state:
    st.session_state.modo_tela = "login"            # "login" ou "cadastro"
if "nucleo_selecionado" not in st.session_state:
    st.session_state.nucleo_selecionado = list(NUCLEOS_INFO.keys())[0]
if "mostrar_perfil" not in st.session_state:
    st.session_state.mostrar_perfil = False         # usado no próximo bloco (painel de perfil)


# ============================================================================
# --- 5. CSS GLOBAL: IDENTIDADE VISUAL APPLE ---------------------------------
# ============================================================================
def imagem_disponivel(caminho: str) -> bool:
    return os.path.exists(caminho)


def aplicar_estilo_login() -> None:
    """CSS da tela pública (login/cadastro): fundo com foto + blur, cartão
    'vidro fosco' (glassmorphism), tipografia SF Pro."""
    bg_css = f"url('{LOGIN_BG_PATH}')" if imagem_disponivel(LOGIN_BG_PATH) else "none"

    st.markdown(f"""
    <style>
    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
                     Helvetica, Arial, sans-serif !important;
    }}
    header {{ visibility: hidden; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}

    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.55), rgba(0,0,0,0.8)), {bg_css};
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    .block-container {{ padding-top: 4vh !important; }}

    /* --- Cartão "vidro fosco" central --- */
    .login-shell {{
        background: rgba(255,255,255,0.14);
        backdrop-filter: blur(28px) saturate(180%);
        -webkit-backdrop-filter: blur(28px) saturate(180%);
        border: 1px solid rgba(255,255,255,0.35);
        border-radius: 24px;
        padding: 8px 6px 2px 6px;
        box-shadow: 0 24px 70px rgba(0,0,0,0.35);
    }}

    .login-titulo {{
        text-align:center; color:#ffffff !important; font-size: 19px !important;
        font-weight: 700 !important; margin: 4px 0 2px 0 !important;
        letter-spacing: 0.2px;
    }}
    .login-subtitulo {{
        text-align:center; color: rgba(255,255,255,0.75) !important; font-size: 12.5px !important;
        margin: 0 0 18px 0 !important; font-weight: 500;
    }}

    /* --- Inputs de texto: brancos, discretos, cantos arredondados --- */
    .stTextInput>div>div>input {{
        background-color: rgba(255,255,255,0.92) !important;
        border: 1px solid rgba(255,255,255,0.5) !important;
        border-radius: 12px !important;
        color: #1d1d1f !important;
        font-size: 14px !important;
        padding: 0.55rem 0.8rem !important;
    }}
    .stTextInput>div>div>input:focus {{
        border: 1px solid #0071e3 !important;
        box-shadow: 0 0 0 3px rgba(0,113,227,0.18) !important;
    }}

    /* --- Selectbox (Núcleo) --- */
    .stSelectbox > div > div {{
        background-color: rgba(255,255,255,0.92) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.5) !important;
    }}
    .stSelectbox [data-baseweb="select"] * {{ color: #1d1d1f !important; }}

    p, label {{ color: rgba(255,255,255,0.88) !important; font-size: 12.5px !important; font-weight: 600 !important; }}

    /* --- Botões: estilo pílula branca translúcida, ao estilo Apple --- */
    .stButton>button {{
        border-radius: 980px !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        background-color: rgba(255,255,255,0.95) !important;
        color: #1d1d1f !important;
        border: none !important;
        padding: 0.55rem 1.4rem !important;
        transition: all 0.18s ease;
    }}
    .stButton>button:hover {{
        background-color: #ffffff !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.18);
    }}
    .stButton>button * {{ color: #1d1d1f !important; }}

    /* Botão secundário (link textual, ex: "Criar nova conta") */
    .link-secundario {{
        text-align:center; margin-top: 8px;
    }}
    .link-secundario .stButton>button {{
        background: transparent !important;
        color: rgba(255,255,255,0.85) !important;
        box-shadow: none !important;
        font-weight: 500 !important;
        text-decoration: underline;
        padding: 0.3rem 0.6rem !important;
    }}
    .link-secundario .stButton>button:hover {{
        background: rgba(255,255,255,0.08) !important;
        transform: none;
        box-shadow: none !important;
    }}
    .link-secundario .stButton>button * {{ color: rgba(255,255,255,0.95) !important; }}

    .divisor-sutil {{
        border: none; border-top: 1px solid rgba(255,255,255,0.22);
        margin: 14px 0 10px 0;
    }}

    [data-testid="stAlert"] p {{ font-size: 12.5px !important; }}
    </style>
    """, unsafe_allow_html=True)


def aplicar_estilo_area_logada() -> None:
    """CSS mínimo para a área logada nesta etapa (será expandido no próximo
    bloco, junto com a barra superior)."""
    st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
                     Helvetica, Arial, sans-serif !important;
    }
    .stApp { background-color: #fafafa !important; }
    header { visibility: hidden; }
    h1, h2, h3, h4 { color: #1d1d1f !important; }
    p, span, label { color: #1d1d1f !important; }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# --- 6. TELA PÚBLICA: LOGIN E CADASTRO --------------------------------------
# ============================================================================
def tela_login() -> None:
    st.markdown("<div class='login-titulo'>Acesso ao Sistema</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-subtitulo'>Entre com seu e-mail e senha</div>", unsafe_allow_html=True)

    email_login = st.text_input("E-mail", key="campo_email_login", placeholder="voce@imla.org")
    senha_login = st.text_input("Senha", key="campo_senha_login", type="password", placeholder="••••••••")

    if st.button("Entrar", key="btn_entrar", use_container_width=True):
        chave = email_login.strip().lower()
        usuario = st.session_state.usuarios.get(chave)

        if usuario is None:
            st.error("E-mail não encontrado.")
            return

        senha_ok = False

        if "senha_hash" in usuario:
            senha_ok = verificar_senha(senha_login, usuario["salt"], usuario["senha_hash"])
        elif "senha" in usuario:
            # Compatibilidade: conta antiga com senha em texto puro.
            # Valida contra o texto puro e, se correta, migra para hash na hora.
            senha_ok = (usuario["senha"] == senha_login)
            if senha_ok:
                salt, h = hash_senha(senha_login)
                usuario["salt"], usuario["senha_hash"] = salt, h
                usuario.pop("senha", None)
                salvar_banco()

        if senha_ok:
            st.session_state.usuario_logado = usuario
            st.session_state.nucleo_selecionado = usuario["nucleo"]
            st.rerun()
        else:
            st.error("Senha incorreta.")

    st.markdown("<div class='link-secundario'>", unsafe_allow_html=True)
    if st.button("Ainda não tem conta? Criar cadastro", key="btn_ir_cadastro", use_container_width=True):
        st.session_state.modo_tela = "cadastro"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def tela_cadastro() -> None:
    st.markdown("<div class='login-titulo'>Criar cadastro</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-subtitulo'>Preencha seus dados para acessar o sistema</div>", unsafe_allow_html=True)

    nome_completo = st.text_input("Nome completo", key="campo_nome_cad", placeholder="Seu nome e sobrenome")
    email_cad = st.text_input("E-mail", key="campo_email_cad", placeholder="voce@imla.org")
    nucleo_cad = st.selectbox("Núcleo", list(NUCLEOS_INFO.keys()), key="campo_nucleo_cad")
    senha_cad = st.text_input("Senha", key="campo_senha_cad", type="password", placeholder="Crie uma senha")
    confirmar_senha_cad = st.text_input(
        "Confirmar senha", key="campo_confirmar_senha_cad", type="password", placeholder="Repita a senha"
    )

    if st.button("Finalizar cadastro", key="btn_finalizar_cadastro", use_container_width=True):
        chave = email_cad.strip().lower()

        if not (nome_completo.strip() and chave and senha_cad and confirmar_senha_cad):
            st.error("Preencha todos os campos.")
        elif "@" not in chave or "." not in chave:
            st.error("Digite um e-mail válido.")
        elif senha_cad != confirmar_senha_cad:
            st.error("As senhas não coincidem.")
        elif len(senha_cad) < 4:
            st.error("A senha deve ter pelo menos 4 caracteres.")
        elif chave in st.session_state.usuarios:
            st.warning("Este e-mail já está cadastrado.")
        else:
            salt, h = hash_senha(senha_cad)
            st.session_state.usuarios[chave] = {
                "nome": nome_completo.strip(),
                "email": chave,
                "nucleo": nucleo_cad,
                "salt": salt,
                "senha_hash": h,
            }
            salvar_banco()
            st.success("Cadastro realizado com sucesso! Faça login para continuar.")
            st.session_state.modo_tela = "login"
            st.rerun()

    st.markdown("<div class='link-secundario'>", unsafe_allow_html=True)
    if st.button("Já tenho conta — voltar ao login", key="btn_voltar_login", use_container_width=True):
        st.session_state.modo_tela = "login"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def renderizar_area_publica() -> None:
    aplicar_estilo_login()

    col_esq, col_centro, col_dir = st.columns([1.3, 1, 1.3])
    with col_centro:
        st.markdown("<div class='login-shell'>", unsafe_allow_html=True)

        if imagem_disponivel(LOGO_PATH):
            col_a, col_b, col_c = st.columns([1, 0.7, 1])
            with col_b:
                st.image(LOGO_PATH, use_container_width=True)

        if st.session_state.modo_tela == "login":
            tela_login()
        else:
            tela_cadastro()

        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# --- 7. PLACEHOLDER DA ÁREA LOGADA (será substituído no próximo bloco) ------
# ============================================================================
def renderizar_area_logada_placeholder() -> None:
    aplicar_estilo_area_logada()
    usuario = st.session_state.usuario_logado

    st.title("Sistema IMLA")
    st.write(f"Bem-vindo(a), **{usuario['nome']}**.")
    st.caption(f"Núcleo: {NUCLEOS_INFO.get(usuario['nucleo'], '')} {usuario['nucleo']}")
    st.info(
        "✅ Base do sistema funcionando: login, cadastro e banco de dados prontos. "
        "A barra superior, o painel de perfil e o conteúdo por núcleo entram no próximo bloco."
    )

    if st.button("Sair"):
        st.session_state.usuario_logado = None
        st.rerun()


# ============================================================================
# --- 8. ROTEAMENTO PRINCIPAL -------------------------------------------------
# ============================================================================
if st.session_state.usuario_logado is None:
    renderizar_area_publica()
else:
    renderizar_area_logada_placeholder()
