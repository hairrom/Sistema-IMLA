import streamlit as st
import datetime
import os
import json
import base64
import io
import uuid
from PIL import Image

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
LOGO_PATH = "Logotipo Principal 01 (1).png"
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
        "perfil": "Perfil",
        "logado_como": "Conectado como",
        "nucleo_label": "Núcleo",
        "email_label": "E-mail",
        "buscar_placeholder": "Buscar...",
        "aba_novidades": "As novidades",
        "aba_tarefas": "Demandas",
        "aba_solicitacoes": "Solicitações",
        "compartilhar": "Compartilhar algo novo",
        "publicar": "Publicar",
        "acessar_drive": "📂 Acessar Drive",
        "cronogramas": "📊 Cronogramas",
        "nova_demanda": "Nova demanda",
        "titulo_demanda": "Título da demanda",
        "descricao_demanda": "Descrição (o que precisa ser feito)",
        "prioridade": "Prioridade",
        "adicionar_demanda": "+ Adicionar demanda",
        "criado_por": "Criado por",
        "editar": "✏️ Editar",
        "salvar": "Salvar alterações",
        "status": "Status",
        "restrito_edicao": "🔒 Apenas membros deste núcleo podem editar.",
        "enviar_solicitacao": "Enviar solicitação",
        "para_nucleo": "Para qual núcleo?",
        "assunto": "Assunto",
        "mensagem": "Mensagem",
        "enviar": "Enviar",
        "enviado": "Enviado com sucesso!",
        "caixa_entrada": "Caixa de Entrada",
        "restrito_caixa": "🔒 Restrito aos membros deste núcleo.",
        "de": "De",
    },
    "en": {
        "titulo_sistema": "IMLA System",
        "subtitulo": "Where we work",
        "sair": "Log out",
        "perfil": "Profile",
        "logado_como": "Signed in as",
        "nucleo_label": "Team",
        "email_label": "E-mail",
        "buscar_placeholder": "Search...",
        "aba_novidades": "Updates",
        "aba_tarefas": "Tasks",
        "aba_solicitacoes": "Requests",
        "compartilhar": "Share something new",
        "publicar": "Post",
        "acessar_drive": "📂 Open Drive",
        "cronogramas": "📊 Timelines",
        "nova_demanda": "New task",
        "titulo_demanda": "Task title",
        "descricao_demanda": "Description (what needs to be done)",
        "prioridade": "Priority",
        "adicionar_demanda": "+ Add task",
        "criado_por": "Created by",
        "editar": "✏️ Edit",
        "salvar": "Save changes",
        "status": "Status",
        "restrito_edicao": "🔒 Only members of this team can edit.",
        "enviar_solicitacao": "Send request",
        "para_nucleo": "Which team?",
        "assunto": "Subject",
        "mensagem": "Message",
        "enviar": "Send",
        "enviado": "Sent successfully!",
        "caixa_entrada": "Inbox",
        "restrito_caixa": "🔒 Restricted to members of this team.",
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
    return {"atualizacoes": [], "tarefas": [], "drive": "https://drive.google.com", "planilha": "https://docs.google.com"}


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
    """Extrai apenas o símbolo (ícone) do logotipo, cortando a parte quadrada da esquerda
    e descartando o nome 'Instituto Mãe Lalu' escrito ao lado. Assume o layout ícone + texto.
    Se o logotipo não seguir esse padrão, ajuste este recorte ou envie um arquivo já isolado."""
    if not os.path.exists(caminho):
        return None
    im = Image.open(caminho).convert("RGBA")
    w, h = im.size
    lado = min(w, h)
    recorte = im.crop((0, 0, lado, h))
    buf = io.BytesIO()
    recorte.save(buf, format="PNG")
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
# 4. PROCESSA PARÂMETROS DE NAVEGAÇÃO (barra flutuante em HTML puro)
# ==========================================
qp = st.query_params

if st.session_state.usuario_logado is not None:
    if qp.get("acao") == "sair":
        st.session_state.usuario_logado = None
        st.query_params.clear()
        st.rerun()

    if "nucleo" in qp and qp.get("nucleo") in NUCLEOS_INFO:
        st.session_state.nucleo_selecionado = qp.get("nucleo")
    if "idioma" in qp and qp.get("idioma") in ("pt", "en"):
        st.session_state.idioma = qp.get("idioma")
    if "busca" in qp:
        st.session_state.busca = qp.get("busca")


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
                    if st.session_state.usuarios[chave]["senha"] == senha_login:
                        st.session_state.usuario_logado = st.session_state.usuarios[chave]
                        st.session_state.nucleo_selecionado = st.session_state.usuarios[chave]["nucleo"]
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
                else:
                    st.error("Email não encontrado.")

            st.markdown("<p style='text-align:center; font-size:12px; margin-top:10px;'>Ainda não tem acesso?</p>", unsafe_allow_html=True)
            if st.button("Criar nova conta", use_container_width=True):
                st.session_state.modo_tela = "cadastro"
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
                    st.session_state.usuarios[chave] = {
                        "nome": novo_nome.strip(),
                        "email": chave,
                        "nucleo": novo_nucleo,
                        "senha": nova_senha
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
    idioma_atual = st.session_state.idioma
    idioma_alvo = "en" if idioma_atual == "pt" else "pt"
    logo_simbolo_b64 = logo_simbolo_base64(LOGO_PATH)
    banner_b64 = banner_base64(BANNER_PATH)
    iniciais = "".join([p[0].upper() for p in usuario["nome"].split()[:2]]) or "?"

    st.markdown(f"""
        <style>
        .stApp {{ background: #fafafa !important; }}
        header {{visibility: hidden;}}

        html, body, [class*="css"] {{
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", Helvetica, Arial, sans-serif !important;
        }}
        h1 {{ font-weight: 600 !important; color: #1d1d1f !important; }}
        h2, h3, h4, p, span {{ color: #1d1d1f !important; }}

        .block-container {{ padding-top: 0rem !important; }}

        /* ---------- ILHA FLUTUANTE (NAVBAR) ---------- */
        .ilha-flutuante {{
            position: fixed;
            top: 14px; left: 50%;
            transform: translateX(-50%);
            width: min(96%, 1200px);
            z-index: 9999;
            background: rgba(255,255,255,0.78);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-radius: 26px;
            border: 1px solid rgba(255,255,255,0.4);
            box-shadow: 0 8px 30px rgba(0,0,0,0.18);
            padding: 8px 16px;
            display: flex; align-items: center; gap: 10px;
            flex-wrap: wrap;
            row-gap: 8px;
        }}
        .ilha-logo {{ height: 30px; border-radius: 8px; flex-shrink:0; }}
        .ilha-nome {{ font-weight: 700; font-size: 15px; color:#1d1d1f; white-space:nowrap; }}
        .ilha-pills {{ display:flex; gap:5px; flex-wrap: wrap; }}
        .ilha-pill,
        .ilha-pill:link,
        .ilha-pill:visited,
        .ilha-pill:hover,
        .ilha-pill:active {{
            text-decoration:none !important;
            border-bottom:none !important;
            box-shadow:none;
        }}
        .ilha-pill {{
            font-size:12px; font-weight:600; color:#1d1d1f !important;
            background: rgba(0,0,0,0.05); padding:6px 11px; border-radius:980px; white-space:nowrap;
            transition: 0.15s;
        }}
        .ilha-pill:hover {{ background: rgba(0,0,0,0.1); }}
        .ilha-pill.ativa {{ background:#1d1d1f; color:#ffffff !important; }}
        .ilha-busca input {{
            border:none; background: rgba(0,0,0,0.05); border-radius:980px; padding:7px 14px;
            font-size:12.5px; width:130px; color:#1d1d1f;
        }}
        .ilha-icone {{
            text-decoration:none; color:#1d1d1f !important; font-size:15px; background: rgba(0,0,0,0.05);
            border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center;
            flex-shrink:0;
        }}
        .ilha-perfil {{ margin-left: auto; flex-shrink:0; position: relative; }}
        .ilha-perfil summary {{
            list-style:none; cursor:pointer; width:34px; height:34px; border-radius:50%;
            background:#0071e3; color:white !important; display:flex; align-items:center; justify-content:center;
            font-size:12px; font-weight:700;
        }}
        .ilha-perfil summary::-webkit-details-marker {{ display:none; }}
        .ilha-perfil[open] summary {{ background:#004c99; }}
        .painel-perfil {{
            position:absolute; right:0; top:44px; background:white; border-radius:16px;
            box-shadow:0 12px 34px rgba(0,0,0,0.25); padding:16px 18px; width:230px; text-align:left;
            z-index: 10000;
        }}
        .painel-perfil .nome {{ font-weight:700; font-size:14px; color:#1d1d1f; }}
        .painel-perfil .info {{ font-size:12px; color:#6e6e73; margin-top:2px; }}
        .painel-perfil a.sair {{
            display:block; margin-top:12px; text-align:center; background:#ff3b30; color:white !important;
            text-decoration:none; padding:7px; border-radius:980px; font-size:12.5px; font-weight:600;
        }}

        /* ---------- BANNER ---------- */
        .banner-imla {{
            margin-top: 76px;
            width: 100%; height: 240px; border-radius: 24px; overflow:hidden;
            background-image: linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.7)), url(data:image/jpeg;base64,{banner_b64 if banner_b64 else ''});
            background-size: cover; background-position: center;
            display:flex; align-items:flex-end; padding: 26px 34px;
        }}
        .banner-imla h1 {{
            color:#ffffff !important; font-size: 40px; margin:0; font-weight:700;
            text-shadow: 0 2px 12px rgba(0,0,0,0.55);
        }}
        .banner-imla p {{
            color: #ffffff !important; margin:0; font-size:15px; opacity:0.92;
            text-shadow: 0 1px 8px rgba(0,0,0,0.5);
        }}

        div.stButton > button:first-child {{
            background-color: transparent; border: none; box-shadow: none; padding: 10px;
            color: #1d1d1f !important; border-radius: 15px; transition: 0.2s;
        }}
        div.stButton > button:first-child:hover {{ background-color: rgba(0,0,0,0.05); }}

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

        </style>
    """, unsafe_allow_html=True)

    # ---------- MONTA A ILHA FLUTUANTE (HTML puro, navegação via query params) ----------
    pills_html = ""
    for nome, emoji in NUCLEOS_INFO.items():
        ativa = "ativa" if nome == n_sel else ""
        pills_html += f'<a class="ilha-pill {ativa}" href="?nucleo={nome}&idioma={idioma_atual}">{emoji} {nome}</a>'

    logo_tag = f'<img class="ilha-logo" src="data:image/png;base64,{logo_simbolo_b64}">' if logo_simbolo_b64 else ""

    navbar_html = f"""
    <div class="ilha-flutuante">
        {logo_tag}
        <span class="ilha-nome">{t('titulo_sistema')}</span>
        <div class="ilha-pills">{pills_html}</div>
        <form class="ilha-busca" method="get" style="margin:0;">
            <input type="hidden" name="nucleo" value="{n_sel}">
            <input type="hidden" name="idioma" value="{idioma_atual}">
            <input type="text" name="busca" placeholder="🔍 {t('buscar_placeholder')}" value="{st.session_state.busca}">
        </form>
        <a class="ilha-icone" title="PT / EN" href="?nucleo={n_sel}&idioma={idioma_alvo}">🌐</a>
        <details class="ilha-perfil">
            <summary>{iniciais}</summary>
            <div class="painel-perfil">
                <div class="nome">{usuario['nome']}</div>
                <div class="info">{t('email_label')}: {usuario['email']}</div>
                <div class="info">{t('nucleo_label')}: {NUCLEOS_INFO.get(usuario['nucleo'],'')} {usuario['nucleo']}</div>
                <a class="sair" href="?acao=sair">{t('sair')}</a>
            </div>
        </details>
    </div>
    """
    st.markdown(navbar_html, unsafe_allow_html=True)

    # ---------- BANNER ----------
    st.markdown(f"""
        <div class="banner-imla">
            <div>
                <h1>{t('titulo_sistema')}</h1>
                <p>{t('subtitulo')}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.busca:
        col_b1, col_b2 = st.columns([6, 1])
        with col_b1:
            st.info(f"🔍 {t('buscar_placeholder')} \"{st.session_state.busca}\"")
        with col_b2:
            st.markdown(f'<a href="?nucleo={n_sel}&idioma={idioma_atual}">✕ Limpar</a>', unsafe_allow_html=True)

    # ---------- MAPA MENTAL DOS NÚCLEOS ---------- (removido: navegação já ocorre pela barra flutuante)

    st.divider()

    st.markdown(f"<h2 style='font-size: 30px;'>{NUCLEOS_INFO.get(n_sel,'')} {n_sel}</h2>", unsafe_allow_html=True)

    aba_feed, aba_tarefas, aba_solicitacoes = st.tabs([t("aba_novidades"), t("aba_tarefas"), t("aba_solicitacoes")])

    # ================= ABA NOVIDADES =================
    with aba_feed:
        if usuario['nucleo'] == n_sel:
            with st.form("form_novo"):
                texto = st.text_area(t("compartilhar") + ":")
                if st.form_submit_button(t("publicar")) and texto.strip():
                    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {
                        "texto": texto,
                        "data": agora,
                        "autor_nome": usuario["nome"],
                        "autor_email": usuario["email"]
                    })
                    salvar_banco()
                    st.rerun()

        st.write("")
        col_c1, col_c2, col_c3 = st.columns(3)
        posts = st.session_state.nucleos_dados[n_sel]["atualizacoes"]

        busca_lower = st.session_state.busca.lower().strip()
        if busca_lower:
            posts = [p for p in posts if busca_lower in p.get("texto", "").lower()]

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
        c_link1, c_link2 = st.columns(2)
        c_link1.link_button(t("acessar_drive"), st.session_state.nucleos_dados[n_sel]["drive"])
        c_link2.link_button(t("cronogramas"), st.session_state.nucleos_dados[n_sel]["planilha"])
        st.divider()

        pode_editar = usuario['nucleo'] == n_sel

        if pode_editar:
            with st.expander(f"➕ {t('nova_demanda')}"):
                with st.form("form_nova_tarefa", clear_on_submit=True):
                    novo_titulo = st.text_input(t("titulo_demanda"))
                    nova_descricao = st.text_area(t("descricao_demanda"))
                    nova_prioridade = st.selectbox(t("prioridade"), PRIORIDADE_OPCOES, index=1)
                    if st.form_submit_button(t("adicionar_demanda")) and novo_titulo.strip():
                        agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
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
        if busca_lower:
            tarefas = [tf for tf in tarefas if busca_lower in tf.get("titulo", "").lower()]

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
                                if st.form_submit_button(t("salvar")):
                                    tf["titulo"] = titulo_edit.strip() or tf["titulo"]
                                    tf["descricao"] = descricao_edit.strip()
                                    tf["status"] = status_edit
                                    tf["prioridade"] = prio_edit
                                    salvar_banco()
                                    st.rerun()

    # ================= ABA SOLICITAÇÕES =================
    with aba_solicitacoes:
        if usuario['nucleo'] == n_sel:
            st.markdown(f"#### {t('enviar_solicitacao')}")
            with st.form("form_sol", clear_on_submit=True):
                dest = st.selectbox(t("para_nucleo"), list(NUCLEOS_INFO.keys()))
                assunto = st.text_input(t("assunto") + ":")
                msg = st.text_area(t("mensagem") + ":")
                if st.form_submit_button(t("enviar")) and assunto.strip():
                    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.caixa_entrada[dest].append({
                        "assunto": assunto,
                        "mensagem": msg,
                        "data": agora,
                        "de_nome": usuario["nome"],
                        "de_nucleo": usuario["nucleo"]
                    })
                    salvar_banco()
                    st.success(t("enviado"))

            st.write(f"### {t('caixa_entrada')}")
            caixa = st.session_state.caixa_entrada[n_sel]
            if not caixa:
                st.caption("Nenhuma solicitação recebida ainda.")
            for m in reversed(caixa):
                with st.expander(f"📩 {m['assunto']} ({t('de')}: {m.get('de_nome','—')} · {m.get('de_nucleo','')})"):
                    st.write(m['mensagem'])
                    st.caption(m['data'])
        else:
            st.error(t("restrito_caixa"))
