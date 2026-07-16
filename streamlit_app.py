import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import json
import base64
import io
import uuid
import hashlib
import secrets
import unicodedata
import gspread
import datetime
from zoneinfo import ZoneInfo
from PIL import Image
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection

# Configuração inicial da página (deve ser a primeira chamada)
st.set_page_config(
    page_title="Portal Unificado | IMLA & Gestão",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONSTANTES E CONFIGURAÇÕES VISUAIS ---
FUSO_BR = ZoneInfo("America/Bahia")
COR_PRIMARIA = "#253a58" # Azul escuro elegante[cite: 3]
COR_DESTAQUE = "#ab875f" # Dourado/terroso sofisticado[cite: 3]
COR_FUNDO = "#fbfbfb"

ARQUIVO_BANCO = "banco_iml.json"
ID_PLANILHA = "1Zj8u67oAWKgYRd2uOkGssdaxXnwdsKsZBDxeLChnBr4"
ARQUIVO_BUFFER = "buffer_estendido.csv"
ARQUIVO_DADOS_TE = "dados_turno_estendido.csv"
ARQUIVO_TABUA_MARE_LOCAL = "tabua_mare_registros_locais.csv"

NUCLEOS_INFO = {
    "Cozinha e Nutrição": "🍳", "Comunicação": "📣", "Pedagógico": "📚",
    "Captação de Recursos": "🤝", "Financeiro": "💰", "Apadrinhamento": "💌",
}

TURMAS_CONFIG = {
    "SALA ROSA": {"cor": "#ff81ba", "icon": "🌸"},
    "SALA AMARELA": {"cor": "#ffc713", "icon": "⭐"},
    "SALA VERDE": {"cor": "#a8cf45", "icon": "🌿"},
    "SALA AZUL": {"cor": "#5cc6d0", "icon": "💧"},
    "CIRAND. MUNDO": {"cor": "#6741d9", "icon": "🌍"},
}

CATEGORIAS = [
    "Atividades em grupo/Proatividade", "Interesse pelo novo", "Compartilhamento de Materiais",
    "Clareza e desenvoltura", "Respeito às regras", "Vocabulário adequado",
    "Leitura e Escrita", "Compreensão de comandos", "Superação de desafios", "Assiduidade"
]

NIVEIS_ALF = [
    "1. Pré-Silábico", "2. Silábico s/ Valor", "3. Silábico c/ Valor",
    "4. Silábico Alfabético", "5. Alfabético Inicial", "6. Alfabético Final",
    "7. Alfabético Ortográfico"
]
MAPA_NIVEIS = {niv: i + 1 for i, niv in enumerate(NIVEIS_ALF)}

# --- ESTILIZAÇÃO PREMIUM (UI/UX) ---
st.markdown(f"""
    <style>
    /* Tipografia e cores globais */
    html, body, [class*="css"] {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        font-size: 13px !important;
        color: {COR_PRIMARIA} !important;
        background-color: {COR_FUNDO} !important;
        font-weight: 400;
    }}
    
    /* Cabeçalhos refinados */
    h1, h2, h3, h4, h5, h6 {{
        color: {COR_PRIMARIA} !important;
        font-weight: 500 !important;
        letter-spacing: -0.5px;
    }}
    h1 {{ font-size: 22px !important; border-bottom: 1px solid #eaeaea; padding-bottom: 8px; margin-bottom: 24px; }}
    h2 {{ font-size: 18px !important; margin-top: 16px; }}
    h3 {{ font-size: 15px !important; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.8; }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {COR_PRIMARIA} !important;
    }}
    [data-testid="stSidebar"] * {{
        color: #ffffff !important;
    }}
    
    /* Botões elegantes */
    .stButton>button {{
        background-color: transparent !important;
        color: {COR_PRIMARIA} !important;
        border: 1px solid {COR_PRIMARIA} !important;
        border-radius: 4px !important;
        font-size: 12px !important;
        padding: 6px 16px !important;
        transition: all 0.2s ease-in-out;
    }}
    .stButton>button:hover {{
        background-color: {COR_PRIMARIA} !important;
        color: #ffffff !important;
    }}
    .stButton>button[kind="primary"] {{
        background-color: {COR_DESTAQUE} !important;
        color: #ffffff !important;
        border: 1px solid {COR_DESTAQUE} !important;
    }}
    .stButton>button[kind="primary"]:hover {{
        background-color: #8c6d4a !important;
        border-color: #8c6d4a !important;
    }}

    /* Cards e Containers Minimalistas */
    .minimal-card {{
        background: #ffffff;
        border: 1px solid #f0f0f0;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.03);
    }}
    .tag-status {{
        font-size: 10px; font-weight: 600; text-transform: uppercase; 
        padding: 4px 8px; border-radius: 4px; display: inline-block;
    }}
    
    /* Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {{
        font-size: 13px !important;
        border-radius: 4px !important;
        border: 1px solid #e0e0e0 !important;
    }}
    
    /* Remoção de elementos desnecessários */
    header {{ visibility: hidden; }}
    .stDivider {{ border-bottom-color: #eaeaea !important; margin: 24px 0 !important; }}
    </style>
""", unsafe_allow_html=True)

# --- UTILITÁRIOS E FUNÇÕES DE BASE ---
def agora_br():
    return datetime.datetime.now(FUSO_BR)

def hash_senha(senha, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return salt, h.hex()

def verificar_senha(senha, salt, hash_esperado):
    _, h = hash_senha(senha, salt)
    return secrets.compare_digest(h, hash_esperado)

# --- GERENCIAMENTO DE DADOS (IMLA & LALU) ---
@st.cache_resource
def init_gsheets_connection():
    return st.connection("gsheets", type=GSheetsConnection)

conn = init_gsheets_connection()

@st.cache_data(ttl=600, show_spinner=False)
def ler_planilha(worksheet_name: str) -> pd.DataFrame:
    try:
        df = conn.read(worksheet=worksheet_name).fillna("")
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

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
    for email, u in dados.get("usuarios", {}).items():
        u.setdefault("nome", (u.get("email") or email).split("@")[0].title())
    return dados

def salvar_banco():
    dados = {
        "usuarios": st.session_state.usuarios,
        "nucleos_dados": st.session_state.nucleos_dados,
        "caixa_entrada": st.session_state.caixa_entrada
    }
    with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)

# Inicialização de Session State Unificado
if "dados_carregados" not in st.session_state:
    dados = carregar_banco()
    st.session_state.usuarios = dados["usuarios"]
    st.session_state.nucleos_dados = dados.get("nucleos_dados", {n: estrutura_padrao_nucleo() for n in NUCLEOS_INFO})
    st.session_state.caixa_entrada = dados.get("caixa_entrada", {n: [] for n in NUCLEOS_INFO})
    st.session_state.dados_carregados = True

if "usuario_logado" not in st.session_state: 
    st.session_state.usuario_logado = None
if "perfil_acesso" not in st.session_state: 
    st.session_state.perfil_acesso = None # 'equipe', 'visitante', 'admin', 'padrinho'
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "dashboard_imla"
if "modo_tela" not in st.session_state:
    st.session_state.modo_tela = "login"

# --- MÓDULOS DE UI DO SISTEMA LALU ---
def criar_grafico_mare(categorias, valores):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valores, theta=categorias, fill="toself",
        line=dict(color=COR_DESTAQUE),
        fillcolor=f"{COR_DESTAQUE}40"
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], gridcolor="#eaeaea"),
            angularaxis=dict(gridcolor="#eaeaea")
        ),
        showlegend=False, 
        margin=dict(l=40, r=40, t=20, b=20), 
        height=300,
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Helvetica Neue", size=10, color=COR_PRIMARIA)
    )
    return fig

# --- AUTENTICAÇÃO UNIFICADA ---
if st.session_state.usuario_logado is None:
    st.markdown("<div style='max-width: 400px; margin: 80px auto;' class='minimal-card'>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center; color: {COR_PRIMARIA}; border:none;'>Acesso ao Portal</h1>", unsafe_allow_html=True)
    
    if st.session_state.modo_tela == "login":
        st.markdown("<p style='text-align: center; font-size: 12px;'>Entre com suas credenciais da Equipe IMLA ou Coordenação/Padrinhos.</p>", unsafe_allow_html=True)
        usuario_email = st.text_input("Usuário ou E-mail:")
        senha_login = st.text_input("Senha:", type="password")

        if st.button("Entrar", type="primary", use_container_width=True):
            chave = usuario_email.strip().lower()
            
            # 1. Tenta login como Admin/Coordenação
            if chave == "admin" and senha_login == "123":
                st.session_state.usuario_logado = {"nome": "Coordenação Geral", "nucleo": "Pedagógico"}
                st.session_state.perfil_acesso = "admin"
                st.rerun()
                
            # 2. Tenta login como Equipe IMLA
            elif chave in st.session_state.usuarios:
                u = st.session_state.usuarios[chave]
                senha_ok = False
                if "senha_hash" in u:
                    senha_ok = verificar_senha(senha_login, u["salt"], u["senha_hash"])
                if senha_ok:
                    st.session_state.usuario_logado = u
                    st.session_state.perfil_acesso = "equipe"
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
            
            # 3. Fallback: Mock Padrinho (Simulando a busca na planilha)
            elif chave.startswith("padrinho"):
                st.session_state.usuario_logado = {"nome": "Padrinho Visitante", "aluno_vinculado": "João Silva"}
                st.session_state.perfil_acesso = "padrinho"
                st.rerun()
            else:
                st.error("Credenciais não encontradas.")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👁️ Sou Visitante", use_container_width=True):
                st.session_state.usuario_logado = {"nome": "Visitante", "nucleo": "Comunicação"}
                st.session_state.perfil_acesso = "visitante"
                st.rerun()
        with col2:
            if st.button("Criar Conta IMLA", use_container_width=True):
                st.session_state.modo_tela = "cadastro"
                st.rerun()

    else:
        st.markdown("<h3>Novo Cadastro (Equipe IMLA)</h3>", unsafe_allow_html=True)
        novo_nome = st.text_input("Nome completo:")
        novo_email = st.text_input("E-mail corporativo:")
        novo_nucleo = st.selectbox("Seu Núcleo:", list(NUCLEOS_INFO.keys()))
        nova_senha = st.text_input("Senha:", type="password")
        
        if st.button("Finalizar Cadastro", type="primary", use_container_width=True):
            chave = novo_email.strip().lower()
            if novo_nome and chave and nova_senha:
                salt, h = hash_senha(nova_senha)
                st.session_state.usuarios[chave] = {
                    "nome": novo_nome.strip(), "email": chave, "nucleo": novo_nucleo,
                    "salt": salt, "senha_hash": h
                }
                salvar_banco()
                st.success("Cadastro realizado! Faça login.")
                st.session_state.modo_tela = "login"
                st.rerun()
                
        if st.button("Voltar ao Login", use_container_width=True):
            st.session_state.modo_tela = "login"
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- INTERFACE PRINCIPAL ---
usuario = st.session_state.usuario_logado
perfil = st.session_state.perfil_acesso

# -- MENU LATERAL (Navegação Unificada) --
with st.sidebar:
    st.markdown(f"<h3 style='color: white; margin-bottom: 0;'>Olá, {usuario['nome']}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #a0aec0; font-size: 11px; margin-bottom: 24px;'>Perfil: {perfil.capitalize()}</p>", unsafe_allow_html=True)
    
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #a0aec0; letter-spacing: 1px;'>ÁREA DE TRABALHO</p>", unsafe_allow_html=True)
    
    if st.button("🏢 Intranet IMLA", use_container_width=True, type="primary" if st.session_state.pagina_atual == "dashboard_imla" else "secondary"):
        st.session_state.pagina_atual = "dashboard_imla"
        st.rerun()
        
    if perfil in ["admin", "equipe", "padrinho"]:
        if st.button("📊 Gestão Pedagógica", use_container_width=True, type="primary" if st.session_state.pagina_atual == "gestao_lalu" else "secondary"):
            st.session_state.pagina_atual = "gestao_lalu"
            st.rerun()
            
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if st.button("Sair / Logout", use_container_width=True):
        st.session_state.usuario_logado = None
        st.session_state.perfil_acesso = None
        st.rerun()


# -- PÁGINA: INTRANET IMLA --
if st.session_state.pagina_atual == "dashboard_imla":
    st.markdown("<h1>Intranet Corporativa IMLA</h1>", unsafe_allow_html=True)
    
    n_sel = usuario.get("nucleo", "Comunicação")
    eh_visitante = (perfil == "visitante")
    pode_editar = not eh_visitante

    # Selecionador de núcleo minimalista
    cols = st.columns(len(NUCLEOS_INFO))
    for i, (nome, emoji) in enumerate(NUCLEOS_INFO.items()):
        if cols[i].button(f"{nome}", key=f"nuc_{nome}", use_container_width=True):
            usuario["nucleo"] = nome # Atualiza visualização
            st.rerun()
            
    st.markdown(f"<h3>Núcleo Atual: {n_sel}</h3>", unsafe_allow_html=True)
    aba_feed, aba_tarefas, aba_solicitacoes = st.tabs(["Notícias & Feed", "Demandas (Kanban)", "Solicitações"])

    with aba_feed:
        if pode_editar:
            with st.container():
                texto = st.text_area("Compartilhar algo novo:", height=80)
                if st.button("Publicar Atualização", type="primary"):
                    st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {
                        "texto": texto, "data": agora_br().strftime("%d/%m/%Y %H:%M"),
                        "autor_nome": usuario["nome"]
                    })
                    salvar_banco()
                    st.rerun()
                    
        st.divider()
        posts = st.session_state.nucleos_dados[n_sel].get("atualizacoes", [])
        if not posts: st.caption("Nenhuma atualização.")
        for p in posts:
            st.markdown(f"""
            <div class='minimal-card'>
                <div style='font-size: 11px; color: {COR_DESTAQUE}; margin-bottom: 4px;'>{p.get('autor_nome','—')} • {p['data']}</div>
                <div style='font-size: 13px; line-height: 1.5;'>{p['texto']}</div>
            </div>
            """, unsafe_allow_html=True)

    with aba_tarefas:
        if pode_editar:
            with st.expander("Nova Demanda"):
                t_tit = st.text_input("Título")
                t_desc = st.text_area("Descrição")
                t_prio = st.selectbox("Prioridade", ["Baixa", "Média", "Alta"])
                if st.button("Adicionar Tarefa"):
                    st.session_state.nucleos_dados[n_sel].setdefault("tarefas", []).append({
                        "id": str(uuid.uuid4())[:8], "titulo": t_tit, "descricao": t_desc,
                        "status": "Criada", "prioridade": t_prio, "autor_nome": usuario["nome"]
                    })
                    salvar_banco()
                    st.rerun()
                    
        tarefas = st.session_state.nucleos_dados[n_sel].get("tarefas", [])
        c_k1, c_k2, c_k3 = st.columns(3)
        status_map = {"Criada": c_k1, "Em andamento": c_k2, "Concluída": c_k3}
        
        for status, col in status_map.items():
            with col:
                st.markdown(f"<div style='font-weight: 600; margin-bottom: 12px; border-bottom: 1px solid #eaeaea; padding-bottom: 4px;'>{status.upper()}</div>", unsafe_allow_html=True)
                for tf in [t for t in tarefas if t.get("status") == status]:
                    cor_prio = "#34c759" if tf.get("prioridade") == "Baixa" else "#ff9f0a" if tf.get("prioridade") == "Média" else "#ff3b30"
                    st.markdown(f"""
                    <div class='minimal-card' style='padding: 12px; border-left: 3px solid {cor_prio};'>
                        <div style='font-weight: 500;'>{tf['titulo']}</div>
                        <div style='font-size: 11px; color: #888; margin-top: 4px;'>{tf.get('prioridade')} • Resp: {tf.get('autor_nome')}</div>
                    </div>
                    """, unsafe_allow_html=True)

    with aba_solicitacoes:
        st.markdown("Mensageria interna entre núcleos.")
        if pode_editar:
            dest = st.selectbox("Para:", list(NUCLEOS_INFO.keys()))
            assunto = st.text_input("Assunto")
            if st.button("Enviar Solicitação"):
                st.session_state.caixa_entrada[dest].append({
                    "assunto": assunto, "mensagem": "...", "data": agora_br().strftime("%d/%m/%Y"),
                    "de_nome": usuario["nome"], "de_nucleo": usuario["nucleo"]
                })
                salvar_banco()
                st.success("Enviado.")
        
        st.divider()
        st.markdown("<h3>Caixa de Entrada</h3>", unsafe_allow_html=True)
        for m in st.session_state.caixa_entrada[n_sel]:
            st.markdown(f"<div class='minimal-card'><b>{m['assunto']}</b><br><span style='font-size:11px'>De: {m['de_nome']} ({m['de_nucleo']})</span></div>", unsafe_allow_html=True)

# -- PÁGINA: GESTÃO PEDAGÓGICA (MÃE LALU) --
elif st.session_state.pagina_atual == "gestao_lalu":
    st.markdown("<h1>Painel de Acompanhamento Pedagógico</h1>", unsafe_allow_html=True)
    
    if perfil == "padrinho":
        st.info("Visualização restrita ao aluno apadrinhado.")
        # Mock view for Padrinho
        st.markdown(f"<h3>Evolução de {usuario.get('aluno_vinculado', 'Aluno')}</h3>", unsafe_allow_html=True)
        fig = criar_grafico_mare(CATEGORIAS, [3, 4, 3, 5, 2, 4, 3, 4, 5, 3])
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        c_filtro1, c_filtro2 = st.columns(2)
        sala_selecionada = c_filtro1.selectbox("Selecione a Turma", list(TURMAS_CONFIG.keys()))
        
        # Simulando carregamento de alunos
        alunos_mock = ["Maria Silva", "João Santos", "Ana Oliveira"]
        aluno_selecionado = c_filtro2.selectbox("Selecione o Aluno", alunos_mock)
        
        st.divider()
        
        c_dash1, c_dash2 = st.columns([2, 1])
        
        with c_dash1:
            st.markdown("<h3>Análise Comportamental (Tábua da Maré)</h3>", unsafe_allow_html=True)
            # Gerando dados aleatórios fixados pelo nome para demonstração
            np.random.seed(len(aluno_selecionado))
            valores_mare = np.random.randint(1, 6, size=len(CATEGORIAS))
            fig = criar_grafico_mare(CATEGORIAS, valores_mare)
            st.plotly_chart(fig, use_container_width=True)
            
        with c_dash2:
            st.markdown("<h3>Status de Alfabetização</h3>", unsafe_allow_html=True)
            nivel_atual = NIVEIS_ALF[np.random.randint(0, len(NIVEIS_ALF))]
            
            st.markdown(f"""
            <div class='minimal-card' style='text-align: center;'>
                <div style='font-size: 11px; color: #888; text-transform: uppercase;'>Nível Diagnóstico Atual</div>
                <div style='font-size: 16px; font-weight: 600; color: {COR_DESTAQUE}; margin-top: 8px;'>{nivel_atual.split('. ')[1]}</div>
                <div style='margin-top: 16px; font-size: 12px; line-height: 1.5; color: {COR_PRIMARIA}; text-align: left;'>
                    <b>Evidências:</b><br>
                    • Reconhece sons iniciais<br>
                    • Escrita autônoma incipiente
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if perfil == "admin":
                st.button("Atualizar Diagnóstico", type="primary", use_container_width=True)
                
        st.markdown("<h3>Trilha de Desenvolvimento Recente</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div style='display: flex; gap: 16px; overflow-x: auto; padding-bottom: 12px;'>
            <div class='minimal-card' style='min-width: 150px; margin-bottom: 0;'>
                <div class='tag-status' style='background: #f0f0f0;'>1ª Avaliação</div>
                <div style='margin-top: 8px; font-size: 12px;'>Silábico s/ Valor</div>
            </div>
            <div style='display: flex; align-items: center; color: #ccc;'>→</div>
            <div class='minimal-card' style='min-width: 150px; margin-bottom: 0; border: 1px solid """+COR_DESTAQUE+"""'>
                <div class='tag-status' style='background: """+COR_DESTAQUE+"""20; color: """+COR_DESTAQUE+"""'>2ª Avaliação (Atual)</div>
                <div style='margin-top: 8px; font-size: 12px; font-weight: 600;'>Silábico c/ Valor</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

```
