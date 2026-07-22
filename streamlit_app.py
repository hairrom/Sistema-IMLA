import streamlit as st
import datetime
from zoneinfo import ZoneInfo
import os
import io
import json
import base64
import hashlib
import secrets
import uuid
from PIL import Image

st.set_page_config(
    page_title="Sistema IMLA",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Constantes gerais -------------------------------------------------------
ARQUIVO_BANCO = "banco_iml.json"
LOGO_CANDIDATOS = ["Submarca 01.png", "Logotipo Principal 01 (1).png"]  # tenta nesta ordem
LOGIN_BG_PATH = "IMG_3987.JPG"       # foto de fundo da tela de login
BANNER_PATH = "IMG_3985.JPG"         # foto do banner na área logada

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


@st.cache_data(show_spinner=False)
def imagem_base64(caminho: str) -> str | None:
    """Lê qualquer imagem do disco e retorna em base64, para embutir via CSS/HTML."""
    if not os.path.exists(caminho):
        return None
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode()


@st.cache_data(show_spinner=False)
def logo_simbolo_base64() -> tuple[str | None, str]:
    """Localiza o logotipo do sistema entre os candidatos conhecidos.
    Se o arquivo já for só o símbolo (proporção quase quadrada), usa como está.
    Se for um logotipo largo (ícone + nome escrito ao lado), corta e mantém só
    o quadrado da esquerda, descartando o texto, para caber com elegância na
    barra superior. Retorna (base64_ou_None, caminho_usado)."""
    for caminho in LOGO_CANDIDATOS:
        if not os.path.exists(caminho):
            continue
        im = Image.open(caminho).convert("RGBA")
        w, h = im.size
        if w > h * 1.15:
            im = im.crop((0, 0, h, h))
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode(), caminho
    return None, ""


@st.cache_data(show_spinner=False)
def banner_base64(caminho: str, proporcao: float = 21 / 6) -> str | None:
    """Recorta a imagem para uma proporção de banner de site bem panorâmica,
    mantendo o centro da foto, e retorna em base64 (JPEG)."""
    if not os.path.exists(caminho):
        return None
    im = Image.open(caminho).convert("RGB")
    w, h = im.size
    razao_atual = w / h
    if razao_atual > proporcao:
        novo_w = int(h * proporcao)
        left = (w - novo_w) // 2
        box = (left, 0, left + novo_w, h)
    else:
        novo_h = int(w / proporcao)
        top = (h - novo_h) // 2
        box = (0, top, w, top + novo_h)
    recorte = im.crop(box).resize((1600, int(1600 / proporcao)))
    buf = io.BytesIO()
    recorte.save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()


def aplicar_estilo_login() -> None:
    """CSS da tela pública (login/cadastro): fundo com foto + blur, cartão
    'vidro fosco' (glassmorphism), tipografia SF Pro."""
    login_bg_b64 = imagem_base64(LOGIN_BG_PATH)
    bg_css = f"url(data:image/jpeg;base64,{login_bg_b64})" if login_bg_b64 else "none"

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
    """CSS completo da área logada: barra superior flutuante em vidro fosco,
    banner com bordas arredondadas, popover de perfil e abas por núcleo."""
    st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
                     Helvetica, Arial, sans-serif !important;
    }
    .stApp { background-color: #f5f5f7 !important; }
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    .block-container { padding-top: 1rem !important; max-width: 1180px !important; }

    h1, h2, h3, h4 { color: #1d1d1f !important; }
    p, span, label { color: #1d1d1f !important; }

    /* ---------- BARRA SUPERIOR (App Bar) — vidro fosco ---------- */
    div[class*="st-key-app_bar"] {
        background: rgba(255,255,255,0.72) !important;
        backdrop-filter: blur(22px) saturate(180%);
        -webkit-backdrop-filter: blur(22px) saturate(180%);
        border: 1px solid rgba(255,255,255,0.6);
        border-radius: 22px;
        box-shadow: 0 10px 34px rgba(0,0,0,0.10);
        padding: 10px 18px !important;
        margin-bottom: 22px;
    }
    div[class*="st-key-app_bar"] div[data-testid="column"] { overflow: visible; }

    /* Botões de navegação dos núcleos, dentro da barra */
    div[class*="st-key-app_bar"] .stButton>button {
        width: 100% !important;
        border-radius: 980px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        padding: 0.5rem 0.7rem !important;
        border: none !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        background-color: transparent !important;
        color: #1d1d1f !important;
        transition: all 0.15s ease;
    }
    div[class*="st-key-app_bar"] .stButton>button:hover {
        background-color: rgba(0,0,0,0.05) !important;
    }
    div[class*="st-key-app_bar"] button[kind="primary"] {
        background-color: #1d1d1f !important;
        color: #ffffff !important;
    }
    div[class*="st-key-app_bar"] button[kind="primary"] p { color: #ffffff !important; }
    div[class*="st-key-app_bar"] button[kind="primary"]:hover { background-color: #000000 !important; }

    /* Botão de perfil (avatar redondo) que abre o popover */
    div[class*="st-key-perfil_col"] button {
        border-radius: 50% !important;
        width: 40px !important; height: 40px !important;
        padding: 0 !important;
        background-color: #0071e3 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 12px !important;
        border: none !important;
    }
    div[class*="st-key-perfil_col"] button p { color: #ffffff !important; }
    div[class*="st-key-perfil_col"] button:hover { background-color: #0060c2 !important; }

    /* Conteúdo do popover de perfil */
    div[data-testid="stPopoverBody"] { border-radius: 16px !important; }
    div[data-testid="stPopoverBody"] .stButton>button {
        border-radius: 980px !important;
        font-size: 12.5px !important;
        font-weight: 600 !important;
    }

    /* ---------- BANNER PRINCIPAL ---------- */
    .banner-imla {
        width: 100%;
        height: 230px;
        border-radius: 26px;
        overflow: hidden;
        background-size: cover;
        background-position: center;
        display: flex;
        align-items: flex-end;
        padding: 26px 32px;
        margin-bottom: 26px;
        box-shadow: 0 14px 40px rgba(0,0,0,0.14);
    }
    .banner-imla h1 {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 32px !important;
        margin: 0 !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 16px rgba(0,0,0,0.55);
    }
    .banner-imla p {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        margin: 2px 0 0 0 !important;
        font-size: 13.5px !important;
        opacity: 0.94;
        text-shadow: 0 1px 10px rgba(0,0,0,0.5);
    }

    /* ---------- ABAS ---------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(0,0,0,0.035);
        padding: 5px;
        border-radius: 14px;
        overflow-x: auto !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        white-space: nowrap !important;
        padding: 6px 18px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }

    /* ---------- Cartões genéricos ---------- */
    .cartao-imla {
        background: #ffffff;
        border-radius: 18px;
        padding: 18px 20px;
        border: 1px solid rgba(0,0,0,0.045);
        box-shadow: 0 3px 14px rgba(0,0,0,0.045);
        margin-bottom: 14px;
    }

    /* ---------- Responsivo ---------- */
    @media (max-width: 760px) {
        div[class*="st-key-app_bar"] { padding: 8px 10px !important; border-radius: 18px; }
        div[class*="st-key-app_bar"] .stButton>button { font-size: 10.5px !important; padding: 0.45rem 0.5rem !important; }
        .banner-imla { height: 170px; padding: 18px 20px; border-radius: 18px; }
        .banner-imla h1 { font-size: 22px !important; }
    }
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

        logo_b64, _ = logo_simbolo_base64()
        if logo_b64:
            col_a, col_b, col_c = st.columns([1, 0.7, 1])
            with col_b:
                st.image(f"data:image/png;base64,{logo_b64}", use_container_width=True)

        if st.session_state.modo_tela == "login":
            tela_login()
        else:
            tela_cadastro()

        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# --- 7. ÁREA LOGADA: BARRA SUPERIOR, BANNER E ABAS DO NÚCLEO ----------------
# ============================================================================
def renderizar_app_bar(usuario: dict) -> None:
    """Barra superior fixa e flutuante: logo à esquerda, navegação dos núcleos
    ao centro, perfil (popover) à direita. Usa componentes reais do Streamlit
    — nenhum link HTML cru — para que a navegação nunca derrube a sessão."""
    n_sel = st.session_state.nucleo_selecionado
    logo_b64, _ = logo_simbolo_base64()
    iniciais = "".join([p[0].upper() for p in usuario["nome"].split()[:2]]) or "?"

    with st.container(key="app_bar"):
        pesos_nucleos = [0.55 + len(nome) * 0.045 for nome in NUCLEOS_INFO]
        larguras = [0.5] + pesos_nucleos + [0.4]
        cols = st.columns(larguras, vertical_alignment="center")

        with cols[0]:
            if logo_b64:
                st.image(f"data:image/png;base64,{logo_b64}")

        for i, (nome, emoji) in enumerate(NUCLEOS_INFO.items(), start=1):
            with cols[i]:
                tipo_botao = "primary" if nome == n_sel else "secondary"
                if st.button(f"{emoji} {nome}", key=f"nav_{nome}", type=tipo_botao, use_container_width=True):
                    st.session_state.nucleo_selecionado = nome
                    st.rerun()

        with cols[-1]:
            with st.container(key="perfil_col"):
                with st.popover(iniciais, use_container_width=False):
                    st.markdown(f"**{usuario['nome']}**")
                    st.caption(f"E-mail: {usuario['email']}")
                    st.caption(f"Núcleo: {NUCLEOS_INFO.get(usuario['nucleo'], '')} {usuario['nucleo']}")
                    st.divider()
                    if st.button("Sair", key="btn_sair_popover", use_container_width=True, type="primary"):
                        st.session_state.usuario_logado = None
                        st.rerun()


def renderizar_banner() -> None:
    """Banner de capa do Hub, usando a foto IMG_3985.JPG recortada em
    proporção panorâmica, com bordas arredondadas."""
    banner_b64 = banner_base64(BANNER_PATH)
    fundo_css = f"url(data:image/jpeg;base64,{banner_b64})" if banner_b64 else "none"

    st.markdown(f"""
        <div class="banner-imla" style="background-image:
            linear-gradient(rgba(0,0,0,0.32), rgba(0,0,0,0.62)), {fundo_css};">
            <div>
                <h1>Sistema IMLA</h1>
                <p>Onde nós trabalhamos</p>
            </div>
        </div>
    """, unsafe_allow_html=True)


def renderizar_aba_feed(usuario: dict, n_sel: str, pode_editar: bool) -> None:
    """Aba de Feed: publica e lista as novidades do núcleo."""
    if pode_editar:
        with st.form("form_novo_post", clear_on_submit=True):
            texto = st.text_area("Compartilhar algo novo com o núcleo:", placeholder="Escreva aqui...")
            if st.form_submit_button("Publicar") and texto.strip():
                st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {
                    "texto": texto.strip(),
                    "data": agora_br().strftime("%d/%m/%Y %H:%M"),
                    "autor_nome": usuario["nome"],
                    "autor_email": usuario["email"],
                })
                salvar_banco()
                st.rerun()
        st.write("")
    else:
        st.caption("🔒 Apenas membros deste núcleo podem publicar. Você pode ler as novidades abaixo.")
        st.write("")

    posts = st.session_state.nucleos_dados[n_sel]["atualizacoes"]
    if not posts:
        st.caption("Nenhuma novidade publicada ainda.")
        return

    col1, col2, col3 = st.columns(3)
    colunas = [col1, col2, col3]
    for i, p in enumerate(posts):
        with colunas[i % 3]:
            st.markdown(f"""
            <div class="cartao-imla">
                <div style="font-size:10.5px; font-weight:700; color:#0071e3; text-transform:uppercase; letter-spacing:.4px;">
                    {p.get('autor_nome', '—')}
                </div>
                <div style="font-size:13.5px; color:#1d1d1f; margin-top:6px; line-height:1.5;">
                    {p['texto']}
                </div>
                <div style="font-size:10.5px; color:#86868b; margin-top:12px;">{p['data']}</div>
            </div>
            """, unsafe_allow_html=True)


def renderizar_aba_tarefas(n_sel: str, pode_editar: bool) -> None:
    """Aba de Tarefas em formato Kanban (Criada / Em andamento / Concluída)."""
    if pode_editar:
        with st.expander("➕ Nova tarefa"):
            with st.form("form_nova_tarefa", clear_on_submit=True):
                titulo = st.text_input("Título da tarefa")
                descricao = st.text_area("Descrição (o que precisa ser feito)")
                prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta"], index=1)
                if st.form_submit_button("Adicionar tarefa") and titulo.strip():
                    st.session_state.nucleos_dados[n_sel]["tarefas"].append({
                        "id": str(uuid.uuid4())[:8],
                        "titulo": titulo.strip(),
                        "descricao": descricao.strip(),
                        "status": "Criada",
                        "prioridade": prioridade,
                        "autor_nome": st.session_state.usuario_logado["nome"],
                        "data_hora": agora_br().strftime("%d/%m/%Y %H:%M"),
                    })
                    salvar_banco()
                    st.rerun()
    else:
        st.caption("🔒 Apenas membros deste núcleo podem criar ou editar tarefas.")

    st.write("")
    tarefas = st.session_state.nucleos_dados[n_sel]["tarefas"]
    status_cores = {"Criada": "#8e8e93", "Em andamento": "#0071e3", "Concluída": "#34c759"}
    prioridade_cores = {"Baixa": "#34c759", "Média": "#ff9f0a", "Alta": "#ff3b30"}

    col_criada, col_andamento, col_concluida = st.columns(3)
    colunas_status = {"Criada": col_criada, "Em andamento": col_andamento, "Concluída": col_concluida}

    for status_nome, coluna in colunas_status.items():
        with coluna:
            st.markdown(
                f"<div style='font-size:11.5px; font-weight:800; color:#6e6e73; "
                f"text-transform:uppercase; letter-spacing:.5px; margin-bottom:8px;'>{status_nome}</div>",
                unsafe_allow_html=True,
            )
            tarefas_col = [tf for tf in tarefas if tf.get("status") == status_nome]
            if not tarefas_col:
                st.caption("—")
            for tf in tarefas_col:
                cor_prio = prioridade_cores.get(tf.get("prioridade", "Média"), "#8e8e93")
                descricao_html = (
                    f"<div style='font-size:12px; color:#6e6e73; margin:4px 0 8px 0; line-height:1.4;'>{tf['descricao']}</div>"
                    if tf.get("descricao") else ""
                )
                st.markdown(f"""
                <div class="cartao-imla" style="border-left: 4px solid {cor_prio}; padding:12px 14px;">
                    <div style="font-weight:700; font-size:13px; color:#1d1d1f;">{tf['titulo']}</div>
                    {descricao_html}
                    <span style="display:inline-block; font-size:10px; font-weight:700; color:white;
                        background:{cor_prio}; padding:2px 8px; border-radius:6px;">{tf.get('prioridade', 'Média')}</span>
                    <div style="font-size:10px; color:#9099a8; margin-top:8px;">
                        {tf.get('autor_nome', '—')} · {tf.get('data_hora', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)


def renderizar_aba_solicitacoes(usuario: dict, n_sel: str, pode_editar: bool) -> None:
    """Aba de Solicitações: enviar mensagens a outros núcleos e ver a caixa
    de entrada do núcleo atual (restrita a quem pertence a ele)."""
    if not pode_editar:
        st.caption("🔒 A caixa de solicitações é restrita aos membros deste núcleo.")
        return

    with st.form("form_solicitacao", clear_on_submit=True):
        destino = st.selectbox("Para qual núcleo?", list(NUCLEOS_INFO.keys()))
        assunto = st.text_input("Assunto")
        mensagem = st.text_area("Mensagem")
        if st.form_submit_button("Enviar") and assunto.strip():
            st.session_state.caixa_entrada[destino].append({
                "assunto": assunto.strip(),
                "mensagem": mensagem.strip(),
                "data": agora_br().strftime("%d/%m/%Y %H:%M"),
                "de_nome": usuario["nome"],
                "de_nucleo": usuario["nucleo"],
            })
            salvar_banco()
            st.success("Solicitação enviada com sucesso!")

    st.write("")
    st.markdown("##### Caixa de entrada")
    caixa = st.session_state.caixa_entrada[n_sel]
    if not caixa:
        st.caption("Nenhuma solicitação recebida ainda.")
    for m in reversed(caixa):
        with st.expander(f"📩 {m['assunto']} — de {m.get('de_nome', '—')} ({m.get('de_nucleo', '')})"):
            st.write(m["mensagem"])
            st.caption(m["data"])


def renderizar_area_logada() -> None:
    aplicar_estilo_area_logada()
    usuario = st.session_state.usuario_logado
    n_sel = st.session_state.nucleo_selecionado
    pode_editar = usuario["nucleo"] == n_sel

    renderizar_app_bar(usuario)
    renderizar_banner()

    st.markdown(f"### {NUCLEOS_INFO.get(n_sel, '')} {n_sel}")
    if not pode_editar:
        st.caption(f"Você está visualizando este núcleo como leitor — seu núcleo é {usuario['nucleo']}.")

    aba_feed, aba_tarefas, aba_solicitacoes = st.tabs(["Feed", "Tarefas", "Solicitações"])

    with aba_feed:
        renderizar_aba_feed(usuario, n_sel, pode_editar)

    with aba_tarefas:
        renderizar_aba_tarefas(n_sel, pode_editar)

    with aba_solicitacoes:
        renderizar_aba_solicitacoes(usuario, n_sel, pode_editar)


# ============================================================================
# --- 8. ROTEAMENTO PRINCIPAL -------------------------------------------------
# ============================================================================
if st.session_state.usuario_logado is None:
    renderizar_area_publica()
else:
    renderizar_area_logada()
