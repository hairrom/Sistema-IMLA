import streamlit as st
import datetime
from zoneinfo import ZoneInfo
import os
import json
import base64
import io
import uuid
import hashlib
import secrets
from PIL import Image
import streamlit.components.v1 as components

FUSO_BR = ZoneInfo("America/Bahia")


def agora_br():
    """Retorna a data/hora certa do Brasil (Bahia), independente do fuso do servidor."""
    return datetime.datetime.now(FUSO_BR)


def hash_senha(senha, salt=None):
    """Gera um hash seguro (PBKDF2) da senha, nunca guardando a senha em texto puro."""
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return salt, h.hex()


def verificar_senha(senha, salt, hash_esperado):
    _, h = hash_senha(senha, salt)
    return secrets.compare_digest(h, hash_esperado)

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Sistema IMLA",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

ARQUIVO_BANCO = "banco_iml.json"
LOGO_PATH = "Submarca 01.png"
LOGIN_BG_PATH = "IMG_3987.JPG"
BANNER_PATH = "IMG_3985.JPG"

NUCLEOS_INFO = {
    "Cozinha e Nutrição": "🍳",
    "Comunicação": "📣",
    "Pedagógico": "📚",
    "Captação de Recursos": "🤝",
    "Financeiro": "💰",
    "Apadrinhamento": "💌",
}

STATUS_OPCOES = ["Criada", "Em andamento", "Concluída"]
PRIORIDADE_OPCOES = ["Baixa", "Média", "Alta"]
PRIORIDADE_COR = {"Baixa": "#34c759", "Média": "#ff9f0a", "Alta": "#ff3b30"}
STATUS_COR = {"Criada": "#8e8e93", "Em andamento": "#0071e3", "Concluída": "#34c759"}

TEXTOS = {
    "pt": {
        "titulo_sistema": "Sistema IMLA",
        "subtitulo": "Onde nós trabalhamos",
        "sair": "Sair",
        "encolher": "Encolher",
        "perfil": "Perfil",
        "logado_como": "Conectado como",
        "nucleo_label": "Núcleo",
        "email_label": "E-mail",
        "buscar_placeholder": "Buscar...",
        "aba_novidades": "As novidades",
        "aba_tarefas": "Demandas",
        "aba_lembretes": "Lembretes",
        "aba_solicitacoes": "Solicitações",
        "compartilhar": "Compartilhar algo novo",
        "publicar": "Publicar",
        "acessar_drive": "📂 Acessar Drive",
        "cronogramas": "📊 Cronogramas",
        "restrito_links": "🔒 Faça login para acessar o Drive e as planilhas.",
        "nova_demanda": "Nova demanda",
        "titulo_demanda": "Título da demanda",
        "descricao_demanda": "Descrição (o que precisa ser feito)",
        "prioridade": "Prioridade",
        "adicionar_demanda": "+ Adicionar demanda",
        "criado_por": "Criado por",
        "editar": "✏️ Editar",
        "salvar": "Salvar alterações",
        "excluir_tarefa": "🗑️ Excluir tarefa",
        "excluir_lembrete": "🗑️ Excluir lembrete",
        "status": "Status",
        "restrito_edicao": "🔒 Apenas membros deste núcleo podem editar.",
        "novo_lembrete": "Novo lembrete",
        "titulo_lembrete": "Nome da tarefa recorrente",
        "descricao_lembrete": "O que precisa ser feito",
        "proxima_data": "Próxima data",
        "adicionar_lembrete": "💾 Salvar",
        "sem_lembretes": "Nenhum lembrete cadastrado.",
        "enviar_solicitacao": "Enviar solicitação",
        "para_nucleo": "Para qual núcleo?",
        "assunto": "Assunto",
        "mensagem": "Mensagem",
        "visibilidade": "Visibilidade",
        "publica": "Pública (todos podem ver)",
        "privada": "Privada (só o núcleo destino)",
        "enviar": "Enviar",
        "enviado": "Enviado com sucesso!",
        "caixa_entrada": "Caixa de Entrada",
        "restrito_caixa": "🔒 Restrito aos membros deste núcleo.",
        "visitante_solicitacoes": "👁️ Você está vendo apenas as solicitações públicas deste núcleo.",
        "de": "De",
    },
    "en": {
        "titulo_sistema": "IMLA System",
        "subtitulo": "Where we work",
        "sair": "Log out",
        "encolher": "Collapse",
        "perfil": "Profile",
        "logado_como": "Signed in as",
        "nucleo_label": "Team",
        "email_label": "E-mail",
        "buscar_placeholder": "Search...",
        "aba_novidades": "Updates",
        "aba_tarefas": "Tasks",
        "aba_lembretes": "Reminders",
        "aba_solicitacoes": "Requests",
        "compartilhar": "Share something new",
        "publicar": "Post",
        "acessar_drive": "📂 Open Drive",
        "cronogramas": "📊 Timelines",
        "restrito_links": "🔒 Log in to access Drive and spreadsheets.",
        "nova_demanda": "New task",
        "titulo_demanda": "Task title",
        "descricao_demanda": "Description (what needs to be done)",
        "prioridade": "Priority",
        "adicionar_demanda": "+ Add task",
        "criado_por": "Created by",
        "editar": "✏️ Edit",
        "salvar": "Save changes",
        "excluir_tarefa": "🗑️ Delete task",
        "excluir_lembrete": "🗑️ Delete reminder",
        "status": "Status",
        "restrito_edicao": "🔒 Only members of this team can edit.",
        "novo_lembrete": "New reminder",
        "titulo_lembrete": "Recurring task name",
        "descricao_lembrete": "What needs to be done",
        "proxima_data": "Next date",
        "adicionar_lembrete": "💾 Save",
        "sem_lembretes": "No reminders yet.",
        "enviar_solicitacao": "Send request",
        "para_nucleo": "Which team?",
        "assunto": "Subject",
        "mensagem": "Message",
        "visibilidade": "Visibility",
        "publica": "Public (everyone can see)",
        "privada": "Private (destination team only)",
        "enviar": "Send",
        "enviado": "Sent successfully!",
        "caixa_entrada": "Inbox",
        "restrito_caixa": "🔒 Restricted to members of this team.",
        "visitante_solicitacoes": "👁️ You're seeing only the public requests for this team.",
        "de": "From",
    }
}


def t(chave):
    idioma = st.session_state.get("idioma", "pt")
    return TEXTOS.get(idioma, TEXTOS["pt"]).get(chave, chave)


# ==========================================
# 2. BANCO DE DADOS (Persistência em JSON)
# ==========================================
def estrutura_padrao_nucleo():
    return {
        "atualizacoes": [], "tarefas": [], "lembretes": [],
        "drive": "https://drive.google.com", "planilha": "https://docs.google.com"
    }


def carregar_banco():
    if os.path.exists(ARQUIVO_BANCO):
        with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
            dados = json.load(f)
    else:
        dados = {
            "usuarios": {},
            "nucleos_dados": {n: estrutura_padrao_nucleo() for n in NUCLEOS_INFO},
            "caixa_entrada": {n: [] for n in NUCLEOS_INFO}
        }

    # --- Migração / compatibilidade com bancos antigos ---

    # 1º: garante que TODO usuário já tenha o campo "nome" antes de qualquer
    # outra parte do código tentar ler usuario["nome"] (evita KeyError).
    for email, u in dados.get("usuarios", {}).items():
        u.setdefault("nome", (u.get("email") or email).split("@")[0].title())
        u.setdefault("email", email)

    for n in NUCLEOS_INFO:
        dados.setdefault("nucleos_dados", {}).setdefault(n, estrutura_padrao_nucleo())
        dados["caixa_entrada"] = dados.get("caixa_entrada", {})
        dados["caixa_entrada"].setdefault(n, [])

        nd = dados["nucleos_dados"][n]
        nd.setdefault("lembretes", [])
        for msg in dados["caixa_entrada"].get(n, []):
            msg.setdefault("publica", False)
        # tarefas antigas eram apenas strings -> converte para o formato novo (Trello-like)
        novas_tarefas = []
        for tarefa in nd.get("tarefas", []):
            if isinstance(tarefa, str):
                novas_tarefas.append({
                    "id": str(uuid.uuid4())[:8],
                    "titulo": tarefa,
                    "status": "Criada",
                    "prioridade": "Média",
                    "descricao": "",
                    "autor_nome": "—",
                    "data_hora": ""
                })
            else:
                tarefa.setdefault("id", str(uuid.uuid4())[:8])
                tarefa.setdefault("status", "Criada")
                tarefa.setdefault("prioridade", "Média")
                tarefa.setdefault("descricao", "")
                tarefa.setdefault("autor_nome", tarefa.get("autor", "—"))
                tarefa.setdefault("data_hora", tarefa.get("data", ""))
                novas_tarefas.append(tarefa)
        nd["tarefas"] = novas_tarefas

        # posts antigos guardavam e-mail como autor -> mantém compatível
        for post in nd.get("atualizacoes", []):
            if not post.get("autor_nome"):
                autor_antigo = post.get("autor", "—")
                usuario_ref = dados.get("usuarios", {}).get(autor_antigo)
                post["autor_nome"] = usuario_ref.get("nome", autor_antigo) if usuario_ref else autor_antigo

    return dados


def salvar_banco():
    dados = {
        "usuarios": st.session_state.usuarios,
        "nucleos_dados": st.session_state.nucleos_dados,
        "caixa_entrada": st.session_state.caixa_entrada
    }
    with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)


if "dados_carregados" not in st.session_state:
    dados = carregar_banco()
    st.session_state.usuarios = dados["usuarios"]
    st.session_state.nucleos_dados = dados["nucleos_dados"]
    st.session_state.caixa_entrada = dados["caixa_entrada"]
    st.session_state.dados_carregados = True

if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "modo_tela" not in st.session_state: st.session_state.modo_tela = "login"
if "nucleo_selecionado" not in st.session_state: st.session_state.nucleo_selecionado = "Comunicação"
if "idioma" not in st.session_state: st.session_state.idioma = "pt"
if "busca" not in st.session_state: st.session_state.busca = ""
if "mostrar_perfil" not in st.session_state: st.session_state.mostrar_perfil = False


# ==========================================
# 3. HELPERS DE IMAGEM
# ==========================================
@st.cache_data(show_spinner=False)
def imagem_base64(caminho):
    if not os.path.exists(caminho):
        return None
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode()


@st.cache_data(show_spinner=False)
def logo_simbolo_base64(caminho):
    """Se o arquivo já for só o símbolo (proporção quase quadrada), usa como está.
    Se for um logotipo largo (ícone + nome escrito ao lado), corta e mantém só o
    quadrado da esquerda, descartando o texto."""
    if not os.path.exists(caminho):
        return None
    im = Image.open(caminho).convert("RGBA")
    w, h = im.size
    if w > h * 1.15:
        im = im.crop((0, 0, h, h))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@st.cache_data(show_spinner=False)
def banner_base64(caminho, proporcao=21 / 6):
    """Recorta a imagem para o formato padrão de banner de site (bem panorâmico) e retorna em base64."""
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


# ==========================================
# ÁREA PÚBLICA (LOGIN / CADASTRO)
# ==========================================
if st.session_state.usuario_logado is None:

    login_bg = imagem_base64(LOGIN_BG_PATH)
    bg_css = f"url(data:image/jpeg;base64,{login_bg})" if login_bg else "none"

    st.markdown(f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(0,0,0,0.55), rgba(0,0,0,0.8)), {bg_css};
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        header {{visibility: hidden;}}

        html, body, [class*="css"] {{
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", Helvetica, Arial, sans-serif !important;
        }}

        .login-container {{ margin-top: -20px; }}

        .stTextInput>div>div>input {{
            background-color: #ffffff !important;
            border: 1px solid #d2d2d7 !important;
            border-radius: 10px !important;
            color: #1d1d1f !important;
        }}
        .stSelectbox>div>div>div {{
            background-color: #ffffff !important;
            border-radius: 10px !important;
            color: #1d1d1f !important;
        }}

        p, label, h2, h4 {{ color: white !important; }}

        .stButton>button {{
            border-radius: 980px !important;
            font-weight: 600 !important;
            background-color: #ffffff !important;
            color: #1d1d1f !important;
            border: none !important;
            padding: 0.5rem 1.4rem !important;
        }}
        .stButton>button * {{ color: #1d1d1f !important; }}
        .stButton>button:hover {{ background-color: #f2f2f2 !important; }}
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2, 1, 1.2])

    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.write("")

        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, use_container_width=True)
        else:
            st.markdown("<h2 style='text-align:center;'>Sistema IMLA</h2>", unsafe_allow_html=True)

        if st.session_state.modo_tela == "login":
            st.markdown("<h4 style='text-align:center; font-size:18px;'>Acesso ao Sistema IMLA</h4>", unsafe_allow_html=True)
            usuario_email = st.text_input("Seu Email:")
            senha_login = st.text_input("Senha:", type="password")

            if st.button("Entrar", use_container_width=True):
                chave = usuario_email.strip().lower()
                if chave in st.session_state.usuarios:
                    u = st.session_state.usuarios[chave]
                    senha_ok = False
                    if "senha_hash" in u:
                        senha_ok = verificar_senha(senha_login, u["salt"], u["senha_hash"])
                    elif "senha" in u:
                        # conta antiga em texto puro: valida e migra para hash na hora
                        senha_ok = (u["senha"] == senha_login)
                        if senha_ok:
                            salt, h = hash_senha(senha_login)
                            u["salt"], u["senha_hash"] = salt, h
                            u.pop("senha", None)
                            salvar_banco()
                    if senha_ok:
                        st.session_state.usuario_logado = u
                        st.session_state.nucleo_selecionado = u["nucleo"]
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
                else:
                    st.error("Email não encontrado.")

            st.markdown("<p style='text-align:center; font-size:12px; margin-top:10px;'>Ainda não tem acesso?</p>", unsafe_allow_html=True)
            if st.button("Criar nova conta", use_container_width=True):
                st.session_state.modo_tela = "cadastro"
                st.rerun()

            st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.25); margin:14px 0;'></div>", unsafe_allow_html=True)
            if st.button("👁️ Entrar como visitante", use_container_width=True):
                st.session_state.usuario_logado = {
                    "nome": "Visitante",
                    "email": None,
                    "nucleo": None,
                    "visitante": True
                }
                st.session_state.nucleo_selecionado = list(NUCLEOS_INFO.keys())[0]
                st.rerun()

        else:
            st.markdown("<h4 style='text-align:center; font-size:18px;'>Novo Cadastro</h4>", unsafe_allow_html=True)
            novo_nome = st.text_input("Nome completo:")
            novo_email = st.text_input("Seu melhor email:")
            novo_nucleo = st.selectbox("Núcleo que pertence:", list(NUCLEOS_INFO.keys()))
            nova_senha = st.text_input("Senha:", type="password")
            confirmar_senha = st.text_input("Confirmar senha:", type="password")

            if st.button("Finalizar Cadastro", use_container_width=True):
                chave = novo_email.strip().lower()
                if not (novo_nome.strip() and chave and nova_senha.strip() and confirmar_senha.strip()):
                    st.error("Preencha todos os campos.")
                elif nova_senha != confirmar_senha:
                    st.error("As senhas não coincidem.")
                elif chave in st.session_state.usuarios:
                    st.warning("Este email já está cadastrado.")
                else:
                    salt, h = hash_senha(nova_senha)
                    st.session_state.usuarios[chave] = {
                        "nome": novo_nome.strip(),
                        "email": chave,
                        "nucleo": novo_nucleo,
                        "salt": salt,
                        "senha_hash": h
                    }
                    salvar_banco()
                    st.success("Cadastro realizado!")
                    st.session_state.modo_tela = "login"
                    st.rerun()

            if st.button("Voltar", use_container_width=True):
                st.session_state.modo_tela = "login"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# ÁREA PRIVADA (SISTEMA INTERNO)
# ==========================================
else:
    usuario = st.session_state.usuario_logado
    n_sel = st.session_state.nucleo_selecionado
    logo_simbolo_b64 = logo_simbolo_base64(LOGO_PATH)
    banner_b64 = banner_base64(BANNER_PATH)
    iniciais = "".join([p[0].upper() for p in usuario["nome"].split()[:2]]) or "?"
    eh_visitante = bool(usuario.get("visitante"))

    # Camada extra de dificuldade contra inspeção casual (não é segurança real).
    components.html("""
    <script>
    (function() {
        try {
            const doc = window.parent.document;
            doc.addEventListener('contextmenu', function(e){ e.preventDefault(); });
            doc.addEventListener('keydown', function(e) {
                if (e.key === 'F12') e.preventDefault();
                if (e.ctrlKey && e.shiftKey && ['I','J','C'].includes(e.key)) e.preventDefault();
                if (e.ctrlKey && e.key === 'u') e.preventDefault();
            });
        } catch (err) {}
    })();
    </script>
    """, height=0, width=0)

    st.markdown(f"""
        <style>
        .stApp {{ background: #fafafa !important; }}
        header {{visibility: hidden;}}

        html, body, [class*="css"] {{
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", Helvetica, Arial, sans-serif !important;
        }}
        h2, h3, h4, p, span {{ color: #1d1d1f !important; }}

        .block-container {{ padding-top: 0.5rem !important; }}

        /* ---------- NAVBAR (agora com botões reais do Streamlit, sem reload de página) ---------- */
        div[data-testid="stVerticalBlock"]:has(> div.element-container > div.stMarkdown > div > div.navbar-anchor) {{
            display: none;
        }}

        .st-key-navbar_container {{
            position: sticky;
            top: 8px;
            z-index: 9999;
            background: rgba(255,255,255,0.9);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-radius: 24px;
            border: 1px solid rgba(0,0,0,0.06);
            box-shadow: 0 8px 30px rgba(0,0,0,0.14);
            padding: 10px 16px;
            margin-bottom: 18px;
        }}
        .st-key-navbar_container .stButton>button {{
            border-radius: 980px !important;
            font-size: 12.5px !important;
            font-weight: 600 !important;
            padding: 0.4rem 0.9rem !important;
            border: none !important;
            white-space: nowrap;
        }}
        .st-key-navbar_container button[kind="secondary"] {{
            background-color: rgba(0,0,0,0.05) !important;
            color: #1d1d1f !important;
        }}
        .st-key-navbar_container button[kind="secondary"]:hover {{
            background-color: rgba(0,0,0,0.1) !important;
        }}
        .st-key-navbar_container button[kind="primary"] {{
            background-color: #1d1d1f !important;
            color: #ffffff !important;
        }}
        .st-key-perfil_btn_col .stButton>button {{
            border-radius: 50% !important;
            width: 38px !important; height: 38px !important;
            padding: 0 !important;
            background-color: #0071e3 !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            border: none !important;
        }}

        .st-key-perfil_painel {{
            position: fixed;
            top: 74px; right: 22px;
            z-index: 10000;
            background: #ffffff;
            border-radius: 18px;
            box-shadow: 0 12px 34px rgba(0,0,0,0.25);
            padding: 16px 18px;
            width: 240px;
        }}
        .st-key-perfil_painel .stButton>button {{
            border-radius: 980px !important;
            font-size: 12.5px !important;
            padding: 0.35rem 0 !important;
        }}

        /* ---------- BANNER ---------- */
        .banner-imla {{
            width: 100%; height: 240px; border-radius: 24px; overflow:hidden;
            background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.75)), url(data:image/jpeg;base64,{banner_b64 if banner_b64 else ''});
            background-size: cover; background-position: center;
            display:flex; align-items:flex-end; padding: 26px 34px;
        }}
        .banner-imla h1 {{
            color:#ffffff !important; font-size: 40px; margin:0; font-weight:700 !important;
            text-shadow: 0 2px 14px rgba(0,0,0,0.7);
        }}
        .banner-imla p {{
            color: #ffffff !important; margin:0; font-size:15px; opacity:0.95;
            text-shadow: 0 1px 10px rgba(0,0,0,0.65);
        }}

        div.stButton > button:first-child {{
            transition: 0.2s;
        }}

        .apple-card {{
            background: #ffffff; border-radius: 20px; padding: 22px; margin-bottom: 18px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
            border: 1px solid rgba(0,0,0,0.02);
        }}
        .card-tag {{ font-size: 11px; font-weight: 700; color: #59c2d1; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 5px;}}
        .card-title {{ font-size: 16px; font-weight: 600; margin-bottom: 8px;}}
        .card-text {{ font-size: 14px; color: #515154; line-height: 1.5;}}
        .card-footer {{ font-size: 10px; color: #86868b; margin-top: 14px;}}

        /* ---------- CARDS DE TAREFA (TRELLO-LIKE) ---------- */
        .task-card {{
            background:#fff; border-radius:16px; padding:14px 16px; margin-bottom:12px;
            box-shadow:0 2px 10px rgba(0,0,0,0.05); border-left: 5px solid #ccc;
        }}
        .task-titulo {{ font-weight:600; font-size:14px; margin-bottom:6px; }}
        .task-desc {{ font-size:12.5px; color:#6e6e73; line-height:1.4; margin-bottom:8px; }}
        .chip {{
            display:inline-block; font-size:10.5px; font-weight:700; color:white; padding:3px 9px;
            border-radius:980px; margin-right:6px;
        }}
        .task-footer {{ font-size:10.5px; color:#86868b; margin-top:10px; }}
        .kanban-col-title {{ font-size:13px; font-weight:700; color:#6e6e73; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:10px;}}

        /* ---------- LEMBRETES ---------- */
        .lembrete-card {{
            background:#fff; border-radius:16px; padding:14px 16px; margin-bottom:12px;
            box-shadow:0 2px 10px rgba(0,0,0,0.05); border-left: 5px solid #0071e3;
        }}
        .lembrete-titulo {{ font-weight:600; font-size:14px; margin-bottom:6px; }}
        .lembrete-desc {{ font-size:12.5px; color:#6e6e73; line-height:1.4; margin-bottom:8px; }}
        .lembrete-data {{
            display:inline-block; font-size:11px; font-weight:700; color:#0071e3;
            background:rgba(0,113,227,0.1); padding:4px 10px; border-radius:980px;
        }}
        .lembrete-data.atrasado {{ color:#ff3b30; background:rgba(255,59,48,0.1); }}

        /* ---------- ABAS: impede corte/truncamento de texto ---------- */
        .stTabs [data-baseweb="tab"] {{
            white-space: nowrap !important;
            padding: 0 16px !important;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            overflow-x: auto !important;
        }}

        /* ---------- RESPONSIVO (CELULAR) ---------- */
        @media (max-width: 700px) {{
            .st-key-navbar_container {{ padding: 6px 10px; border-radius: 20px; top: 4px; }}
            .banner-imla {{ height: 190px; padding: 18px 20px; border-radius:18px; }}
            .banner-imla h1 {{ font-size: 26px; }}
            .banner-imla p {{ font-size: 12px; }}
        }}

        </style>
    """, unsafe_allow_html=True)

    # ---------- NAVBAR (contêiner real do Streamlit, sem <a href> nem reload) ----------
    with st.container(key="navbar_container"):
        n_nucleos = len(NUCLEOS_INFO)
        larguras = [0.7] + [1] * n_nucleos + [0.5]
        cols = st.columns(larguras, vertical_alignment="center")

        with cols[0]:
            if logo_simbolo_b64:
                st.image(f"data:image/png;base64,{logo_simbolo_b64}")

        for i, (nome, emoji) in enumerate(NUCLEOS_INFO.items(), start=1):
            with cols[i]:
                tipo_botao = "primary" if nome == n_sel else "secondary"
                if st.button(f"{emoji} {nome}", key=f"nuc_{nome}", type=tipo_botao, use_container_width=True):
                    st.session_state.nucleo_selecionado = nome
                    st.session_state.mostrar_perfil = False
                    st.rerun()

        with cols[-1]:
            with st.container(key="perfil_btn_col"):
                rotulo_avatar = "👁️" if eh_visitante else iniciais
                if st.button(rotulo_avatar, key="btn_abrir_perfil"):
                    st.session_state.mostrar_perfil = not st.session_state.mostrar_perfil
                    st.rerun()

    # ---------- PAINEL DE PERFIL (aparece/some com botão, sem bug de HTML cru) ----------
    if st.session_state.mostrar_perfil:
        with st.container(key="perfil_painel"):
            if eh_visitante:
                st.markdown("**👁️ Modo Visitante**")
                st.caption("Você está vendo o sistema apenas para leitura.")
            else:
                st.markdown(f"**{usuario['nome']}**")
                st.caption(f"{t('email_label')}: {usuario['email']}")
                st.caption(f"{t('nucleo_label')}: {NUCLEOS_INFO.get(usuario['nucleo'],'')} {usuario['nucleo']}")

            c_enc, c_sair = st.columns(2)
            with c_enc:
                if st.button(t("encolher"), key="btn_encolher", use_container_width=True):
                    st.session_state.mostrar_perfil = False
                    st.rerun()
            with c_sair:
                if st.button(t("sair"), key="btn_sair", use_container_width=True, type="primary"):
                    st.session_state.usuario_logado = None
                    st.session_state.mostrar_perfil = False
                    st.rerun()

    # ---------- BANNER ----------
    st.markdown(f"""
        <div class="banner-imla">
            <div>
                <h1>{t('titulo_sistema')}</h1>
                <p>{t('subtitulo')}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown(f"<h2 style='font-size: 30px;'>{NUCLEOS_INFO.get(n_sel,'')} {n_sel}</h2>", unsafe_allow_html=True)

    aba_feed, aba_tarefas, aba_lembretes, aba_solicitacoes = st.tabs(
        [t("aba_novidades"), t("aba_tarefas"), t("aba_lembretes"), t("aba_solicitacoes")]
    )

    # ---------- PERMISSÕES ----------
    # pode_editar: só quem fez login E está vendo o próprio núcleo pode criar/editar/excluir.
    pode_editar = (not eh_visitante) and (usuario.get("nucleo") == n_sel)
    # pode_ver_links: qualquer pessoa logada pode abrir Drive/Planilhas em qualquer núcleo,
    # mas o visitante nunca pode.
    pode_ver_links = not eh_visitante

    # ================= ABA NOVIDADES =================
    with aba_feed:
        if pode_editar:
            with st.form("form_novo"):
                texto = st.text_area(t("compartilhar") + ":")
                if st.form_submit_button(t("publicar")) and texto.strip():
                    agora = agora_br().strftime("%d/%m/%Y %H:%M")
                    st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {
                        "texto": texto,
                        "data": agora,
                        "autor_nome": usuario["nome"],
                        "autor_email": usuario.get("email")
                    })
                    salvar_banco()
                    st.rerun()

        st.write("")
        col_c1, col_c2, col_c3 = st.columns(3)
        posts = st.session_state.nucleos_dados[n_sel]["atualizacoes"]

        if not posts:
            st.caption("Nenhuma atualização ainda.")

        for i, p in enumerate(posts):
            col = [col_c1, col_c2, col_c3][i % 3]
            with col:
                st.markdown(f"""
                <div class='apple-card'>
                    <div class='card-tag'>NOVO</div>
                    <div class='card-title'>{p.get('autor_nome','—')}</div>
                    <div class='card-text'>{p['texto']}</div>
                    <div class='card-footer'>{p['data']}</div>
                </div>
                """, unsafe_allow_html=True)

    # ================= ABA TAREFAS (ESTILO TRELLO) =================
    with aba_tarefas:
        if pode_ver_links:
            c_link1, c_link2 = st.columns(2)
            c_link1.link_button(t("acessar_drive"), st.session_state.nucleos_dados[n_sel]["drive"])
            c_link2.link_button(t("cronogramas"), st.session_state.nucleos_dados[n_sel]["planilha"])
        else:
            st.caption(t("restrito_links"))
        st.divider()

        if pode_editar:
            with st.expander(f"➕ {t('nova_demanda')}"):
                with st.form("form_nova_tarefa", clear_on_submit=True):
                    novo_titulo = st.text_input(t("titulo_demanda"))
                    nova_descricao = st.text_area(t("descricao_demanda"))
                    nova_prioridade = st.selectbox(t("prioridade"), PRIORIDADE_OPCOES, index=1)
                    if st.form_submit_button(t("adicionar_demanda")) and novo_titulo.strip():
                        agora = agora_br().strftime("%d/%m/%Y %H:%M")
                        st.session_state.nucleos_dados[n_sel]["tarefas"].append({
                            "id": str(uuid.uuid4())[:8],
                            "titulo": novo_titulo.strip(),
                            "descricao": nova_descricao.strip(),
                            "status": "Criada",
                            "prioridade": nova_prioridade,
                            "autor_nome": usuario["nome"],
                            "data_hora": agora
                        })
                        salvar_banco()
                        st.rerun()
        else:
            st.caption(t("restrito_edicao"))

        tarefas = st.session_state.nucleos_dados[n_sel]["tarefas"]

        col_k1, col_k2, col_k3 = st.columns(3)
        colunas_kanban = {STATUS_OPCOES[0]: col_k1, STATUS_OPCOES[1]: col_k2, STATUS_OPCOES[2]: col_k3}

        for status_nome, coluna in colunas_kanban.items():
            with coluna:
                st.markdown(f"<div class='kanban-col-title'>{status_nome}</div>", unsafe_allow_html=True)
                tarefas_col = [tf for tf in tarefas if tf.get("status") == status_nome]
                if not tarefas_col:
                    st.caption("—")
                for tf in tarefas_col:
                    cor_prio = PRIORIDADE_COR.get(tf.get("prioridade", "Média"), "#8e8e93")
                    descricao_html = f"<div class='task-desc'>{tf['descricao']}</div>" if tf.get("descricao") else ""
                    st.markdown(f"""
                    <div class="task-card" style="border-left-color:{cor_prio};">
                        <div class="task-titulo">{tf['titulo']}</div>
                        {descricao_html}
                        <span class="chip" style="background:{cor_prio};">{tf.get('prioridade','Média')}</span>
                        <div class="task-footer">{t('criado_por')} {tf.get('autor_nome','—')} · {tf.get('data_hora','')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if pode_editar:
                        with st.expander(t("editar"), expanded=False):
                            with st.form(f"editar_{tf['id']}"):
                                titulo_edit = st.text_input(t("titulo_demanda"), value=tf["titulo"], key=f"tit_{tf['id']}")
                                descricao_edit = st.text_area(t("descricao_demanda"), value=tf.get("descricao", ""), key=f"desc_{tf['id']}")
                                status_edit = st.selectbox(t("status"), STATUS_OPCOES, index=STATUS_OPCOES.index(tf.get("status", "Criada")), key=f"sta_{tf['id']}")
                                prio_edit = st.selectbox(t("prioridade"), PRIORIDADE_OPCOES, index=PRIORIDADE_OPCOES.index(tf.get("prioridade", "Média")), key=f"pri_{tf['id']}")
                                col_salvar, col_excluir = st.columns(2)
                                salvar_clicado = col_salvar.form_submit_button(t("salvar"))
                                excluir_clicado = col_excluir.form_submit_button(t("excluir_tarefa"))
                                if salvar_clicado:
                                    tf["titulo"] = titulo_edit.strip() or tf["titulo"]
                                    tf["descricao"] = descricao_edit.strip()
                                    tf["status"] = status_edit
                                    tf["prioridade"] = prio_edit
                                    salvar_banco()
                                    st.rerun()
                                if excluir_clicado:
                                    st.session_state.nucleos_dados[n_sel]["tarefas"] = [
                                        x for x in st.session_state.nucleos_dados[n_sel]["tarefas"] if x["id"] != tf["id"]
                                    ]
                                    salvar_banco()
                                    st.rerun()

    # ================= ABA LEMBRETES (DEMANDAS RECORRENTES) =================
    with aba_lembretes:
        if pode_editar:
            with st.expander(f"➕ {t('novo_lembrete')}"):
                with st.form("form_novo_lembrete", clear_on_submit=True):
                    lem_titulo = st.text_input(t("titulo_lembrete"))
                    lem_descricao = st.text_area(t("descricao_lembrete"))
                    lem_data = st.date_input(t("proxima_data"), value=datetime.date.today())
                    if st.form_submit_button(t("adicionar_lembrete")) and lem_titulo.strip():
                        st.session_state.nucleos_dados[n_sel].setdefault("lembretes", []).append({
                            "id": str(uuid.uuid4())[:8],
                            "titulo": lem_titulo.strip(),
                            "descricao": lem_descricao.strip(),
                            "proxima_data": lem_data.isoformat(),
                            "autor_nome": usuario["nome"],
                            "data_criacao": agora_br().strftime("%d/%m/%Y %H:%M")
                        })
                        salvar_banco()
                        st.rerun()
        else:
            st.caption(t("restrito_edicao"))

        lembretes = st.session_state.nucleos_dados[n_sel].setdefault("lembretes", [])
        lembretes_ordenados = sorted(lembretes, key=lambda l: l.get("proxima_data", ""))

        if not lembretes_ordenados:
            st.caption(t("sem_lembretes"))

        hoje = agora_br().date()
        for lm in lembretes_ordenados:
            try:
                data_lm = datetime.date.fromisoformat(lm.get("proxima_data", ""))
                data_fmt = data_lm.strftime("%d/%m/%Y")
                atrasado = data_lm < hoje
            except ValueError:
                data_fmt = lm.get("proxima_data", "—")
                atrasado = False

            descricao_html = f"<div class='lembrete-desc'>{lm['descricao']}</div>" if lm.get("descricao") else ""
            classe_data = "lembrete-data atrasado" if atrasado else "lembrete-data"
            rotulo_data = f"⚠️ {data_fmt}" if atrasado else f"📅 {data_fmt}"

            st.markdown(f"""
            <div class="lembrete-card">
                <div class="lembrete-titulo">{lm['titulo']}</div>
                {descricao_html}
                <span class="{classe_data}">{rotulo_data}</span>
                <div class="task-footer">{t('criado_por')} {lm.get('autor_nome','—')}</div>
            </div>
            """, unsafe_allow_html=True)

            if pode_editar:
                with st.expander(t("editar"), expanded=False):
                    with st.form(f"editar_lembrete_{lm['id']}"):
                        tit_edit = st.text_input(t("titulo_lembrete"), value=lm["titulo"], key=f"lt_{lm['id']}")
                        desc_edit = st.text_area(t("descricao_lembrete"), value=lm.get("descricao", ""), key=f"ld_{lm['id']}")
                        try:
                            data_atual = datetime.date.fromisoformat(lm.get("proxima_data", ""))
                        except ValueError:
                            data_atual = datetime.date.today()
                        data_edit = st.date_input(t("proxima_data"), value=data_atual, key=f"ldt_{lm['id']}")
                        col_s, col_e = st.columns(2)
                        salvar_lm = col_s.form_submit_button(t("adicionar_lembrete"))
                        excluir_lm = col_e.form_submit_button(t("excluir_lembrete"))
                        if salvar_lm:
                            lm["titulo"] = tit_edit.strip() or lm["titulo"]
                            lm["descricao"] = desc_edit.strip()
                            lm["proxima_data"] = data_edit.isoformat()
                            salvar_banco()
                            st.rerun()
                        if excluir_lm:
                            st.session_state.nucleos_dados[n_sel]["lembretes"] = [
                                x for x in st.session_state.nucleos_dados[n_sel]["lembretes"] if x["id"] != lm["id"]
                            ]
                            salvar_banco()
                            st.rerun()

    # ================= ABA SOLICITAÇÕES =================
    with aba_solicitacoes:
        if pode_editar:
            st.markdown(f"#### {t('enviar_solicitacao')}")
            with st.form("form_sol", clear_on_submit=True):
                dest = st.selectbox(t("para_nucleo"), list(NUCLEOS_INFO.keys()))
                assunto = st.text_input(t("assunto") + ":")
                msg = st.text_area(t("mensagem") + ":")
                visibilidade = st.radio(t("visibilidade"), [t("privada"), t("publica")], horizontal=True)
                if st.form_submit_button(t("enviar")) and assunto.strip():
                    agora = agora_br().strftime("%d/%m/%Y %H:%M")
                    st.session_state.caixa_entrada[dest].append({
                        "assunto": assunto,
                        "mensagem": msg,
                        "data": agora,
                        "de_nome": usuario["nome"],
                        "de_nucleo": usuario["nucleo"],
                        "publica": visibilidade == t("publica")
                    })
                    salvar_banco()
                    st.success(t("enviado"))

            st.write(f"### {t('caixa_entrada')}")
            caixa = st.session_state.caixa_entrada[n_sel]
            if not caixa:
                st.caption("Nenhuma solicitação recebida ainda.")
            for m in reversed(caixa):
                selo = "🌐 " if m.get("publica") else "🔒 "
                with st.expander(f"{selo}📩 {m['assunto']} ({t('de')}: {m.get('de_nome','—')} · {m.get('de_nucleo','')})"):
                    st.write(m['mensagem'])
                    st.caption(m['data'])
        else:
            st.caption(t("visitante_solicitacoes"))
            caixa_publica = [m for m in st.session_state.caixa_entrada[n_sel] if m.get("publica")]
            if not caixa_publica:
                st.caption("Nenhuma solicitação pública neste núcleo.")
            for m in reversed(caixa_publica):
                with st.expander(f"🌐 📩 {m['assunto']} ({t('de')}: {m.get('de_nome','—')} · {m.get('de_nucleo','')})"):
                    st.write(m['mensagem'])
                    st.caption(m['data'])
