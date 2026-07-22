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
# ==========================================
# 6. AUTENTICAÇÃO UNIFICADA (BLOCO 2)
# ==========================================

def registrar_usuario_equipe(usuario, senha, nucleo):
    """Função auxiliar para cadastrar novos membros da equipe no banco JSON."""
    banco = carregar_banco_json()
    if "usuarios" not in banco:
        banco["usuarios"] = {}
    
    if usuario in banco["usuarios"]:
        return False, "Este usuário já existe!"
        
    salt, hash_s = hash_senha(senha)
    banco["usuarios"][usuario] = {
        "salt": salt,
        "hash": hash_s,
        "nucleo": nucleo,
        "data_cadastro": str(agora_br())
    }
    salvar_banco_json(banco)
    return True, "Membro da equipe cadastrado com sucesso!"

def tela_login():
    """Renderiza a tela de login unificada com três perfis de acesso."""
    
    # Cria colunas para centralizar o formulário de login de forma elegante
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='main-header'><h1>🔒 Acesso IMLA</h1></div>", unsafe_allow_html=True)
        st.write("---")
        
        tipo_acesso = st.selectbox(
            "Selecione seu perfil de acesso:", 
            ["Equipe (Núcleos)", "Padrinho / Madrinha", "Administração"]
        )
        
        with st.form("form_login"):
            # Renderiza os campos de forma dinâmica dependendo do perfil escolhido
            if tipo_acesso == "Equipe (Núcleos)":
                st.info("Acesso restrito aos membros cadastrados nos Núcleos do IMLA.")
                usuario = st.text_input("Nome de Usuário")
                senha = st.text_input("Senha", type="password")
            
            elif tipo_acesso == "Padrinho / Madrinha":
                st.info("Acesso simplificado para acompanhamento do sistema pedagógico.")
                usuario = st.text_input("Digite seu Nome Completo")
                senha = None # Padrinhos usam acesso simplificado sem senha neste escopo
            
            else: # Administração
                st.warning("Acesso exclusivo para a gestão geral do sistema.")
                usuario = st.text_input("Usuário Admin")
                senha = st.text_input("Senha Admin", type="password")
            
            btn_login = st.form_submit_button("Entrar no Sistema")
            
        # Lógica de validação do login
        if btn_login:
            if tipo_acesso == "Administração":
                # Credenciais fixas iniciais para o Admin (podem ser aprimoradas depois)
                if usuario == "admin" and senha == "imla2026":
                    st.session_state["logado"] = True
                    st.session_state["perfil"] = "Admin"
                    st.session_state["nome_usuario"] = "Administrador Geral"
                    st.rerun()
                else:
                    st.error("Credenciais de administrador incorretas.")
            
            elif tipo_acesso == "Equipe (Núcleos)":
                banco = carregar_banco_json()
                usuarios = banco.get("usuarios", {})
                
                if usuario in usuarios:
                    dados_user = usuarios[usuario]
                    if verificar_senha(senha, dados_user["salt"], dados_user["hash"]):
                        st.session_state["logado"] = True
                        st.session_state["perfil"] = "Equipe"
                        st.session_state["nome_usuario"] = usuario
                        st.session_state["nucleo"] = dados_user.get("nucleo", "Geral")
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
                else:
                    st.error("Usuário não encontrado. Solicite seu cadastro à Administração.")
                    
            elif tipo_acesso == "Padrinho / Madrinha":
                if usuario.strip():
                    st.session_state["logado"] = True
                    st.session_state["perfil"] = "Padrinho"
                    st.session_state["nome_usuario"] = usuario.strip().title()
                    st.rerun()
                else:
                    st.error("Por favor, insira seu nome para continuar.")
        
        # Área oculta para criar os primeiros usuários da equipe (útil durante o desenvolvimento)
        st.write("")
        with st.expander("🛠️ Primeiro Acesso / Cadastro de Equipe"):
            with st.form("form_cadastro"):
                novo_user = st.text_input("Novo Usuário")
                nova_senha = st.text_input("Nova Senha", type="password")
                novo_nucleo = st.selectbox("Núcleo de Atuação", ["Comunicação", "Pedagógico", "Administrativo", "Apoio"])
                btn_cadastrar = st.form_submit_button("Cadastrar Membro")
                
                if btn_cadastrar:
                    if novo_user and nova_senha:
                        sucesso, msg = registrar_usuario_equipe(novo_user, nova_senha, novo_nucleo)
                        if sucesso:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Preencha todos os campos para cadastrar.")
                        # ==========================================
# 7. NAVEGAÇÃO PRINCIPAL E ROTEAMENTO (BLOCO 3)
# ==========================================

def menu_lateral():
    """Renderiza o menu lateral dinâmico, minimalista e baseado no perfil do usuário."""
    with st.sidebar:
        # Cabeçalho da sidebar limpo e sofisticado
        st.markdown("<h3 style='text-align: center; margin-bottom: 0;'>🕊️ IMLA</h3>", unsafe_allow_html=True)
        
        # Identificação discreta do usuário
        nome = st.session_state.get('nome_usuario', '')
        perfil = st.session_state.get('perfil', '')
        st.markdown(
            f"<p style='text-align: center; font-size: 11px; color: #7f8c8d; margin-top: -5px;'>"
            f"{nome} <br> <span style='font-size: 9px; text-transform: uppercase; letter-spacing: 1px;'>{perfil}</span>"
            f"</p>", 
            unsafe_allow_html=True
        )
        st.write("---")

        # Define as rotas disponíveis com base no perfil
        paginas = []
        if perfil == "Admin":
            paginas = ["Início", "Gestão de Núcleos", "Sistema Pedagógico", "Configurações Gerais"]
        elif perfil == "Equipe":
            paginas = ["Início", "Meu Núcleo", "Sistema Pedagógico"]
        elif perfil == "Padrinho":
            paginas = ["Início", "Acompanhamento Pedagógico"]
        else:
            paginas = ["Início"]

        # Menu de navegação limpo, sem label visível para não poluir o visual
        escolha = st.radio("Navegação", paginas, label_visibility="collapsed")
        
        st.write("---")
        
        # Botão de logout unificado
        if st.button("Sair / Logout", use_container_width=True):
            # Limpa todas as variáveis de sessão para garantir um logout seguro
            st.session_state.clear() 
            st.rerun()
            
        return escolha

def renderizar_pagina(escolha):
    """Renderiza o conteúdo da página selecionada (Placeholder temporário)."""
    if escolha == "Início":
        st.markdown("<h2>Visão Geral</h2>", unsafe_allow_html=True)
        st.write("Selecione um módulo no menu lateral.")
        
    elif escolha == "Gestão de Núcleos":
        st.markdown("<h2>Gestão de Núcleos</h2>", unsafe_allow_html=True)
        st.info("Módulo administrativo em construção...")
        
    elif escolha == "Meu Núcleo":
        nucleo_atual = st.session_state.get('nucleo', '')
        st.markdown(f"<h2>Área de Trabalho: {nucleo_atual}</h2>", unsafe_allow_html=True)
        st.info("Ferramentas do núcleo em construção...")
        
    elif escolha in ["Sistema Pedagógico", "Acompanhamento Pedagógico"]:
        st.markdown("<h2>Módulo Pedagógico</h2>", unsafe_allow_html=True)
        st.info("Integração do painel pedagógico em construção...")
        
    elif escolha == "Configurações Gerais":
        st.markdown("<h2>Configurações</h2>", unsafe_allow_html=True)
        st.info("Ajustes do sistema em construção...")

def main():
    """Motor de execução do aplicativo."""
    # Se não estiver logado, exibe apenas a tela limpa de login
    if not st.session_state.get("logado", False):
        tela_login()
    else:
        # Se estiver logado, exibe o menu e a página correspondente
        pagina_selecionada = menu_lateral()
        renderizar_pagina(pagina_selecionada)

# ==========================================
# 8. EXECUÇÃO DO SISTEMA
# ==========================================
if __name__ == "__main__":
    main()
    # ==========================================
# 9. MÓDULOS DA INTRANET (BLOCO 4)
# ==========================================

def inicializar_chaves_banco():
    """Garante que as chaves da Intranet existam no banco."""
    banco = carregar_banco_json()
    modificado = False
    for chave in ["feed", "tarefas", "solicitacoes"]:
        if chave not in banco:
            banco[chave] = []
            modificado = True
    if modificado:
        salvar_banco_json(banco)
    return banco

def modulo_feed(nucleo_usuario):
    """Renderiza um feed de mensagens minimalista."""
    st.markdown("<h3 style='color: #253a58; font-size: 16px; font-weight: 800;'>Mural de Comunicação</h3>", unsafe_allow_html=True)
    banco = inicializar_chaves_banco()
    
    # Formulário de nova postagem
    with st.form("form_novo_post", clear_on_submit=True):
        mensagem = st.text_area("Nova mensagem", height=80, label_visibility="collapsed", placeholder="Compartilhe uma atualização com a equipe...")
        col_btn1, col_btn2 = st.columns([4, 1])
        with col_btn2:
            submit_post = st.form_submit_button("Publicar")
            
        if submit_post and mensagem.strip():
            novo_post = {
                "id": str(uuid.uuid4())[:8],
                "autor": st.session_state["nome_usuario"],
                "nucleo": nucleo_usuario,
                "mensagem": mensagem.strip(),
                "data": str(agora_br().strftime("%d/%m/%Y %H:%M"))
            }
            banco["feed"].insert(0, novo_post) # Adiciona no topo
            salvar_banco_json(banco)
            st.rerun()

    st.write("---")
    
    # Exibição das postagens (Filtrando por núcleo ou gerais)
    feed_visivel = [p for p in banco["feed"] if p["nucleo"] in [nucleo_usuario, "Geral", "Comunicação", "Administrativo", "Apoio"]]
    
    if not feed_visivel:
        st.markdown("<p style='font-size: 12px; color: #7f8c8d; text-align: center;'>Nenhuma atualização recente.</p>", unsafe_allow_html=True)
    
    for post in feed_visivel:
        st.markdown(f"""
        <div style="padding: 12px; border-left: 3px solid #ab875f; background-color: #fcfcfc; margin-bottom: 10px; border-radius: 0 4px 4px 0;">
            <p style="margin: 0; font-size: 13px; color: #2c3e50;">{post['mensagem']}</p>
            <p style="margin: 5px 0 0 0; font-size: 10px; color: #95a5a6; font-weight: 600; text-transform: uppercase;">
                {post['autor']} • {post['data']} <span style="background-color: #253a58; color: white; padding: 2px 6px; border-radius: 10px; margin-left: 5px;">{post['nucleo']}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)


def modulo_kanban(nucleo_usuario):
    """Renderiza um Kanban elegante para controle de tarefas."""
    st.markdown("<h3 style='color: #253a58; font-size: 16px; font-weight: 800;'>Painel de Tarefas</h3>", unsafe_allow_html=True)
    banco = inicializar_chaves_banco()
    
    # Filtra tarefas do núcleo
    tarefas_nucleo = [t for t in banco["tarefas"] if t["nucleo"] == nucleo_usuario]
    
    with st.expander("➕ Adicionar Nova Tarefa"):
        with st.form("form_nova_tarefa", clear_on_submit=True):
            titulo = st.text_input("Título da Tarefa")
            desc = st.text_area("Descrição (opcional)", height=60)
            col_t1, col_t2 = st.columns(2)
            responsavel = col_t1.text_input("Responsável (opcional)")
            prioridade = col_t2.selectbox("Prioridade", ["Baixa", "Média", "Alta"])
            submit_tarefa = st.form_submit_button("Criar Tarefa")
            
            if submit_tarefa and titulo.strip():
                nova_tarefa = {
                    "id": str(uuid.uuid4())[:8],
                    "titulo": titulo.strip(),
                    "descricao": desc.strip(),
                    "responsavel": responsavel.strip() or "Não atribuído",
                    "prioridade": prioridade,
                    "status": "A Fazer",
                    "nucleo": nucleo_usuario
                }
                banco["tarefas"].append(nova_tarefa)
                salvar_banco_json(banco)
                st.rerun()

    # Layout do Kanban
    col_todo, col_doing, col_done = st.columns(3)
    status_map = {"A Fazer": col_todo, "Em Andamento": col_doing, "Concluído": col_done}
    cores_pri = {"Baixa": "#a8cf45", "Média": "#ffc713", "Alta": "#ff81ba"}

    for status, coluna in status_map.items():
        with coluna:
            st.markdown(f"""
            <div style="background-color: #253a58; color: white; padding: 6px; text-align: center; border-radius: 4px; margin-bottom: 10px;">
                <span style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">{status}</span>
            </div>
            """, unsafe_allow_html=True)
            
            tarefas_status = [t for t in tarefas_nucleo if t["status"] == status]
            for t in tarefas_status:
                with st.container():
                    st.markdown(f"""
                    <div style="border: 1px solid #eaeaea; padding: 10px; border-radius: 6px; margin-bottom: 8px; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                        <p style="margin: 0 0 4px 0; font-size: 13px; font-weight: 700; color: #2c3e50;">{t['titulo']}</p>
                        <p style="margin: 0 0 6px 0; font-size: 11px; color: #7f8c8d;">{t['descricao'][:60]}{'...' if len(t['descricao'])>60 else ''}</p>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 9px; color: #95a5a6; text-transform: uppercase;">👤 {t['responsavel'][:10]}</span>
                            <span style="font-size: 9px; font-weight: bold; color: {cores_pri[t['prioridade']]};">• {t['prioridade']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Controles de movimento minimalistas
                    c1, c2, c3 = st.columns([1,1,1])
                    if status != "A Fazer":
                        if c1.button("⏪", key=f"back_{t['id']}", help="Mover para trás"):
                            t["status"] = "A Fazer" if status == "Em Andamento" else "Em Andamento"
                            salvar_banco_json(banco)
                            st.rerun()
                    if c2.button("🗑️", key=f"del_{t['id']}", help="Excluir tarefa"):
                        banco["tarefas"] = [x for x in banco["tarefas"] if x["id"] != t["id"]]
                        salvar_banco_json(banco)
                        st.rerun()
                    if status != "Concluído":
                        if c3.button("⏩", key=f"fwd_{t['id']}", help="Mover para frente"):
                            t["status"] = "Em Andamento" if status == "A Fazer" else "Concluído"
                            salvar_banco_json(banco)
                            st.rerun()


def modulo_solicitacoes(nucleo_usuario):
    """Renderiza área para registrar e acompanhar solicitações."""
    st.markdown("<h3 style='color: #253a58; font-size: 16px; font-weight: 800;'>Solicitações Internas</h3>", unsafe_allow_html=True)
    banco = inicializar_chaves_banco()
    
    with st.form("form_solicitacao", clear_on_submit=True):
        tipo_solicitacao = st.selectbox("Tipo de Solicitação", ["Material/Compra", "Suporte Técnico", "Criação de Design/Mídia", "Outros"])
        detalhes = st.text_area("Detalhes do Pedido", height=80)
        btn_solicitar = st.form_submit_button("Enviar Solicitação")
        
        if btn_solicitar and detalhes.strip():
            nova_req = {
                "id": str(uuid.uuid4())[:8],
                "solicitante": st.session_state["nome_usuario"],
                "nucleo_origem": nucleo_usuario,
                "tipo": tipo_solicitacao,
                "detalhes": detalhes.strip(),
                "status": "Pendente",
                "data": str(agora_br().strftime("%d/%m/%Y"))
            }
            banco["solicitacoes"].append(nova_req)
            salvar_banco_json(banco)
            st.success("Solicitação enviada!")
            st.rerun()
            
    st.write("---")
    st.markdown("<h4 style='font-size: 13px; color: #7f8c8d; text-transform: uppercase;'>Minhas Solicitações Ativas</h4>", unsafe_allow_html=True)
    
    minhas_reqs = [s for s in banco["solicitacoes"] if s["nucleo_origem"] == nucleo_usuario and s["status"] != "Arquivada"]
    if not minhas_reqs:
        st.markdown("<p style='font-size: 12px; color: #bdc3c7;'>Nenhuma solicitação pendente.</p>", unsafe_allow_html=True)
    else:
        for req in minhas_reqs:
            cor_status = "#ab875f" if req["status"] == "Pendente" else "#a8cf45"
            st.markdown(f"""
            <div style="font-size: 12px; padding: 8px; border-bottom: 1px solid #f0f0f0;">
                <strong>{req['tipo']}</strong> — {req['detalhes'][:50]}...
                <br>
                <span style="font-size: 10px; color: {cor_status}; font-weight: bold;">Status: {req['status']}</span> 
                <span style="font-size: 10px; color: #95a5a6;">| {req['data']}</span>
            </div>
            """, unsafe_allow_html=True)
            # ==========================================
# 10. MÓDULOS PEDAGÓGICOS (BLOCO 5)
# ==========================================

def modulo_matricula_apadrinhamento():
    """Renderiza a gestão de matrículas e apadrinhamento."""
    st.markdown("<h3 style='color: #253a58; font-size: 16px; font-weight: 800;'>Matrícula e Apadrinhamento</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 12px; color: #7f8c8d;'>Gerencie as alocações de alunos nas salas e os vínculos com os padrinhos/madrinhas.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.selectbox("Filtrar por Sala", ["Todas", "SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"], key="filtro_sala_mat")
    with col2:
        st.text_input("Buscar Aluno ou Padrinho", placeholder="Digite o nome...", key="busca_mat")
        
    st.write("---")
    st.info("A tabela de matrículas será carregada do Google Sheets aqui, exibindo o status de apadrinhamento de forma compacta.")

def modulo_turno_estendido():
    """Renderiza a gestão do turno estendido."""
    st.markdown("<h3 style='color: #253a58; font-size: 16px; font-weight: 800;'>Turno Estendido</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 12px; color: #7f8c8d;'>Controle de frequência e atividades do contraturno.</p>", unsafe_allow_html=True)
    
    st.date_input("Data do Registro", value=agora_br().date(), key="data_te")
    
    st.markdown("""
    <div style="border: 1px solid #eaeaea; padding: 12px; border-radius: 6px; background-color: #fcfcfc;">
        <p style="font-size: 12px; margin: 0; color: #2c3e50; font-weight: 600;">Lista de Presença Rápida</p>
    </div>
    """, unsafe_allow_html=True)
    st.warning("Integração com a base de dados do Turno Estendido em desenvolvimento.")

def modulo_tabua_mare():
    """Renderiza a avaliação pedagógica (Tábua da Maré)."""
    st.markdown("<h3 style='color: #253a58; font-size: 16px; font-weight: 800;'>Tábua da Maré (Alfabetização)</h3>", unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.selectbox("Selecionar Aluno", ["Selecione um aluno..."], key="aluno_mare")
    with col_t2:
        st.selectbox("Nível Atual", NIVEIS_ALF, key="nivel_mare")
        
    st.write("---")
    st.markdown("<p style='font-size: 12px; font-weight: 700; color: #ab875f; text-transform: uppercase;'>Evidências de Aprendizagem</p>", unsafe_allow_html=True)
    
    # Exemplo de check-list minimalista baseado nas evidências do nível 1
    for evidencia in EVIDENCIAS_POR_NIVEL["1. Pré-Silábico"]:
        st.checkbox(evidencia, key=f"ev_{evidencia}")
        
    st.button("Salvar Avaliação", use_container_width=True)

def modulo_indicadores():
    """Renderiza os gráficos e métricas pedagógicas."""
    st.markdown("<h3 style='color: #253a58; font-size: 16px; font-weight: 800;'>Indicadores de Desempenho</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total de Alunos", value="124")
    with col2:
        st.metric(label="Média de Frequência", value="92%")
    with col3:
        st.metric(label="Avanços na Maré", value="+15", delta="Este mês")
        
    st.write("---")
    st.markdown("<p style='font-size: 12px; color: #7f8c8d; text-align: center;'>Os gráficos dinâmicos serão renderizados aqui utilizando Plotly.</p>", unsafe_allow_html=True)

def modulo_canal_apadrinhamento():
    """Renderiza o canal de comunicação para Padrinhos/Madrinhas."""
    st.markdown("<h3 style='color: #253a58; font-size: 16px; font-weight: 800;'>Canal do Apadrinhamento</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 12px; color: #7f8c8d;'>Acompanhe o desenvolvimento do seu afilhado(a) e receba atualizações da equipe.</p>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="padding: 15px; border-left: 3px solid #ab875f; background-color: #f9f9f9; border-radius: 0 6px 6px 0; margin-top: 15px;">
        <h4 style="margin: 0 0 5px 0; font-size: 13px; color: #253a58;">Atualização Semanal - Sala Azul</h4>
        <p style="margin: 0; font-size: 12px; color: #2c3e50;">Nesta semana, trabalhamos a coordenação motora fina e a identificação das vogais. As crianças demonstraram grande interesse nas atividades de pintura com os dedos!</p>
        <p style="margin: 8px 0 0 0; font-size: 9px; color: #95a5a6; font-weight: bold; text-transform: uppercase;">Equipe Pedagógica • Ontem</p>
    </div>
    """, unsafe_allow_html=True)
