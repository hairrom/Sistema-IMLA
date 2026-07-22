import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import unicodedata
import gspread
import datetime
from zoneinfo import ZoneInfo
import json
import base64
import io
import uuid
import hashlib
import secrets
from PIL import Image
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURAÇÃO UNIFICADA DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Sistema IMLA - Gestão Unificada",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. CONSTANTES E CONFIGURAÇÕES GLOBAIS
# ==========================================

# --- Constantes da Intranet ---
FUSO_BR = ZoneInfo("America/Bahia")
ARQUIVO_BANCO = "banco_iml.json"
LOGO_PATH = "Submarca 01.png"
LOGIN_BG_PATH = "IMG_3987.JPG"
BANNER_PATH = "IMG_3985.JPG"
NUCLEOS_INFO = {} 

# --- Constantes do Pedagógico ---
ID_PLANILHA = "1Zj8u67oAWKgYRd2uOkGssdaxXnwdsKsZBDxeLChnBr4"
ARQUIVO_BUFFER   = "buffer_estendido.csv"
ARQUIVO_DADOS_TE = "dados_turno_estendido.csv"
ARQUIVO_TABUA_MARE_LOCAL = "tabua_mare_registros_locais.csv"

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"
C_AZUL_MARE = "#8fd9fb"

NIVEIS_ALF = [
    "1. Pré-Silábico", "2. Silábico s/ Valor", "3. Silábico c/ Valor",
    "4. Silábico Alfabético", "5. Alfabético Inicial", "6. Alfabético Final",
    "7. Alfabético Ortográfico"
]
MAPA_NIVEIS = {niv: i + 1 for i, niv in enumerate(NIVEIS_ALF)}
CORES_EXCLUSIVAS = {
    "1. Pré-Silábico": "#FADBD8", "2. Silábico s/ Valor": "#FDEBD0",
    "3. Silábico c/ Valor": "#FCF3CF", "4. Silábico Alfabético": "#D5F5E3",
    "5. Alfabético Inicial": "#A9DFBF", "6. Alfabético Final": "#D6EAF8",
    "7. Alfabético Ortográfico": "#EBDEF0"
}
MARE_LABELS = {1: "Maré Baixa", 2: "Maré Vazante", 3: "Maré Enchente", 4: "Maré Alta", 5: "Maré Cheia"}
TURMAS_CONFIG = {
    "SALA ROSA":     {"cor": C_ROSA,    "icon": "🌸"},
    "SALA AMARELA":  {"cor": C_AMARELO, "icon": "⭐"},
    "SALA VERDE":    {"cor": C_VERDE,   "icon": "🌿"},
    "SALA AZUL":     {"cor": C_AZUL,    "icon": "💧"},
    "CIRAND. MUNDO": {"cor": C_ROXO,    "icon": "🌍"},
}
BADGE_LABEL = {
    "SALA ROSA":     "ROSA",
    "SALA AMARELA":  "AMARELA",
    "SALA VERDE":    "VERDE",
    "SALA AZUL":     "AZUL",
    "CIRAND. MUNDO": "MUNDO",
}
CATEGORIAS = [
    "Atividades em grupo/Proatividade", "Interesse pelo novo", "Compartilhamento de Materiais",
    "Clareza e desenvoltura", "Respeito às regras", "Vocabulário adequado",
    "Leitura e Escrita", "Compreensão de comandos", "Superação de desafios", "Assiduidade"
]
OPCOES_MARE = ["Maré Baixa", "Maré Vazante", "Maré Enchente", "Maré Alta", "Maré Cheia"]
EVIDENCIAS_POR_NIVEL = {
    "1. Pré-Silábico":          ["Diferencia letras de desenhos", "Escreve o nome sem apoio", "Acredita que nomes grandes têm muitas letras", "Sabe que se escreve da esquerda para a direita"],
    "2. Silábico s/ Valor":     ["Uma letra para cada sílaba (sem som)", "Segmenta a fala em partes", "Respeita quantidade de emissões sonoras", "Faz leitura global da palavra"],
    "3. Silábico c/ Valor":     ["Usa vogais correspondentes ao som", "Identifica o som inicial das palavras", "Leitura apontada (acompanha com o dedo)", "Escreve uma letra por sílaba com som correto"],
    "4. Silábico Alfabético":   ["Oscila entre uma letra e a sílaba completa", "Começa a usar consoantes nas sílabas", "Consegue completar lacunas de letras", "Percebe a estrutura da sílaba simples"],
    "5. Alfabético Inicial":    ["Compreende o sistema de escrita", "Erros ortográficos comuns (ex: K por C)", "Lê textos curtos com fluidez", "Segmentação de palavras irregular"],
    "6. Alfabético Final":      ["Diferencia sons semelhantes (P/B, T/D)", "Usa corretamente dígrafos (LH, NH, CH)", "Domina regras básicas de pontuação", "Produz textos com coesão"],
    "7. Alfabético Ortográfico":["Escrita autônoma e correta", "Domina acentuação e regras complexas", "Lê com entonação e fluidez total", "Revisa o próprio texto"],
}

# ==========================================
# 3. CONEXÕES E FUNÇÕES DE BANCO (GSheets & JSON)
# ==========================================

# Conexão Global Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Funções Auxiliares de Tempo e Segurança (Intranet)
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
    """Verifica a integridade da senha contra o hash esperado."""
    _, h = hash_senha(senha, salt)
    return secrets.compare_digest(h, hash_esperado)

# Funções Estruturais de Banco JSON (Intranet)
def carregar_banco_json():
    """Carrega o banco de dados JSON da Intranet."""
    if not os.path.exists(ARQUIVO_BANCO):
        return {}
    with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_banco_json(dados):
    """Salva os dados no banco JSON da Intranet."""
    with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# ==========================================
# 4. INICIALIZAÇÃO DE SESSION STATE ISOLADA
# ==========================================

# --- Chaves da Intranet (Sem prefixo) ---
chaves_intranet_padrao = {
    "logado": False, 
    "perfil": None, 
    "nome_usuario": ""
}
for k, v in chaves_intranet_padrao.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- Chaves do Pedagógico (Com prefixo ped_) ---
if "ped_alunos_te_dict" not in st.session_state:
    st.session_state["ped_alunos_te_dict"] = {}

chaves_pedagogico = ["sel_mat", "sel_pad", "sel_aval", "sel_int", "sel_alf", "sel_ind", "sel_te"]
for k in chaves_pedagogico:
    chave_isolada = f"ped_{k}"
    if chave_isolada not in st.session_state:
        st.session_state[chave_isolada] = "SALA ROSA"

# ==========================================
# 5. CSS GLOBAL UNIFICADO
# ==========================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

/* ── Nunito via herança — NÃO toca em containers com ícones ── */
html, body {{ font-family: 'Nunito', sans-serif; background-color: #ffffff; }}

/* Somente elementos de texto puro — sem button, sem span, sem div */
h1, h2, h3, h4, h5, h6 {{ font-family: 'Nunito', sans-serif !important; }}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] li {{
    font-family: 'Nunito', sans-serif !important;
}}
[data-testid="stWidgetLabel"] p,
[data-testid="stCheckbox"] p,
[data-testid="stRadio"] p,
[data-testid="stSelectbox"] label,
[data-testid="stTextInput"] label {{ font-family: 'Nunito', sans-serif !important; }}
input, select, textarea {{ font-family: 'Nunito', sans-serif !important; }}
table, td, th {{ font-family: 'Nunito', sans-serif !important; }}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {{ font-family: 'Nunito', sans-serif !important; }}

/* ── Tamanhos ── */
h1, [data-testid="stMarkdownContainer"] h1 {{
    font-size: 32px !important; font-weight: 900 !important; color: #1a1a2e !important;
}}
h2, [data-testid="stMarkdownContainer"] h2 {{
    font-size: 24px !important; font-weight: 800 !important; color: #1a1a2e !important;
}}
h3, [data-testid="stMarkdownContainer"] h3 {{
    font-size: 20px !important; font-weight: 800 !important; color: #2c3e50 !important;
}}
h4, h5, h6 {{ font-size: 15px !important; font-weight: 700 !important; color: #2c3e50 !important; }}
[data-testid="stMarkdownContainer"] p {{
    font-size: 14px !important; font-weight: 400 !important; line-height: 1.6 !important;
}}
[data-testid="stWidgetLabel"] p {{
    font-size: 13px !important; font-weight: 700 !important; color: #2c3e50 !important;
}}

/* ── Tabelas HTML inline ── */
table {{ font-size: 12px !important; }}
table th {{ font-size: 12px !important; font-weight: 800 !important; }}
table td {{ font-size: 12px !important; font-weight: 400 !important; }}

/* ── Botões: layout + peso, SEM font-family no container ── */
div.stButton > button {{
    font-weight: 800 !important; font-size: 12px !important;
    width: 100%; border-radius: 8px !important;
    height: 42px; border: none !important; transition: all 0.3s;
}}

/* ── Métricas e alertas ── */
[data-testid="stMetricValue"] {{ font-size: 26px !important; font-weight: 800 !important; }}
[data-testid="stMetricLabel"] {{ font-size: 12px !important; font-weight: 700 !important; }}
[data-testid="stAlert"] p {{ font-size: 13px !important; font-weight: 600 !important; }}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {{ font-size: 13px !important; font-weight: 700 !important; }}

/* ── Componentes custom reutilizados ── */
.main-header {{ text-align: center; padding: 20px 0; }}
.main-header h1 {{ font-size: 38px !important; font-weight: 900; }}
.custom-table {{ width: 100%; border-collapse: separate; border-spacing: 0;
    border: 1px solid #f0f0f0; border-radius: 10px; overflow: hidden;
    font-size: 12px; margin-top: 5px; margin-bottom: 15px; }}
.custom-table thead th {{ padding: 12px 10px; text-align: left; color: white !important;
    font-weight: 800; border: none; font-size: 12px; }}
.custom-table td {{ padding: 10px; border-bottom: 1px solid #f9f9f9; font-size: 12px; }}
.sala-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px;
    color: white; font-weight: 800; font-size: 10px; margin-top: 5px; text-transform: uppercase; }}
.trilha-container {{ display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 10px 0; }}
.caixa-trilha {{ flex: 1; height: 85px; border-radius: 15px; display: flex; align-items: center;
    justify-content: center; text-align: center; font-size: 10px; font-weight: 800; padding: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 2px solid transparent; line-height: 1.2; }}
.seta-trilha {{ padding: 0 5px; color: #ccc; font-size: 18px; font-weight: bold; }}
.mare-box {{ display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; padding: 2px; }}
.mare-mini-tabela {{ width: 35px; height: 20px; border: 1px solid #999; border-radius: 3px; }}
.mare-texto-tabela {{ font-size: 10px !important; color: #555; font-weight: 700 !important;
    line-height: 1; text-transform: lowercase; font-family: 'Nunito', sans-serif !important; }}
</style>
""", unsafe_allow_html=True)
