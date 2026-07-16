import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import unicodedata
import gspread
import datetime
import json
import base64
import io
import uuid
import hashlib
import secrets
from PIL import Image
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection

# Tratamento para fuso horário brasileiro
try:
    from zoneinfo import ZoneInfo
    FUSO_BR = ZoneInfo("America/Bahia")
except Exception:
    class UTC3(datetime.tzinfo):
        def utcoffset(self, dt): return datetime.timedelta(hours=-3)
        def tzname(self, dt): return "America/Bahia"
        def dst(self, dt): return datetime.timedelta(0)
    FUSO_BR = UTC3()

def agora_br():
    """Retorna a data e hora do Brasil (Bahia), independente do fuso do servidor."""
    return datetime.datetime.now(FUSO_BR)

# Configuração da página - Tema Premium unificado
st.set_page_config(
    page_title="Sistema Integrado IMLA",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# --- CONSTANTES E CONFIGURAÇÕES DE SISTEMA ---
# ==============================================================================
# Sistema 1: Gestão Mãe Lalu
ID_PLANILHA = "1Zj8u67oAWKgYRd2uOkGssdaxXnwdsKsZBDxeLChnBr4"
ARQUIVO_BUFFER = "buffer_estendido.csv"
ARQUIVO_DADOS_TE = "dados_turno_estendido.csv"
ARQUIVO_TABUA_MARE_LOCAL = "tabua_mare_registros_locais.csv"

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"
C_AZUL_MARE = "#8fd9fb"

# Cores da Identidade Visual Premium
C_PRIMARY = "#253a58"
C_ACCENT = "#ab875f"

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

# Sistema 2: Intranet IMLA
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
        "subtitulo": "Espaço de Trabalho e Comunicação Interna",
        "sair": "Sair", "encolher": "Fechar Perfil", "perfil": "Perfil",
        "logado_como": "Conectado como", "nucleo_label": "Núcleo", "email_label": "E-mail",
        "buscar_placeholder": "Buscar...", "aba_novidades": "Novidades", "aba_tarefas": "Demandas",
        "aba_lembretes": "Avisos", "aba_solicitacoes": "Solicitações", "compartilhar": "Compartilhar algo novo",
        "publicar": "Publicar", "acessar_drive": "📂 Acessar Drive", "cronogramas": "📊 Cronogramas",
        "restrito_links": "🔒 Faça login para acessar o Drive e as planilhas.", "nova_demanda": "Nova demanda",
        "titulo_demanda": "Título da demanda", "descricao_demanda": "Descrição (o que precisa ser feito)",
        "prioridade": "Prioridade", "adicionar_demanda": "+ Adicionar demanda", "criado_por": "Criado por",
        "editar": "✏️ Edit", "salvar": "Salvar alterações", "excluir_tarefa": "🗑️ Excluir tarefa",
        "excluir_lembrete": "🗑️ Excluir lembrete", "status": "Status",
        "restrito_edicao": "🔒 Apenas membros deste núcleo podem editar.", "novo_lembrete": "Novo lembrete",
        "titulo_lembrete": "Nome da tarefa", "descricao_lembrete": "O que precisa ser feito",
        "proxima_data": "Próxima data", "adicionar_lembrete": "💾 Salvar", "sem_lembretes": "Nenhum lembrete cadastrado.",
        "enviar_solicitacao": "Enviar solicitação", "para_nucleo": "Para qual setor?", "assunto": "Assunto",
        "mensagem": "Mensagem", "visibilidade": "Visibilidade", "publica": "Pública (todos podem ver)",
        "privada": "Privada (só o núcleo destino)", "enviar": "Enviar", "enviado": "Enviado com sucesso!",
        "caixa_entrada": "Caixa de Entrada", "restrito_caixa": "🔒 Restrito aos membros deste núcleo.",
        "visitante_solicitacoes": "👁️ Você está vendo apenas as solicitações públicas deste núcleo.", "de": "De",
    },
    "en": {
        "titulo_sistema": "IMLA System",
        "subtitulo": "Workspace & Internal Communication",
        "sair": "Log out", "encolher": "Close Profile", "perfil": "Profile",
        "logado_como": "Signed in as", "nucleo_label": "Team", "email_label": "E-mail",
        "buscar_placeholder": "Search...", "aba_novidades": "Updates", "aba_tarefas": "Tasks",
        "aba_lembretes": "Reminders", "aba_solicitacoes": "Requests", "compartilhar": "Share something new",
        "publicar": "Post", "acessar_drive": "📂 Open Drive", "cronogramas": "📊 Timelines",
        "restrito_links": "🔒 Log in to access Drive and spreadsheets.", "nova_demanda": "New task",
        "titulo_demanda": "Task title", "descricao_demanda": "Description (what needs to be done)",
        "prioridade": "Priority", "adicionar_demanda": "+ Add task", "criado_por": "Created by",
        "editar": "✏️ Edit", "salvar": "Save changes", "excluir_tarefa": "🗑️ Delete task",
        "excluir_lembrete": "🗑️ Delete reminder", "status": "Status",
        "restrito_edicao": "🔒 Only members of this team can edit.", "novo_lembrete": "New reminder",
        "titulo_lembrete": "Recurring task name", "descricao_lembrete": "What needs to be done",
        "proxima_data": "Next date", "adicionar_lembrete": "💾 Save", "sem_lembretes": "No reminders yet.",
        "enviar_solicitacao": "Send request", "para_nucleo": "Which team?", "assunto": "Subject",
        "mensagem": "Message", "visibilidade": "Visibility", "publica": "Public (everyone can see)",
        "privada": "Private (destination team only)", "enviar": "Send", "enviado": "Sent successfully!",
        "caixa_entrada": "Inbox", "restrito_caixa": "🔒 Restricted to members of this team.",
        "visitante_solicitacoes": "👁️ You're seeing only the public requests for this team.", "de": "From",
    }
}

def t(chave):
    idioma = st.session_state.get("idioma", "pt")
    return TEXTOS.get(idioma, TEXTOS["pt"]).get(chave, chave)

# ==============================================================================
# --- INICIALIZAÇÃO DE CONEXÕES E BANCO DE DADOS ---
# ==============================================================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Erro ao inicializar conexão com Google Sheets: {e}")
    conn = None

@st.cache_data(ttl=600, show_spinner=False)
def ler_planilha(worksheet_name: str) -> pd.DataFrame:
    if conn is None:
        return pd.DataFrame()
    try:
        df = conn.read(worksheet=worksheet_name).fillna("")
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.warning(f"Não foi possível carregar a aba '{worksheet_name}': {e}")
        return pd.DataFrame()

# Carregamento das planilhas gerais
df_g = ler_planilha("GERAL")
df_alf = ler_planilha("TURNO_ESTENDIDO")
df_aval = ler_planilha("TABUA_MARE")

def get_gspread_client():
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds = Credentials.from_service_account_info(st.secrets["connections"]["gsheets"], scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro nas credenciais do gspread: {e}")
        return None

# Persistência JSON para Intranet IMLA
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

    # Normalização de dados do banco
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

        novas_tarefas = []
        for tarefa in nd.get("tarefas", []):
            if isinstance(tarefa, str):
                novas_tarefas.append({
                    "id": str(uuid.uuid4())[:8], "titulo": tarefa, "status": "Criada",
                    "prioridade": "Média", "descricao": "", "autor_nome": "—", "data_hora": ""
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

# Inicialização segura do estado da sessão
if "dados_carregados" not in st.session_state:
    dados_carregadas = carregar_banco()
    st.session_state.usuarios = dados_carregadas["usuarios"]
    st.session_state.nucleos_dados = dados_carregadas["nucleos_dados"]
    st.session_state.caixa_entrada = dados_carregadas["caixa_entrada"]
    st.session_state.dados_carregados = True

# Segurança e Hash de Senhas
def hash_senha(senha, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return salt, h.hex()

def verificar_senha(senha, salt, hash_esperado):
    _, h = hash_senha(senha, salt)
    return secrets.compare_digest(h, hash_esperado)

# ==============================================================================
# --- FUNÇÕES INTERNAS E MANIPULAÇÃO DE DADOS (MÃE LALU) ---
# ==============================================================================
def _upsert_csv(caminho, chaves, novo_registro):
    if os.path.exists(caminho):
        df = pd.read_csv(caminho).fillna("")
    else:
        df = pd.DataFrame(columns=list(novo_registro.keys()))
    for col in novo_registro:
        if col not in df.columns:
            df[col] = ""
    mask = pd.Series([True] * len(df))
    for k in chaves:
        mask = mask & (df[k].astype(str) == str(novo_registro[k]))
    if mask.any():
        for k, v in novo_registro.items():
            df.loc[mask, k] = v
    else:
        df = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)
    df.to_csv(caminho, index=False)

def salvar_dados_locais_te(aluno, sala, avaliacao_tipo, nivel, evidencias_str, obs, ano):
    MAP_ETAPA_COL = {
        "1ª Avaliação":    "1ª AVALIAÇÃO",
        "2ª Avaliação":    "2ª AVALIAÇÃO",
        "Avaliação Final": "AVALIAÇÃO FINAL",
    }
    col_destino = MAP_ETAPA_COL.get(avaliacao_tipo)
    if not col_destino:
        return

    if os.path.exists(ARQUIVO_DADOS_TE):
        df = pd.read_csv(ARQUIVO_DADOS_TE).fillna("")
    else:
        df = pd.DataFrame(columns=["ALUNO", "SALA", "ANO",
                                    "1ª AVALIAÇÃO", "2ª AVALIAÇÃO", "AVALIAÇÃO FINAL",
                                    "DIAGNÓSTICO", "EVIDÊNCIAS", "OBSERVAÇÕES"])

    for col in ["ALUNO", "SALA", "ANO", "1ª AVALIAÇÃO", "2ª AVALIAÇÃO",
                "AVALIAÇÃO FINAL", "DIAGNÓSTICO", "EVIDÊNCIAS", "OBSERVAÇÕES"]:
        if col not in df.columns:
            df[col] = ""

    mask = (
        (df["ALUNO"].astype(str).str.strip() == str(aluno).strip()) &
        (df["ANO"].astype(str).str.strip() == str(ano).strip())
    )

    if mask.any():
        idx = df.index[mask][0]
        df.at[idx, col_destino] = nivel
        df.at[idx, "SALA"] = sala
        df.at[idx, "DIAGNÓSTICO"] = nivel
        if evidencias_str:
            df.at[idx, "EVIDÊNCIAS"] = evidencias_str
        if obs:
            df.at[idx, "OBSERVAÇÕES"] = obs
    else:
        nova = {
            "ALUNO": aluno, "SALA": sala, "ANO": str(ano),
            "1ª AVALIAÇÃO": "", "2ª AVALIAÇÃO": "", "AVALIAÇÃO FINAL": "",
            "DIAGNÓSTICO": nivel,
            "EVIDÊNCIAS": evidencias_str, "OBSERVAÇÕES": obs,
        }
        nova[col_destino] = nivel
        df = pd.concat([df, pd.DataFrame([nova])], ignore_index=True)

    df.to_csv(ARQUIVO_DADOS_TE, index=False)

def salvar_buffer_local(aluno, sala, avaliacao_tipo, nivel, evidencias_list, obs, ano):
    hoje = agora_br().strftime("%d/%m/%Y")
    evid_str = ", ".join(evidencias_list) if evidencias_list else ""
    novo_buf = {
        "ALUNO": aluno, "SALA": sala, "ETAPA": avaliacao_tipo,
        "NIVEL": nivel, "EVIDENCIAS": evid_str, "OBS": obs,
        "ANO": str(ano), "DATA": hoje,
    }
    _upsert_csv(ARQUIVO_BUFFER, ["ALUNO", "ANO", "ETAPA"], novo_buf)
    salvar_dados_locais_te(aluno, sala, avaliacao_tipo, nivel, evid_str, obs, ano)
    return True

def enviar_buffer_para_sheets():
    if not os.path.exists(ARQUIVO_BUFFER):
        st.info("Não há registros pendentes para sincronizar.")
        return
    df_pendente = pd.read_csv(ARQUIVO_BUFFER)
    if df_pendente.empty:
        st.info("Fila de registros está vazia.")
        return
    client = get_gspread_client()
    if client is None:
        return
    sh = client.open_by_key(ID_PLANILHA)
    wks = sh.worksheet("TURNO_ESTENDIDO")
    col_map = {"1ª Avaliação": "C", "2ª Avaliação": "D", "Avaliação Final": "E"}
    sucessos = 0
    for _, row in df_pendente.iterrows():
        try:
            dados = wks.get_all_records()
            df_temp = pd.DataFrame(dados)
            linha_encontrada = -1
            if not df_temp.empty:
                df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
                filtro_vazio = (
                    (df_temp["ALUNO"].astype(str).str.strip() == str(row["ALUNO"]).strip()) &
                    (df_temp["ANO"].astype(str).str.strip() == "")
                )
                indices_vazios = df_temp.index[filtro_vazio].tolist()
                if indices_vazios:
                    linha_encontrada = indices_vazios[0] + 2
                else:
                    filtro_ano = (
                        (df_temp["ALUNO"].astype(str).str.strip() == str(row["ALUNO"]).strip()) &
                        (df_temp["ANO"].astype(str).str.strip() == str(row["ANO"]).strip())
                    )
                    indices_ano = df_temp.index[filtro_ano].tolist()
                    if indices_ano:
                        linha_encontrada = indices_ano[0] + 2
            etapa = str(row["ETAPA"])
            nivel = str(row["NIVEL"])
            evid  = str(row.get("EVIDENCIAS", ""))
            obs   = str(row.get("OBS", ""))
            ano   = str(row["ANO"])
            if linha_encontrada != -1:
                letra_col = col_map.get(etapa, "C")
                wks.update(range_name=f"F{linha_encontrada}", values=[[ano]])
                wks.update(range_name=f"{letra_col}{linha_encontrada}", values=[[nivel]])
                wks.update(range_name=f"G{linha_encontrada}", values=[[nivel]])
                if obs:
                    wks.update(range_name=f"I{linha_encontrada}", values=[[obs]])
                if evid:
                    wks.update(range_name=f"H{linha_encontrada}", values=[[evid]])
            else:
                nova_linha = [row["ALUNO"], row["SALA"], "", "", "", ano, "", evid, obs, str(row.get("DATA", ""))]
                idx_etapa = {"1ª Avaliação": 2, "2ª Avaliação": 3, "Avaliação Final": 4}.get(etapa, 2)
                nova_linha[idx_etapa] = nivel
                nova_linha[6] = nivel
                wks.append_row(nova_linha)
            sucessos += 1
        except Exception as e:
            st.warning(f"Falha ao sincronizar {row['ALUNO']}: {e}")
    if sucessos == len(df_pendente):
        st.success(f"🎉 {sucessos} registro(s) enviado(s) com sucesso!")
        os.remove(ARQUIVO_BUFFER)
        st.cache_data.clear()
        st.rerun()
    else:
        st.warning(f"⚠️ {sucessos}/{len(df_pendente)} registros sincronizados. Verifique os avisos acima.")

def registrar_matricula_te(aluno, sala):
    salvar_buffer_local(aluno=aluno, sala=sala, avaliacao_tipo="MATRÍCULA",
                        nivel="", evidencias_list=[], obs="", ano="")
    try:
        client = get_gspread_client()
        if client:
            sh  = client.open_by_key(ID_PLANILHA)
            wks = sh.worksheet("TURNO_ESTENDIDO")
            hoje = agora_br().strftime("%d/%m/%Y")
            wks.append_row([aluno, sala, "", "", "", "", "", "", "", hoje])
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao matricular: {e}")
        return False

def normalizar_texto(valor):
    texto = "" if pd.isna(valor) else str(valor)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return " ".join(texto.strip().upper().split())

def normalizar_sala_tabua(valor):
    texto = normalizar_texto(valor)
    if texto.startswith("SALA "):
        texto = texto.replace("SALA ", "", 1)
    return texto.split(" - ")[0].strip()

def sala_para_tabua(valor):
    texto = str(valor).replace("**", "").strip()
    if texto.upper().startswith("SALA "):
        texto = texto[5:].strip()
    return texto

def colunas_tabua_mare():
    return ["ALUNO", "SALA/TURMA", "SEMESTRE"] + [c.upper() for c in CATEGORIAS] + [
        "OBSERVAÇÕES PEDAGÓGICAS", "DATA_REGISTRO", "STATUS_ENVIO"
    ]

def carregar_tabua_mare_local():
    if os.path.exists(ARQUIVO_TABUA_MARE_LOCAL):
        df = pd.read_csv(ARQUIVO_TABUA_MARE_LOCAL).fillna("")
    else:
        df = pd.DataFrame(columns=colunas_tabua_mare())
    df.columns = [str(c).strip().upper() for c in df.columns]
    for col in colunas_tabua_mare():
        if col not in df.columns:
            df[col] = ""
    return df

def linha_tem_avaliacao_tabua(row):
    for cat in CATEGORIAS:
        valor = row.get(cat.upper(), row.get(cat, ""))
        if str(valor).strip():
            return True
    for col in ["SEMESTRE", "OBSERVAÇÕES PEDAGÓGICAS", "OBSERVACOES"]:
        if str(row.get(col, "")).strip():
            return True
    return False

def obter_tabua_mare_para_visualizacao():
    df_nuvem = df_aval.copy()
    df_nuvem.columns = [str(c).strip().upper() for c in df_nuvem.columns]
    df_local = carregar_tabua_mare_local()
    frames = [df for df in [df_nuvem, df_local] if not df.empty]
    if not frames:
        return pd.DataFrame(columns=colunas_tabua_mare())
    df = pd.concat(frames, ignore_index=True).fillna("")
    for col in colunas_tabua_mare():
        if col not in df.columns:
            df[col] = ""
    if "ALUNO" in df.columns and "SEMESTRE" in df.columns:
        df["_CHAVE_ALUNO"] = df["ALUNO"].apply(normalizar_texto)
        df["_CHAVE_SEMESTRE"] = df["SEMESTRE"].apply(normalizar_texto)
        df = df.drop_duplicates(subset=["_CHAVE_ALUNO", "_CHAVE_SEMESTRE"], keep="last")
        df = df.drop(columns=["_CHAVE_ALUNO", "_CHAVE_SEMESTRE"])
    return df

def registrar_tabua_mare(aluno, sala, semestre, notas_dict, obs):
    try:
        df_atual = carregar_tabua_mare_local()
        registro = {
            "ALUNO": str(aluno).strip(),
            "SALA/TURMA": sala_para_tabua(sala),
            "SEMESTRE": semestre,
            "OBSERVAÇÕES PEDAGÓGICAS": obs,
            "DATA_REGISTRO": agora_br().strftime("%d/%m/%Y %H:%M"),
            "STATUS_ENVIO": "PENDENTE",
        }
        for cat in CATEGORIAS:
            registro[cat.upper()] = notas_dict.get(cat, "")
        for col in colunas_tabua_mare():
            if col not in df_atual.columns:
                df_atual[col] = ""
        mask = (
            (df_atual["ALUNO"].apply(normalizar_texto) == normalizar_texto(aluno)) &
            (df_atual["SEMESTRE"].apply(normalizar_texto) == normalizar_texto(semestre))
        )
        if mask.any():
            idx = df_atual.index[mask][0]
            for col, valor in registro.items():
                df_atual.at[idx, col] = valor
        else:
            df_atual = pd.concat([df_atual, pd.DataFrame([registro])], ignore_index=True)
        df_atual.to_csv(ARQUIVO_TABUA_MARE_LOCAL, index=False)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar na Tábua da Maré: {e}")
        return False

def enviar_tabua_mare_local_para_sheets():
    df_pendente = carregar_tabua_mare_local()
    if df_pendente.empty:
        st.info("Não há avaliações pendentes para enviar.")
        return
    client = get_gspread_client()
    if client is None:
        return
    try:
        from gspread.utils import rowcol_to_a1
        sh = client.open_by_key(ID_PLANILHA)
        wks = sh.worksheet("TABUA_MARE")
        headers_originais = wks.row_values(1)
        headers = [str(h).strip().upper() for h in headers_originais]
        header_map = {normalizar_texto(h): i + 1 for i, h in enumerate(headers)}
        df_sheet = pd.DataFrame(wks.get_all_records()).fillna("")
        df_sheet.columns = [str(c).strip().upper() for c in df_sheet.columns]
        if "ALUNO" not in df_sheet.columns:
            st.error("A aba TABUA_MARE não possui a coluna ALUNO.")
            return
        col_sala = next((c for c in ["SALA/TURMA", "SALA", "TURMA"] if c in df_sheet.columns), "")
        registros_restantes = []
        sucessos = 0
        for _, row in df_pendente.iterrows():
            aluno = str(row.get("ALUNO", "")).strip()
            semestre = str(row.get("SEMESTRE", "")).strip()
            sala_local = str(row.get("SALA/TURMA", row.get("SALA", ""))).strip()
            candidatos = df_sheet[df_sheet["ALUNO"].apply(normalizar_texto) == normalizar_texto(aluno)]
            if candidatos.empty:
                st.warning(f"Aluno não encontrado na TABUA_MARE: {aluno}")
                registros_restantes.append(row.to_dict())
                continue
            if col_sala:
                candidatos_sala = candidatos[candidatos[col_sala].apply(normalizar_sala_tabua) == normalizar_sala_tabua(sala_local)]
                if candidatos_sala.empty:
                    sala_planilha = str(candidatos.iloc[0].get(col_sala, "")).strip()
                    st.warning(f"Sala divergente para {aluno}: app={sala_local}, planilha={sala_planilha}")
                    registros_restantes.append(row.to_dict())
                    continue
                candidatos = candidatos_sala
            if "SEMESTRE" in df_sheet.columns:
                mesmo_semestre = candidatos[candidatos["SEMESTRE"].apply(normalizar_texto) == normalizar_texto(semestre)]
                if not mesmo_semestre.empty:
                    idx_planilha = mesmo_semestre.index[0]
                else:
                    semestre_vazio = candidatos[candidatos["SEMESTRE"].apply(normalizar_texto) == ""]
                    idx_planilha = semestre_vazio.index[0] if not semestre_vazio.empty else candidatos.index[0]
            else:
                idx_planilha = candidatos.index[0]
            linha_planilha = idx_planilha + 2
            campos = {"SEMESTRE": semestre, "OBSERVAÇÕES PEDAGÓGICAS": str(row.get("OBSERVAÇÕES PEDAGÓGICAS", ""))}
            for cat in CATEGORIAS:
                campos[cat.upper()] = str(row.get(cat.upper(), "")).strip()
            updates = []
            for col, valor in campos.items():
                col_num = header_map.get(normalizar_texto(col))
                if col_num:
                    celula = rowcol_to_a1(linha_planilha, col_num)
                    updates.append({"range": celula, "values": [[valor]]})
            try:
                if updates:
                    try:
                        wks.batch_update(updates, value_input_option="USER_ENTERED")
                    except TypeError:
                        wks.batch_update(updates)
                sucessos += 1
            except Exception as e:
                st.warning(f"Falha ao enviar {aluno}: {e}")
                registros_restantes.append(row.to_dict())
        if registros_restantes:
            pd.DataFrame(registros_restantes).to_csv(ARQUIVO_TABUA_MARE_LOCAL, index=False)
            st.warning(f"{sucessos}/{len(df_pendente)} avaliação(ões) enviada(s). Corrija os avisos e tente novamente.")
        else:
            if os.path.exists(ARQUIVO_TABUA_MARE_LOCAL):
                os.remove(ARQUIVO_TABUA_MARE_LOCAL)
            st.success(f"{sucessos} avaliação(ões) enviada(s) para a aba TABUA_MARE.")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao enviar avaliações para a TABUA_MARE: {e}")

def atualizar_padrinho_sheets(sala, aluno, nome_padrinho):
    try:
        client = get_gspread_client()
        if client is None:
            return False
        sh  = client.open_by_key(ID_PLANILHA)
        wks = sh.worksheet(sala)
        dados = wks.get_all_records()
        df_temp = pd.DataFrame(dados)
        df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
        if "PADRINHO/MADRINHA" not in df_temp.columns or "ALUNO" not in df_temp.columns:
            st.error("Colunas necessárias não encontradas.")
            return False
        indices = df_temp.index[df_temp["ALUNO"].astype(str).str.strip() == str(aluno).strip()].tolist()
        if not indices:
            st.error("Aluno não encontrado na aba.")
            return False
        linha = indices[0] + 2
        col_idx = list(df_temp.columns).index("PADRINHO/MADRINHA") + 1
        wks.update_cell(linha, col_idx, nome_padrinho)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar padrinho: {e}")
        return False

def get_text_color(nivel=None):
    return "#2C3E50"

def obter_ultimo_diagnostico(aluno_sel, df_logica, col_aluno, col_diag):
    ultimo_nv = "Sem registro"
    if col_aluno:
        df_al = df_logica[df_logica[col_aluno].astype(str).str.strip() == aluno_sel]
        if not df_al.empty:
            for c_av in ["AVALIAÇÃO FINAL", "2ª AVALIAÇÃO", "1ª AVALIAÇÃO"]:
                if c_av in df_al.columns:
                    val = str(df_al[c_av].iloc[-1]).strip()
                    if val and val not in ["nan", "None", ""]:
                        ultimo_nv = val
                        break
            if ultimo_nv == "Sem registro" and col_diag and col_diag in df_al.columns:
                val = str(df_al[col_diag].iloc[-1]).strip()
                if val and val not in ["nan", "None", ""]:
                    ultimo_nv = val

    if os.path.exists(ARQUIVO_BUFFER):
        df_buf_local = pd.read_csv(ARQUIVO_BUFFER)
        buf_aluno = df_buf_local[df_buf_local["ALUNO"].astype(str).str.strip() == aluno_sel]
        if not buf_aluno.empty and "NIVEL" in buf_aluno.columns:
            ultimo_nv_buf = str(buf_aluno["NIVEL"].iloc[-1]).strip()
            if ultimo_nv_buf and ultimo_nv_buf not in ["nan", "None", ""]:
                ultimo_nv = ultimo_nv_buf

    if os.path.exists(ARQUIVO_DADOS_TE):
        df_dados = pd.read_csv(ARQUIVO_DADOS_TE).fillna("")
        mask = df_dados["ALUNO"].astype(str).str.strip() == aluno_sel
        if mask.any():
            row = df_dados[mask].iloc[-1]
            for c_av in ["AVALIAÇÃO FINAL", "2ª AVALIAÇÃO", "1ª AVALIAÇÃO", "DIAGNÓSTICO"]:
                if c_av in df_dados.columns:
                    val = str(row.get(c_av, "")).strip()
                    if val and val not in ["nan", "None", ""]:
                        ultimo_nv = val
                        break
    return ultimo_nv

def detectar_sala_config(valor):
    texto = normalizar_texto(valor)
    for sala in TURMAS_CONFIG:
        sala_norm = normalizar_texto(sala)
        if texto == sala_norm or texto in sala_norm or sala_norm in texto:
            return sala
    if "ROSA" in texto: return "SALA ROSA"
    if "AMARELA" in texto or "AMARELO" in texto: return "SALA AMARELA"
    if "VERDE" in texto: return "SALA VERDE"
    if "AZUL" in texto: return "SALA AZUL"
    if "MUNDO" in texto or "CIRAND" in texto: return "CIRAND. MUNDO"
    return ""

def carregar_turno_estendido_completo():
    colunas_te = ["ALUNO", "SALA", "ANO", "1ª AVALIAÇÃO", "2ª AVALIAÇÃO",
                  "AVALIAÇÃO FINAL", "DIAGNÓSTICO", "EVIDÊNCIAS", "OBSERVAÇÕES"]
    df_sheets = df_alf.copy()
    df_sheets.columns = [str(c).strip().upper() for c in df_sheets.columns]
    if "ANO" not in df_sheets.columns:
        df_sheets["ANO"] = "2025"
    for col in colunas_te:
        if col not in df_sheets.columns:
            df_sheets[col] = ""
    df_sheets["ANO"] = (
        pd.to_numeric(df_sheets["ANO"], errors="coerce")
        .fillna(0).astype(int).astype(str)
        .replace("0", "")
    )
    if os.path.exists(ARQUIVO_DADOS_TE):
        df_local = pd.read_csv(ARQUIVO_DADOS_TE).fillna("")
        df_local.columns = [str(c).strip().upper() for c in df_local.columns]
        for col in colunas_te:
            if col not in df_local.columns:
                df_local[col] = ""
        df_local["ANO"] = (
            pd.to_numeric(df_local["ANO"], errors="coerce")
            .fillna(0).astype(int).astype(str)
            .replace("0", "")
        )
    else:
        df_local = pd.DataFrame(columns=colunas_te)
    for _, row_loc in df_local.iterrows():
        aluno_loc = str(row_loc.get("ALUNO", "")).strip()
        ano_loc = str(row_loc.get("ANO", "")).strip()
        if not aluno_loc:
            continue
        mask = (
            (df_sheets["ALUNO"].astype(str).str.strip() == aluno_loc) &
            (df_sheets["ANO"].astype(str).str.strip() == ano_loc)
        )
        if mask.any():
            idx = df_sheets.index[mask][0]
            for col in ["1ª AVALIAÇÃO", "2ª AVALIAÇÃO", "AVALIAÇÃO FINAL",
                        "DIAGNÓSTICO", "EVIDÊNCIAS", "OBSERVAÇÕES", "SALA"]:
                val_loc = str(row_loc.get(col, "")).strip()
                if val_loc:
                    df_sheets.at[idx, col] = val_loc
        else:
            df_sheets = pd.concat([df_sheets, pd.DataFrame([row_loc])], ignore_index=True)
    return df_sheets.fillna("")

def obter_historico_te_aluno(aluno):
    df_h = carregar_turno_estendido_completo()
    if df_h.empty or "ALUNO" not in df_h.columns:
        return pd.DataFrame()
    df_al = df_h[df_h["ALUNO"].apply(normalizar_texto) == normalizar_texto(aluno)].copy()
    if df_al.empty:
        return df_al
    df_al["_ANO_NUM"] = pd.to_numeric(df_al.get("ANO", ""), errors="coerce").fillna(0)
    df_al = df_al.sort_values("_ANO_NUM")
    return df_al.drop(columns=["_ANO_NUM"])

def extrair_resumo_te(df_al):
    niveis_seq = []
    avaliacoes_por_ano = {}
    for _, row in df_al.iterrows():
        ano = str(row.get("ANO", "")).strip() or "Sem ano"
        avaliacoes_por_ano.setdefault(ano, [])
        for label, col in [("1ª Avaliação", "1ª AVALIAÇÃO"), ("2ª Avaliação", "2ª AVALIAÇÃO"), ("Avaliação Final", "AVALIAÇÃO FINAL")]:
            val = str(row.get(col, "")).strip()
            if val and val not in ["nan", "None"]:
                avaliacoes_por_ano[ano].append((label, val))
                niveis_seq.append(val)
    ultimo = df_al.iloc[-1] if not df_al.empty else pd.Series(dtype=object)
    ultimo_nivel = ""
    for _, row in df_al.iloc[::-1].iterrows():
        for col in ["AVALIAÇÃO FINAL", "2ª AVALIAÇÃO", "1ª AVALIAÇÃO", "DIAGNÓSTICO"]:
            val = str(row.get(col, "")).strip()
            if val and val not in ["nan", "None"]:
                ultimo_nivel = val
                break
        if ultimo_nivel:
            break
    evidencias = next((str(row.get("EVIDÊNCIAS", "")).strip() for _, row in df_al.iloc[::-1].iterrows()
                       if str(row.get("EVIDÊNCIAS", "")).strip()), "---")
    observacoes = next((str(row.get("OBSERVAÇÕES", "")).strip() for _, row in df_al.iloc[::-1].iterrows()
                        if str(row.get("OBSERVAÇÕES", "")).strip()), "---")
    if not ultimo_nivel:
        ultimo_nivel = str(ultimo.get("DIAGNÓSTICO", "Sem diagnóstico")).strip() or "Sem diagnóstico"
    return ultimo_nivel, evidencias, observacoes, niveis_seq, avaliacoes_por_ano

# ==============================================================================
# --- RENDERIZADORES DE ELEMENTOS VISUAIS (UI/UX) ---
# ==============================================================================
@st.cache_data(show_spinner=False)
def imagem_base64(caminho):
    if not os.path.exists(caminho): return None
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode()

@st.cache_data(show_spinner=False)
def logo_simbolo_base64(caminho):
    if not os.path.exists(caminho): return None
    im = Image.open(caminho).convert("RGBA")
    w, h = im.size
    if w > h * 1.15:
        im = im.crop((0, 0, h, h))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

@st.cache_data(show_spinner=False)
def banner_base64(caminho, proporcao=21/6):
    if not os.path.exists(caminho): return None
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

def render_badge_sala_html(sala):
    sala_key = detectar_sala_config(sala)
    cor = TURMAS_CONFIG.get(sala_key, {}).get("cor", "#95a5a6")
    label = BADGE_LABEL.get(sala_key, str(sala).replace("SALA ", "").strip() or "—")
    return (
        f'<span style="background:{cor};color:#fff;border-radius:50px;'
        f'padding:5px 14px;font-size:10px;font-weight:800;letter-spacing:0.5px;'
        f'text-transform:uppercase;white-space:nowrap;">{label}</span>'
    )

def render_status_mare_te_html(nv_atual, hist):
    n_at = MAPA_NIVEIS.get(nv_atual, 0)
    if n_at == 0:
        return '<div class="mare-box"><span class="mare-texto-tabela">—</span></div>'
    fill_pct = max(6, round(n_at * 90 / 7))
    if n_at <= 2:
        txt = "maré baixa"
    elif n_at == 7:
        txt = "maré cheia"
    else:
        n_ant = MAPA_NIVEIS.get(hist[-2], 0) if len(hist) >= 2 else 0
        if n_ant != 0 and n_at > n_ant:
            txt = "maré enchente"
        elif n_ant != 0 and n_at < n_ant:
            txt = "maré vazante"
        else:
            if n_at in [3, 4]: txt = "maré enchente"
            elif n_at in [5, 6]: txt = "maré alta"
            else: txt = "maré estável"
    vasilha = (
        f'<div style="width:100px;height:58px;border:1px solid #bbb;border-radius:8px;'
        f'overflow:hidden;position:relative;background:#f5f8fa;display:inline-block;">'
        f'<div style="position:absolute;bottom:0;left:0;width:100%;height:{fill_pct}%;">'
        f'<svg width="100" height="14" viewBox="0 0 100 14" preserveAspectRatio="none" '
        f'style="position:absolute;top:-9px;left:0;width:100%;height:14px;display:block;">'
        f'<path d="M0,9 Q25,3 50,9 Q75,15 100,9 L100,14 L0,14 Z" fill="{C_AZUL_MARE}"/>'
        f'</svg><div style="width:100%;height:100%;background:{C_AZUL_MARE};"></div>'
        f'</div></div>'
    )
    return (
        f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:18px;text-align:center;color:#2c3e50;">'
        f'<div style="font-weight:800;margin-bottom:10px;font-size:12px;letter-spacing:0.5px;">STATUS MARÉ</div>'
        f'{vasilha}'
        f'<div style="font-size:11px;color:#2E86C1;font-weight:900;text-transform:uppercase;margin-top:8px;">{txt}</div>'
        f'</div>'
    )

def render_trilha_desenvolvimento_html(avaliacoes_por_ano):
    pontos = []
    for ano, itens in sorted(avaliacoes_por_ano.items()):
        for label, nivel in itens:
            pontos.append({"ano": ano, "label": label, "nivel": nivel})
    if not pontos:
        return '<div style="color:#7f8c8d;font-size:13px;">Sem avaliações suficientes para formar a trilha.</div>'
    html = '<div style="display:flex;align-items:center;gap:8px;overflow-x:auto;margin-top:10px;padding:8px 0;">'
    total = len(pontos)
    for i, ponto in enumerate(pontos):
        nivel = ponto["nivel"]
        cor = CORES_EXCLUSIVAS.get(nivel, "#eee")
        txt = get_text_color(nivel)
        destaque = "border:3px solid #253a58;" if i == total - 1 else "border:1px solid #ffffff;"
        etapa = "Início" if i == 0 else ("Atual" if i == total - 1 else "Evolução")
        html += (
            f'<div style="background:{cor};color:{txt};{destaque}padding:10px;border-radius:12px;'
            f'font-size:10px;font-weight:800;min-width:130px;text-align:center;line-height:1.2;'
            f'box-shadow:0 2px 6px rgba(0,0,0,0.08);">'
            f'<div style="font-size:9px;text-transform:uppercase;letter-spacing:.4px;opacity:.75;">{etapa} • {ponto["ano"]}</div>'
            f'<div style="margin-top:4px;">{ponto["label"]}</div>'
            f'<div style="margin-top:5px;font-size:11px;">{nivel.split(". ")[1] if ". " in nivel else nivel}</div>'
            f'</div>'
        )
        if i < total - 1:
            html += '<div style="font-size:20px;color:#95a5a6;font-weight:900;">→</div>'
    return html + "</div>"

def render_vasilha_mare(nivel_num, titulo):
    config = {
        1: {"pct": 85, "txt": "Maré Baixa",    "seta": ""},
        2: {"pct": 70, "txt": "Maré Vazante",   "seta": "↓"},
        3: {"pct": 45, "txt": "Maré Enchente",  "seta": "↑"},
        4: {"pct": 15, "txt": "Maré Cheia",     "seta": "↑"},
    }
    try:
        n = max(1, min(4, int(float(nivel_num))))
    except Exception:
        n = 1
    c = config[n]
    return f'''
    <div style="text-align:center;margin-bottom:20px;border:1px solid #e2e8f0;padding:10px;border-radius:10px;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.02);">
        <div style="font-size:11px;font-weight:bold;color:#253a58;min-height:35px;display:flex;align-items:center;justify-content:center;line-height:1.2;">{titulo}</div>
        <div style="width:70px;height:45px;margin:5px auto;background:linear-gradient(to bottom,#f1f5f9 {c["pct"]}%,#5DADE2 {c["pct"]}%);
                    clip-path:path('M 0 10 Q 17.5 0 35 10 T 70 10 L 70 40 Q 70 45 65 45 L 5 45 Q 0 45 0 40 Z');border:1px solid #ddd;position:relative;">
            <span style="position:absolute;right:2px;top:5px;font-size:12px;font-weight:bold;color:#2E86C1;">{c["seta"]}</span>
        </div>
        <div style="font-size:9px;color:#2E86C1;font-weight:bold;text-transform:uppercase;margin-top:5px;">{c["txt"]}</div>
    </div>'''

def render_legenda_niveis_botoes(aluno_sel, key_prefix="te"):
    st.markdown("##### 📝 Selecione o Nível de Diagnóstico")
    session_key = f"nivel_diag_{key_prefix}_{aluno_sel}"
    n_cache = len(NIVEIS_ALF)
    css_niveis = "<style>"
    for i, nv in enumerate(NIVEIS_ALF):
        cor_fundo = CORES_EXCLUSIVAS.get(nv, "#eee")
        cor_txt = get_text_color(nv)
        is_selected = st.session_state.get(session_key) == nv
        borda = f"3px solid {C_PRIMARY}" if is_selected else "2px solid transparent"
        css_niveis += (
            f'[data-testid="stHorizontalBlock"]'
            f':has(> [data-testid="stColumn"]:nth-child({n_cache}))'
            f':not(:has(> [data-testid="stColumn"]:nth-child({n_cache + 1})))'
            f' > [data-testid="stColumn"]:nth-child({i + 1}) button {{'
            f'background-color:{cor_fundo} !important;color:{cor_txt} !important;'
            f'border:{borda} !important;border-radius:10px !important;'
            f'font-weight:bold !important;font-size:10px !important;'
            f'min-height:52px !important;white-space:normal !important;'
            f'line-height:1.2 !important;}}\n'
        )
    css_niveis += "</style>"
    st.markdown(css_niveis, unsafe_allow_html=True)

    cols_leg = st.columns(n_cache)
    for i, nv in enumerate(NIVEIS_ALF):
        label_nv = nv.split(". ")[1] if ". " in nv else nv
        if cols_leg[i].button(label_nv, key=f"btn_nivel_{key_prefix}_{i}", use_container_width=True):
            st.session_state[session_key] = nv
            st.rerun()

    nivel_selecionado = st.session_state.get(session_key, None)
    if nivel_selecionado:
        cor_sel = CORES_EXCLUSIVAS.get(nivel_selecionado, "#eee")
        st.markdown(
            f'<div style="background:{cor_sel}; padding:10px 20px; border-radius:10px; margin:10px 0; '
            f'font-weight:bold; font-size:13px; color:#2c3e50; border:2px solid {C_PRIMARY};">'
            f'Nível de Diagnóstico Selecionado: {nivel_selecionado}</div>',
            unsafe_allow_html=True
        )
    return nivel_selecionado

def render_legenda_niveis():
    st.markdown("##### 📝 Legenda de Níveis")
    cols_leg = st.columns(len(NIVEIS_ALF))
    for i, nv in enumerate(NIVEIS_ALF):
        cor_fundo = CORES_EXCLUSIVAS.get(nv, "#eee")
        cor_txt = get_text_color(nv)
        cols_leg[i].markdown(
            f'<div style="background-color:{cor_fundo}; color:{cor_txt}; padding:8px 2px; border-radius:10px; '
            f'text-align:center; font-size:9px; font-weight:bold; min-height:50px; display:flex; '
            f'align-items:center; justify-content:center; line-height:1.1; box-shadow:0 1px 3px rgba(0,0,0,0.03);">'
            f'{nv.split(". ")[1]}</div>',
            unsafe_allow_html=True
        )

def render_filtros(df_geral, key_suffix):
    f1, f2 = st.columns(2)
    tn = f1.selectbox("Filtrar Turno", ["Todos", "A", "B"], key=f"tn_{key_suffix}")
    if "COMUNIDADE" in df_geral.columns:
        comu_list = ["Todas"] + sorted([c for c in df_geral["COMUNIDADE"].unique() if str(c).strip()])
    else:
        comu_list = ["Todas"]
    cm = f2.selectbox("Filtrar Comunidade", comu_list, key=f"cm_{key_suffix}")
    return tn, cm

def aplicar_filtros(df_alvo, df_geral, tn, cm):
    df_f = df_alvo.copy()
    df_f.columns = [str(c).strip().upper() for c in df_f.columns]
    if tn != "Todos":
        alunos_no_turno = df_geral[df_geral["TURNO"].astype(str).str.contains(tn, na=False)]["ALUNO"].unique()
        df_f = df_f[df_f["ALUNO"].isin(alunos_no_turno)]
    if cm != "Todas":
        if "COMUNIDADE" in df_f.columns:
            df_f = df_f[df_f["COMUNIDADE"] == cm]
        else:
            alunos_na_comu = df_geral[df_geral["COMUNIDADE"] == cm]["ALUNO"].unique()
            df_f = df_f[df_f["ALUNO"].isin(alunos_na_comu)]
    return df_f

def render_botoes_salas(key_prefix, session_key, salas_permitidas=None):
    salas = salas_permitidas if salas_permitidas else list(TURMAS_CONFIG.keys())
    n = len(salas)
    css = "<style>"
    for i, nome_aba in enumerate(salas):
        cor = TURMAS_CONFIG.get(nome_aba, {"cor": "#566573"})["cor"]
        is_active = st.session_state.get(session_key) == nome_aba
        borda = f"3px solid {C_PRIMARY}" if is_active else f"2px solid {cor}"
        op = "1" if is_active else "0.65"
        css += (
            f'[data-testid="stHorizontalBlock"]'
            f':has(> [data-testid="stColumn"]:nth-child({n}))'
            f':not(:has(> [data-testid="stColumn"]:nth-child({n + 1})))'
            f' > [data-testid="stColumn"]:nth-child({i + 1}) button {{'
            f'background-color:{cor} !important;color:white !important;'
            f'border:{borda} !important;border-radius:10px !important;'
            f'font-weight:bold !important;font-size:11px !important;'
            f'opacity:{op} !important;height:44px !important;}}\n'
        )
    css += "</style>"
    st.markdown(css, unsafe_allow_html=True)

    cols = st.columns(n)
    for i, nome_aba in enumerate(salas):
        label_exibicao = BADGE_LABEL.get(nome_aba, nome_aba.replace("SALA ", ""))
        if cols[i].button(label_exibicao, key=f"{key_prefix}_{i}", use_container_width=True):
            st.session_state[session_key] = nome_aba
            st.rerun()

# ==============================================================================
# --- ESTILIZAÇÃO E IDENTIDADE VISUAL CSS ---
# ==============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

/* Reset de Tipografia e Escopo */
html, body, [class*="css"] {{
    font-family: 'Nunito', sans-serif !important;
    background-color: #f8fafc;
}}

/* Redimensionamento elegante e discreto de fontes */
h1, [data-testid="stMarkdownContainer"] h1 {{
    font-size: 24px !important; font-weight: 800 !important; color: {C_PRIMARY} !important; margin-bottom: 5px;
}}
h2, [data-testid="stMarkdownContainer"] h2 {{
    font-size: 18px !important; font-weight: 700 !important; color: {C_PRIMARY} !important;
}}
h3, [data-testid="stMarkdownContainer"] h3 {{
    font-size: 15px !important; font-weight: 700 !important; color: {C_PRIMARY} !important;
}}
h4, h5, h6 {{ font-size: 13px !important; font-weight: 700 !important; color: #2c3e50 !important; }}
[data-testid="stMarkdownContainer"] p {{
    font-size: 13px !important; font-weight: 400 !important; line-height: 1.5 !important; color: #334155;
}}
[data-testid="stWidgetLabel"] p {{
    font-size: 12px !important; font-weight: 700 !important; color: #1e293b !important;
}}

/* Customizações de Botões Streamlit Globais */
div.stButton > button {{
    font-weight: 700 !important; font-size: 11px !important;
    border-radius: 8px !important; border: 1px solid #e2e8f0;
    transition: all 0.2s ease-in-out;
}}
div.stButton > button:hover {{
    border-color: {C_ACCENT} !important;
    color: {C_PRIMARY} !important;
}}

/* Componentes Premium Cards */
.apple-card {{
    background: #ffffff; border-radius: 16px; padding: 18px; margin-bottom: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    border: 1px solid #f1f5f9;
}}
.card-tag {{ font-size: 9px; font-weight: 800; color: {C_ACCENT}; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 5px;}}
.card-title {{ font-size: 14px; font-weight: 700; color: {C_PRIMARY}; margin-bottom: 6px;}}
.card-text {{ font-size: 12px; color: #475569; line-height: 1.5;}}
.card-footer {{ font-size: 9.5px; color: #94a3b8; margin-top: 12px;}}

/* Kanban Trello Board */
.task-card {{
    background:#fff; border-radius:12px; padding:12px; margin-bottom:10px;
    box-shadow:0 2px 8px rgba(0,0,0,0.03); border-left: 4px solid #cbd5e1;
}}
.task-titulo {{ font-weight:700; font-size:12.5px; color: {C_PRIMARY}; margin-bottom:4px; }}
.task-desc {{ font-size:11.5px; color:#475569; line-height:1.4; margin-bottom:6px; }}
.chip {{
    display:inline-block; font-size:9px; font-weight:800; color:white; padding:2px 8px;
    border-radius:20px; margin-right:4px;
}}
.task-footer {{ font-size:9px; color:#94a3b8; margin-top:8px; }}
.kanban-col-title {{ font-size:11px; font-weight:800; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px;}}

/* Lembretes / Avisos */
.lembrete-card {{
    background:#fff; border-radius:12px; padding:12px; margin-bottom:10px;
    box-shadow:0 2px 8px rgba(0,0,0,0.03); border-left: 4px solid {C_ACCENT};
}}
.lembrete-titulo {{ font-weight:700; font-size:12.5px; color: {C_PRIMARY}; margin-bottom:4px; }}
.lembrete-desc {{ font-size:11.5px; color:#475569; line-height:1.4; margin-bottom:6px; }}
.lembrete-data {{
    display:inline-block; font-size:9.5px; font-weight:800; color:{C_PRIMARY};
    background:rgba(37,58,88,0.08); padding:3px 8px; border-radius:20px;
}}
.lembrete-data.atrasado {{ color:#ef4444; background:rgba(239,68,68,0.08); }}

/* Tabelas Customizadas */
.custom-table {{
    width: 100%; border-collapse: separate; border-spacing: 0;
    border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;
    font-size: 11px; margin-bottom: 15px;
}}
.custom-table thead th {{
    padding: 10px; text-align: left; background-color: {C_PRIMARY}; color: white !important;
    font-weight: 700; border: none; font-size: 11px;
}}
.custom-table td {{ padding: 8px 10px; border-bottom: 1px solid #f1f5f9; font-size: 11px; color: #334155; }}

/* Banner Header do Sistema */
.banner-imla {{
    width: 100%; height: 160px; border-radius: 16px; overflow:hidden; margin-bottom: 20px;
    background-image: linear-gradient(rgba(37,58,88,0.5), rgba(37,58,88,0.85));
    background-size: cover; background-position: center;
    display:flex; align-items:flex-end; padding: 20px 25px;
}}
.banner-imla h1 {{
    color:#ffffff !important; font-size: 26px; margin:0; font-weight:800 !important;
    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
}}
.banner-imla p {{
    color: #f1f5f9 !important; margin:0; font-size:12px; opacity:0.9;
    text-shadow: 0 1px 6px rgba(0,0,0,0.25);
}}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# --- SESSÃO E SEGURANÇA (AUTENTICAÇÃO) ---
# ==============================================================================
if "logado" not in st.session_state:
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None
if "modo_tela" not in st.session_state:
    st.session_state.modo_tela = "login"
if "nucleo_selecionado" not in st.session_state:
    st.session_state.nucleo_selecionado = "Comunicação"
if "idioma" not in st.session_state:
    st.session_state.idioma = "pt"
if "alunos_te_dict" not in st.session_state:
    st.session_state["alunos_te_dict"] = {}

for k in ["sel_mat", "sel_pad", "sel_aval", "sel_int", "sel_alf", "sel_ind", "sel_te"]:
    if k not in st.session_state:
        st.session_state[k] = "SALA ROSA"

# Tela de Autenticação Unificada
if not st.session_state.logado:
    login_bg = imagem_base64(LOGIN_BG_PATH)
    bg_css = f"url(data:image/jpeg;base64,{login_bg})" if login_bg else "none"

    st.markdown(f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(37,58,88,0.8), rgba(37,58,88,0.95)), {bg_css};
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        header {{visibility: hidden;}}
        p, label, h2, h4 {{ color: white !important; }}
        .login-card {{
            background: rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.15);
            margin-top: 50px;
        }}
        .login-logo {{ text-align: center; margin-bottom: 20px; }}
        </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.2, 1, 1.2])
    with c2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, use_container_width=True)
        else:
            st.markdown("<h2 style='text-align:center;'>🕊️ Instituto Mãe Lalu</h2>", unsafe_allow_html=True)

        if st.session_state.modo_tela == "login":
            st.markdown("<h4 style='text-align:center; font-size:15px; margin-bottom:20px;'>Acesso ao Portal Unificado</h4>", unsafe_allow_html=True)
            u = st.text_input("👤 E-mail ou Usuário:").strip()
            s = st.text_input("🔑 Senha ou Chave:", type="password")

            if st.button("Entrar", use_container_width=True):
                u_upper = u.upper()
                u_lower = u.lower()

                # 1. Perfil Admin (Coordenação)
                if u_upper == "ADMIN" and s == "123":
                    st.session_state.update({
                        "logado": True, "perfil": "admin", "nome_usuario": "COORDENAÇÃO",
                        "usuario_logado": {"nome": "Coordenação IMLA", "email": "admin@iml.org.br", "nucleo": "Pedagógico", "visitante": False}
                    })
                    st.rerun()

                # 2. Perfil Equipe / Núcleos (Intranet)
                elif u_lower in st.session_state.usuarios:
                    u_banco = st.session_state.usuarios[u_lower]
                    senha_ok = False
                    if "senha_hash" in u_banco:
                        senha_ok = verificar_senha(s, u_banco["salt"], u_banco["senha_hash"])
                    elif "senha" in u_banco:
                        senha_ok = (u_banco["senha"] == s)
                        if senha_ok:
                            salt, h = hash_senha(s)
                            u_banco["salt"], u_banco["senha_hash"] = salt, h
                            u_banco.pop("senha", None)
                            salvar_banco()
                    if senha_ok:
                        st.session_state.update({
                            "logado": True, "perfil": "staff", "nome_usuario": u_banco["nome"].upper(),
                            "usuario_logado": u_banco, "nucleo_selecionado": u_banco["nucleo"]
                        })
                        st.rerun()
                    else:
                        st.error("Chave de acesso incorreta.")

                # 3. Perfil Padrinho / Madrinha
                else:
                    encontrado = False
                    for sala in TURMAS_CONFIG.keys():
                        df_s = ler_planilha(sala)
                        if not df_s.empty and "PADRINHO/MADRINHA" in df_s.columns:
                            if u_upper in df_s["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper().unique():
                                encontrado = True
                                break
                    if encontrado:
                        st.session_state.update({
                            "logado": True, "perfil": "padrinho", "nome_usuario": u_upper,
                            "usuario_logado": {"nome": u_upper, "email": None, "nucleo": "Apadrinhamento", "visitante": False}
                        })
                        st.rerun()
                    else:
                        st.error("Credenciais não localizadas.")

            if st.button("Criar nova conta", use_container_width=True):
                st.session_state.modo_tela = "cadastro"
                st.rerun()

            st.markdown("<hr style='border-color:rgba(255,255,255,0.15); margin:15px 0;'>", unsafe_allow_html=True)
            if st.button("👁️ Entrar como visitante", use_container_width=True):
                st.session_state.update({
                    "logado": True, "perfil": "visitante", "nome_usuario": "VISITANTE",
                    "usuario_logado": {"nome": "Visitante", "email": None, "nucleo": None, "visitante": True},
                    "nucleo_selecionado": list(NUCLEOS_INFO.keys())[0]
                })
                st.rerun()

        # Fluxo de Cadastro de Equipe
        else:
            st.markdown("<h4 style='text-align:center; font-size:15px; margin-bottom:20px;'>Cadastro de Equipe</h4>", unsafe_allow_html=True)
            novo_nome = st.text_input("Nome completo:")
            novo_email = st.text_input("Seu melhor e-mail:")
            novo_nucleo = st.selectbox("Núcleo de atuação:", list(NUCLEOS_INFO.keys()))
            nova_senha = st.text_input("Senha de acesso:", type="password")
            confirmar_senha = st.text_input("Confirmar Senha:", type="password")

            if st.button("Finalizar Cadastro", use_container_width=True):
                chave = novo_email.strip().lower()
                if not (novo_nome.strip() and chave and nova_senha.strip() and confirmar_senha.strip()):
                    st.error("Preencha todos os campos obrigatórios.")
                elif nova_senha != confirmar_senha:
                    st.error("As senhas informadas divergem.")
                elif chave in st.session_state.usuarios:
                    st.warning("Este e-mail já possui cadastro cadastrado.")
                else:
                    salt, h = hash_senha(nova_senha)
                    st.session_state.usuarios[chave] = {
                        "nome": novo_nome.strip(), "email": chave, "nucleo": novo_nucleo,
                        "salt": salt, "senha_hash": h
                    }
                    salvar_banco()
                    st.success("Conta cadastrada com sucesso!")
                    st.session_state.modo_tela = "login"
                    st.rerun()

            if st.button("Voltar", use_container_width=True):
                st.session_state.modo_tela = "login"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# --- INTERFACE PRINCIPAL (SIDEBAR E NAVEGAÇÃO) ---
# ==============================================================================
# Injeção de Scripts de Segurança
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

# Barra Lateral Unificada (Sidebar)
st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 10px 0;">
        <h3 style="margin:0; color:{C_PRIMARY};">🕊️ INSTITUTO</h3>
        <p style="margin:0; font-size:10px; font-weight:800; color:{C_ACCENT}; letter-spacing:2px;">MÃE LALU</p>
    </div>
    <hr style="margin: 10px 0;">
""", unsafe_allow_html=True)

# Painel de Perfil no Sidebar
st.sidebar.markdown(f"""
    <div style="background-color: #f1f5f9; padding: 12px; border-radius: 10px; margin-bottom: 15px;">
        <span style="font-size: 10px; font-weight: 800; color: #64748b; text-transform: uppercase;">Usuário Conectado</span>
        <div style="font-size:13px; font-weight: 700; color: {C_PRIMARY};">{st.session_state.nome_usuario}</div>
        <div style="font-size:10px; color: #475569;">Nível: {st.session_state.perfil.upper()}</div>
    </div>
""", unsafe_allow_html=True)

# Definição Dinâmica de Menu por Permissão
role = st.session_state.perfil
opcoes_menu = []

if role == "admin":
    opcoes_menu = [
        "🏠 Intranet IMLA",
        "📝 Controle de Matrícula e Apadrinhamento",
        "📊 Dados - Turno Estendido",
        "📊 Avaliação da Tábua da Maré",
        "📖 Turno Estendido",
        "📈 Indicadores Pedagógicos",
        "🌊 Canal do Apadrinhamento",
        "🌊 Tábua da Maré"
    ]
elif role in ["staff", "visitante"]:
    opcoes_menu = ["🏠 Intranet IMLA"]
elif role == "padrinho":
    opcoes_menu = ["🌊 Canal do Apadrinhamento"]

menu_selecionado = st.sidebar.radio("Navegação", opcoes_menu)

# Seletor de Idioma para a Intranet
if "🏠 Intranet IMLA" in opcoes_menu:
    st.sidebar.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
    idioma_op = st.sidebar.selectbox("Idioma / Language", ["Português", "English"], index=0 if st.session_state.idioma == "pt" else 1)
    st.session_state.idioma = "pt" if idioma_op == "Português" else "en"

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": "", "usuario_logado": None})
    st.rerun()

# Banner Principal na Área do Sistema
banner_b64 = banner_base64(BANNER_PATH)
bg_banner_style = f"background-image: linear-gradient(rgba(37,58,88,0.5), rgba(37,58,88,0.85)), url(data:image/jpeg;base64,{banner_b64});" if banner_b64 else f"background: {C_PRIMARY};"

st.markdown(f"""
    <div class="banner-imla" style="{bg_banner_style}">
        <div>
            <h1>{t('titulo_sistema')}</h1>
            <p>{t('subtitulo')}</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# --- RENDERIZAÇÃO DAS PÁGINAS ---
# ==============================================================================

# --- MÓDULO 1: INTRANET IMLA ---
if menu_selecionado == "🏠 Intranet IMLA":
    usuario = st.session_state.usuario_logado
    n_sel = st.session_state.nucleo_selecionado
    eh_visitante = bool(usuario.get("visitante"))

    # Cabeçalho dos núcleos de trabalho (Navbar integrada por Streamlit)
    st.markdown("#### 🛠️ Núcleos de Atuação")
    cols_n = st.columns(len(NUCLEOS_INFO))
    for i, (nome, emoji) in enumerate(NUCLEOS_INFO.items()):
        tipo_b = "primary" if nome == n_sel else "secondary"
        if cols_n[i].button(f"{emoji} {nome}", key=f"btn_nav_nuc_{nome}", use_container_width=True):
            st.session_state.nucleo_selecionado = nome
            st.rerun()

    st.markdown(f"### {NUCLEOS_INFO.get(n_sel,'')} Área de Trabalho: {n_sel}")
    aba_feed, aba_tarefas, aba_lembretes, aba_solicitacoes = st.tabs([
        t("aba_novidades"), t("aba_tarefas"), t("aba_lembretes"), t("aba_solicitacoes")
    ])

    pode_editar = (not eh_visitante) and (usuario.get("nucleo") == n_sel or role == "admin")
    pode_ver_links = not eh_visitante

    # ABA NOVIDADES / FEED
    with aba_feed:
        if pode_editar:
            with st.form("form_novo_post"):
                texto = st.text_area(t("compartilhar") + ":")
                if st.form_submit_button(t("publicar")) and texto.strip():
                    agora = agora_br().strftime("%d/%m/%Y %H:%M")
                    st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {
                        "texto": texto, "data": agora, "autor_nome": usuario["nome"], "autor_email": usuario.get("email")
                    })
                    salvar_banco()
                    st.rerun()

        posts = st.session_state.nucleos_dados[n_sel]["atualizacoes"]
        if not posts:
            st.caption("Nenhum aviso ou novidade cadastrada neste núcleo.")
        else:
            col_c1, col_c2, col_c3 = st.columns(3)
            for idx, p in enumerate(posts):
                coluna = [col_c1, col_c2, col_c3][idx % 3]
                with coluna:
                    st.markdown(f"""
                    <div class='apple-card'>
                        <div class='card-tag'>Destaque</div>
                        <div class='card-title'>{p.get('autor_nome','—')}</div>
                        <div class='card-text'>{p['texto']}</div>
                        <div class='card-footer'>{p['data']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ABA TAREFAS / KANBAN
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
                with st.form("form_nova_tarefa_k", clear_on_submit=True):
                    novo_titulo = st.text_input(t("titulo_demanda"))
                    nova_desc = st.text_area(t("descricao_demanda"))
                    nova_prio = st.selectbox(t("prioridade"), PRIORIDADE_OPCOES, index=1)
                    if st.form_submit_button(t("adicionar_demanda")) and novo_titulo.strip():
                        agora = agora_br().strftime("%d/%m/%Y %H:%M")
                        st.session_state.nucleos_dados[n_sel]["tarefas"].append({
                            "id": str(uuid.uuid4())[:8], "titulo": novo_titulo.strip(), "descricao": nova_desc.strip(),
                            "status": "Criada", "prioridade": nova_prio, "autor_nome": usuario["nome"], "data_hora": agora
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
                            with st.form(f"editar_form_{tf['id']}"):
                                t_edit = st.text_input(t("titulo_demanda"), value=tf["titulo"])
                                d_edit = st.text_area(t("descricao_demanda"), value=tf.get("descricao", ""))
                                s_edit = st.selectbox(t("status"), STATUS_OPCOES, index=STATUS_OPCOES.index(tf.get("status", "Criada")))
                                p_edit = st.selectbox(t("prioridade"), PRIORIDADE_OPCOES, index=PRIORIDADE_OPCOES.index(tf.get("prioridade", "Média")))
                                col_s, col_e = st.columns(2)
                                if col_s.form_submit_button(t("salvar")):
                                    tf["titulo"] = t_edit.strip() or tf["titulo"]
                                    tf["descricao"] = d_edit.strip()
                                    tf["status"] = s_edit
                                    tf["prioridade"] = p_edit
                                    salvar_banco()
                                    st.rerun()
                                if col_e.form_submit_button(t("excluir_tarefa")):
                                    st.session_state.nucleos_dados[n_sel]["tarefas"] = [x for x in tarefas if x["id"] != tf["id"]]
                                    salvar_banco()
                                    st.rerun()

    # ABA AVISOS / RECORRENTES
    with aba_lembretes:
        if pode_editar:
            with st.expander(f"➕ {t('novo_lembrete')}"):
                with st.form("form_lembrete", clear_on_submit=True):
                    lem_t = st.text_input(t("titulo_lembrete"))
                    lem_d = st.text_area(t("descricao_lembrete"))
                    lem_dt = st.date_input(t("proxima_data"), value=agora_br().date())
                    if st.form_submit_button(t("adicionar_lembrete")) and lem_t.strip():
                        st.session_state.nucleos_dados[n_sel].setdefault("lembretes", []).append({
                            "id": str(uuid.uuid4())[:8], "titulo": lem_t.strip(), "descricao": lem_d.strip(),
                            "proxima_data": lem_dt.isoformat(), "autor_nome": usuario["nome"],
                            "data_criacao": agora_br().strftime("%d/%m/%Y %H:%M")
                        })
                        salvar_banco()
                        st.rerun()

        lembretes = st.session_state.nucleos_dados[n_sel].setdefault("lembretes", [])
        lembretes_ordenados = sorted(lembretes, key=lambda l: l.get("proxima_data", ""))

        if not lembretes_ordenados:
            st.caption(t("sem_lembretes"))
        else:
            hoje = agora_br().date()
            for lm in lembretes_ordenados:
                try:
                    data_lm = datetime.date.fromisoformat(lm.get("proxima_data", ""))
                    data_fmt = data_lm.strftime("%d/%m/%Y")
                    atrasado = data_lm < hoje
                except ValueError:
                    data_fmt = lm.get("proxima_data", "—")
                    atrasado = False

                desc_html = f"<div class='lembrete-desc'>{lm['descricao']}</div>" if lm.get("descricao") else ""
                classe_data = "lembrete-data atrasado" if atrasado else "lembrete-data"
                rotulo_data = f"⚠️ {data_fmt}" if atrasado else f"📅 {data_fmt}"

                st.markdown(f"""
                <div class="lembrete-card">
                    <div class="lembrete-titulo">{lm['titulo']}</div>
                    {desc_html}
                    <span class="{classe_data}">{rotulo_data}</span>
                    <div class="task-footer">{t('criado_por')} {lm.get('autor_nome','—')}</div>
                </div>
                """, unsafe_allow_html=True)

                if pode_editar:
                    with st.expander(t("editar"), expanded=False):
                        with st.form(f"edit_lembrete_{lm['id']}"):
                            lt_edit = st.text_input(t("titulo_lembrete"), value=lm["titulo"])
                            ld_edit = st.text_area(t("descricao_lembrete"), value=lm.get("descricao", ""))
                            try:
                                dt_atual = datetime.date.fromisoformat(lm.get("proxima_data", ""))
                            except ValueError:
                                dt_atual = agora_br().date()
                            ldt_edit = st.date_input(t("proxima_data"), value=dt_atual)
                            col_ls, col_le = st.columns(2)
                            if col_ls.form_submit_button(t("adicionar_lembrete")):
                                lm["titulo"] = lt_edit.strip() or lm["titulo"]
                                lm["descricao"] = ld_edit.strip()
                                lm["proxima_data"] = ldt_edit.isoformat()
                                salvar_banco()
                                st.rerun()
                            if col_le.form_submit_button(t("excluir_lembrete")):
                                st.session_state.nucleos_dados[n_sel]["lembretes"] = [x for x in lembretes if x["id"] != lm["id"]]
                                salvar_banco()
                                st.rerun()

    # ABA SOLICITAÇÕES / COMUNICAÇÃO INTERSETORIAL
    with aba_solicitacoes:
        if pode_editar:
            st.markdown(f"#### {t('enviar_solicitacao')}")
            with st.form("form_sol_inter", clear_on_submit=True):
                dest = st.selectbox(t("para_nucleo"), list(NUCLEOS_INFO.keys()))
                assunto = st.text_input(t("assunto") + ":")
                msg = st.text_area(t("mensagem") + ":")
                visib = st.radio(t("visibilidade"), [t("privada"), t("publica")], horizontal=True)
                if st.form_submit_button(t("enviar")) and assunto.strip():
                    agora = agora_br().strftime("%d/%m/%Y %H:%M")
                    st.session_state.caixa_entrada[dest].append({
                        "assunto": assunto, "mensagem": msg, "data": agora, "de_nome": usuario["nome"],
                        "de_nucleo": usuario["nucleo"], "publica": visib == t("publica")
                    })
                    salvar_banco()
                    st.success(t("enviado"))

            st.write(f"### {t('caixa_entrada')}")
            caixa = st.session_state.caixa_entrada[n_sel]
            if not caixa:
                st.caption("Caixa de entrada vazia.")
            else:
                for m in reversed(caixa):
                    selo = "🌐 " if m.get("publica") else "🔒 "
                    with st.expander(f"{selo}📩 {m['assunto']} ({t('de')}: {m.get('de_nome','—')} · {m.get('de_nucleo','')})"):
                        st.write(m['mensagem'])
                        st.caption(m['data'])
        else:
            st.caption(t("visitante_solicitacoes"))
            caixa_pub = [m for m in st.session_state.caixa_entrada[n_sel] if m.get("publica")]
            if not caixa_pub:
                st.caption("Sem solicitações públicas neste núcleo.")
            else:
                for m in reversed(caixa_pub):
                    with st.expander(f"🌐 📩 {m['assunto']} ({t('de')}: {m.get('de_nome','—')} · {m.get('de_nucleo','')})"):
                        st.write(m['mensagem'])
                        st.caption(m['data'])

# --- MÓDULO 2: MATRÍCULA E APADRINHAMENTO ---
elif menu_selecionado == "📝 Controle de Matrícula e Apadrinhamento":
    st.markdown("### 📝 Controle de Matrícula e Apadrinhamento")
    
    cor_rosa, cor_amarela, cor_verde, cor_azul = "#F783AC", "#FFE066", "#A9E34B", "#99E9F2"
    df_geral = df_g.copy()
    lista_alunos_geral = sorted(df_geral["ALUNO"].unique().tolist()) if not df_geral.empty else []

    df_te_check = df_alf.copy()
    set_matriculados_te = set(df_te_check["ALUNO"].unique().tolist()) if not df_te_check.empty else set()

    st.markdown(f"""
        <style>
        div[data-testid="stPopover"] > button {{
            background-color: white !important; border-radius: 8px; height: 3.2rem; transition: 0.3s;
        }}
        div[key="mat_popover"] > button {{ color: {cor_rosa} !important; border: 2px solid {cor_rosa} !important; }}
        div[key="pad_popover"] > button {{ color: {cor_amarela} !important; border: 2px solid {cor_amarela} !important; }}
        div[key="est_popover"] > button {{ color: {cor_verde} !important; border: 2px solid {cor_verde} !important; }}
        div[key="del_popover"] > button {{ color: {cor_azul} !important; border: 2px solid {cor_azul} !important; }}
        div[data-testid="stPopover"] button p {{ font-weight: 800 !important; }}
        </style>""", unsafe_allow_html=True)

    gestao_col1, gestao_col2, gestao_col3, gestao_col4 = st.columns([1, 2.2, 1.3, 0.9])

    with gestao_col1:
        with st.popover("➕ Matrícula", key="mat_popover", use_container_width=True):
            st.markdown("##### 📝 Nova Matrícula")
            n_nome = st.text_input("Nome do Aluno", key="reg_nome")
            n_sala = st.selectbox("Sala Destino", list(TURMAS_CONFIG.keys()), key="reg_sala")
            if st.button("Salvar Novo Aluno"):
                st.success("Aluno registrado!")

    with gestao_col2:
        with st.popover("🤝 Padrinho/Madrinha", key="pad_popover", use_container_width=True):
            st.markdown("##### 🤝 Novo Apadrinhamento")
            s_busca_p = st.selectbox("Selecione a Sala:", list(TURMAS_CONFIG.keys()), key="pad_sala_select")
            df_b = ler_planilha(s_busca_p)
            if "PADRINHO/MADRINHA" in df_b.columns:
                lista_lib = sorted(df_b[df_b["PADRINHO/MADRINHA"].astype(str).isin(["", "-", "nan", "0"])]["ALUNO"].unique())
                al_sel = st.selectbox("Escolha o Afilhado:", lista_lib)
                nome_p = st.text_input("Nome do Padrinho")
                if st.button("Confirmar Apadrinhamento"):
                    if nome_p.strip():
                        ok = atualizar_padrinho_sheets(s_busca_p, al_sel, nome_p.strip())
                        if ok:
                            st.success("Apadrinhamento registrado!")
                            st.rerun()
                    else:
                        st.warning("Informe o nome do padrinho/madrinha.")

    with gestao_col3:
        with st.popover("⏳ Turno Estendido", key="est_popover", use_container_width=True):
            st.markdown("##### ⏳ Matricular no Turno Estendido")
            lista_disponivel_te = [a for a in lista_alunos_geral if a not in set_matriculados_te]
            if lista_disponivel_te:
                al_mat = st.selectbox("Selecione o Aluno:", lista_disponivel_te, key="sel_aluno_matricula_te")
                if st.button("✅ Confirmar Matrícula", key="btn_confirmar_te"):
                    info_aluno = df_geral[df_geral["ALUNO"] == al_mat]
                    if not info_aluno.empty:
                        col_sala = "SALA" if "SALA" in df_geral.columns else "TURMA"
                        sala_origem = info_aluno[col_sala].values[0] if col_sala in info_aluno.columns else "NÃO DEFINIDA"
                        sucesso = registrar_matricula_te(aluno=al_mat, sala=sala_origem)
                        if sucesso:
                            st.success(f"✅ {al_mat} matriculado!")
                            st.rerun()
            else:
                st.info("Todos os alunos já estão matriculados no Turno Estendido.")

    with gestao_col4:
        with st.popover("🗑️ Remover", key="del_popover", use_container_width=True):
            st.radio("Remover:", ["Aluno", "Padrinho"])
            st.button("🚨 EXCLUIR")

    st.divider()

    render_botoes_salas("btn_pad", "sel_pad")
    sala_v = st.session_state.get("sel_pad", "SALA ROSA")
    cfg_sala = TURMAS_CONFIG.get(sala_v, {"cor": "#333", "icon": "🏫"})
    cor_h = cfg_sala["cor"]

    df_s = ler_planilha(sala_v)
    if not df_s.empty:
        tn, cm = render_filtros(df_geral, "pad")
        df_f = df_s.copy()
        if tn != "Todos" and "TURMA" in df_f.columns:
            df_f = df_f[df_f["TURMA"] == tn]
        if cm != "Todas" and "COMUNIDADE" in df_f.columns:
            df_f = df_f[df_f["COMUNIDADE"] == cm]

        st.markdown(f"""
            <div style="background-color:{cor_h}22;padding:10px;border-radius:5px;border-left:5px solid {cor_h};
                        margin:20px 0;display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:13px;color:#333;">{cfg_sala["icon"]} Atualmente: <b>{len(df_f)}</b> alunos na <b>{sala_v}</b></span>
                <span style="font-size:11px;background-color:{C_VERDE}44;padding:2px 8px;border-radius:10px;
                             border:1px solid {C_VERDE};color:#2b5e2b;"><b>📖</b> = Turno Estendido</span>
            </div>""", unsafe_allow_html=True)

        v_cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
        table_html = f'<table class="custom-table">'
        table_html += f'<thead style="background-color:{cor_h};"><tr>'
        for col in v_cols:
            table_html += f'<th>{col}</th>'
        table_html += "</tr></thead><tbody>"

        for i, (_, r) in enumerate(df_f.iterrows()):
            p_nome = str(r.get("PADRINHO/MADRINHA", "-")).strip()
            if p_nome in ["", "0", "nan", "None", "-"]:
                p_nome = "-"
            nome_aluno = r.get("ALUNO", "-")
            marcador_te = " <span title='Turno Estendido' style='color:#2b5e2b;'>📖</span>" if nome_aluno in set_matriculados_te else ""
            table_html += f'<tr>'
            table_html += f'<td style="font-weight:bold;">{nome_aluno}{marcador_te}</td>'
            table_html += f'<td style="text-align:center;">{r.get("TURMA","-")}</td>'
            table_html += f'<td style="text-align:center;">{r.get("IDADE","-")}</td>'
            table_html += f'<td>{r.get("COMUNIDADE","-")}</td>'
            table_html += f'<td style="font-weight:600; color:{C_PRIMARY};">{p_nome}</td>'
            table_html += "</tr>"

        st.markdown(table_html + "</tbody></table>", unsafe_allow_html=True)
    else:
        st.info(f"A {sala_v} ainda não possui alunos matriculados.")

# --- MÓDULO 3: DADOS TURNO ESTENDIDO ---
elif menu_selecionado == "📊 Dados - Turno Estendido":
    st.markdown("### 📋 Panorama de Avaliações - Turno Estendido")

    tem_pendentes = os.path.exists(ARQUIVO_BUFFER) and not pd.read_csv(ARQUIVO_BUFFER).empty if os.path.exists(ARQUIVO_BUFFER) else False

    if tem_pendentes:
        df_pendente = pd.read_csv(ARQUIVO_BUFFER)
        qtd = len(df_pendente)
        col_sync1, col_sync2, col_sync3 = st.columns([1.5, 1, 3])
        col_sync1.warning(f"⏳ **{qtd} registro(s) locais pendentes de envio**")
        if col_sync2.button("📤 Enviar para Google Sheets", type="primary", use_container_width=True):
            with st.spinner("Sincronizando avaliações e evidências..."):
                enviar_buffer_para_sheets()
        if col_sync3.button("🗑️ Descartar registros locais", use_container_width=True):
            os.remove(ARQUIVO_BUFFER)
            st.rerun()
    else:
        st.success("✅ Sincronização em conformidade com o Google Sheets.")

    st.divider()

    if "ano_ativo_te" not in st.session_state:
        st.session_state.ano_ativo_te = 2025

    col_anos = st.columns([0.15, 0.15, 0.7])
    anos = [2025, 2026]
    cores_ano = {2025: C_PRIMARY, 2026: C_ACCENT}

    for i, ano in enumerate(anos):
        is_active = st.session_state.ano_ativo_te == ano
        cor_btn = cores_ano[ano] if is_active else "#cbd5e1"
        txt_cor = "white" if is_active else "#475569"
        if col_anos[i].button(f"📅 {ano}", key=f"btn_ano_{ano}", use_container_width=True):
            st.session_state.ano_ativo_te = ano
            st.rerun()

    ano_sel = st.session_state.ano_ativo_te
    st.markdown(f"**Exibindo dados do Ano Letivo: {ano_sel}**")
    render_legenda_niveis()

    df_h = carregar_turno_estendido_completo()

    def get_status_mare_html(nv_atual, hist):
        n_at = MAPA_NIVEIS.get(nv_atual, 0)
        if n_at == 0:
            return '<span class="mare-texto-tabela">—</span>'
        fill_pct = max(6, round(n_at * 90 / 7))
        if n_at <= 2: txt = "maré baixa"
        elif n_at == 7: txt = "maré cheia"
        else:
            n_ant = MAPA_NIVEIS.get(hist[-2], 0) if len(hist) >= 2 else 0
            if n_ant != 0 and n_at > n_ant: txt = "maré enchente"
            elif n_ant != 0 and n_at < n_ant: txt = "maré vazante"
            else:
                if n_at in [3, 4]: txt = "maré enchente"
                elif n_at in [5, 6]: txt = "maré alta"
                else: txt = "maré estável"
        return f'<div class="mare-box"><span class="mare-texto-tabela" style="font-weight:800; color:{C_PRIMARY};">{txt.upper()}</span></div>'

    cols_header = ["Nome do Aluno", "1ª AVALIAÇÃO", "2ª AVALIAÇÃO", "AVALIAÇÃO FINAL", "STATUS MARÉ"]
    if ano_sel == 2026:
        cols_header.insert(1, "Diagnóstico Anterior")

    html_tab = (
        f'<table class="custom-table">'
        f'<thead><tr>'
        + "".join([f'<th>{c}</th>' for c in cols_header])
        + "</tr></thead><tbody>"
    )

    alunos_nesta_aba = sorted([
        a for a in df_h["ALUNO"].astype(str).str.strip().unique()
        if a and a not in ["nan", "None", ""]
    ]) if not df_h.empty else []

    for al in alunos_nesta_aba:
        dados_aluno_ano = df_h[
            (df_h["ALUNO"].astype(str).str.strip() == al) &
            (df_h["ANO"].astype(str).str.strip() == str(ano_sel))
        ]
        if dados_aluno_ano.empty:
            continue

        sala_al_raw = str(dados_aluno_ano["SALA"].iloc[0]).strip().upper() if "SALA" in dados_aluno_ano.columns else ""
        sala_al = sala_al_raw
        if sala_al not in TURMAS_CONFIG:
            for k in TURMAS_CONFIG:
                if k in sala_al or sala_al in k:
                    sala_al = k
                    break
        cfg_sala  = TURMAS_CONFIG.get(sala_al, {})
        cor_badge = cfg_sala.get("cor", "#aaa")
        txt_badge = BADGE_LABEL.get(sala_al, sala_al_raw.replace("SALA ", "") if sala_al_raw else "—")
        badge_sala = (
            f' <span style="background:{cor_badge};color:#fff;border-radius:50px;'
            f'padding:3px 10px;font-size:9px;font-weight:800;white-space:nowrap;">'
            f'{txt_badge}</span>'
        )

        html_tab += f'<tr><td style="font-weight:bold;">{al}{badge_sala}</td>'

        if ano_sel == 2026:
            dados_2025 = df_h[
                (df_h["ALUNO"].astype(str).str.strip() == al) &
                (df_h["ANO"].astype(str).str.strip() == "2025")
            ]
            diag_2025 = ""
            if not dados_2025.empty:
                for c_av in ["AVALIAÇÃO FINAL", "2ª AVALIAÇÃO", "1ª AVALIAÇÃO", "DIAGNÓSTICO"]:
                    if c_av in dados_2025.columns:
                        val = str(dados_2025[c_av].iloc[0]).strip()
                        if val and val not in ["nan", "None", ""]:
                            diag_2025 = val
                            break
            if not diag_2025 or diag_2025 in ["nan", "None", ""]:
                diag_2025 = "-"
            if diag_2025 != "-":
                cor_d  = CORES_EXCLUSIVAS.get(diag_2025, "#eee")
                txt_d  = diag_2025.split(". ")[1] if ". " in diag_2025 else diag_2025
                html_tab += f'<td style="background:{cor_d}; text-align:center;font-weight:bold;">{txt_d}</td>'
            else:
                html_tab += '<td style="text-align:center;color:#aaa;">—</td>'

        for col_av in ["1ª AVALIAÇÃO", "2ª AVALIAÇÃO", "AVALIAÇÃO FINAL"]:
            nv = dados_aluno_ano[col_av].iloc[0] if col_av in dados_aluno_ano.columns else ""
            nv = str(nv).strip() if nv else ""
            if nv:
                cor    = CORES_EXCLUSIVAS.get(nv, "#eee")
                txt_nv = nv.split(". ")[1] if ". " in nv else nv
                html_tab += f'<td style="background:{cor}; text-align:center; font-weight:bold;">{txt_nv}</td>'
            else:
                html_tab += '<td></td>'

        niveis_preenchidos = [
            str(dados_aluno_ano[c].iloc[0]).strip()
            for c in ["1ª AVALIAÇÃO", "2ª AVALIAÇÃO", "AVALIAÇÃO FINAL"]
            if c in dados_aluno_ano.columns and str(dados_aluno_ano[c].iloc[0]).strip()
        ]
        status_html = '<td style="text-align:center;">-</td>'
        if niveis_preenchidos:
            status_html = f'<td>{get_status_mare_html(niveis_preenchidos[-1], niveis_preenchidos)}</td>'

        html_tab += status_html + "</tr>"

    st.markdown(html_tab + "</tbody></table>", unsafe_allow_html=True)

# --- MÓDULO 4: LANÇAMENTO DE AVALIAÇÃO (TÁBUA DA MARÉ) ---
elif menu_selecionado == "📊 Avaliação da Tábua da Maré":
    st.markdown(f"### 📊 Lançar Avaliação na Tábua da Maré")
    st.info("ℹ️ Os lançamentos são salvos localmente e consolidados no Google Sheets no canal de visualização da Tábua da Maré.")

    df_av = obter_tabua_mare_para_visualizacao()

    render_botoes_salas("btn_aval", "sel_aval")
    sala_atual = st.session_state.sel_aval

    dict_te = st.session_state.get("alunos_te_dict", {})
    alunos_na_sala = [n for n, s in dict_te.items() if str(s).strip().upper() == str(sala_atual).strip().upper()]

    if not alunos_na_sala:
        df_sala = ler_planilha(sala_atual)
        if not df_sala.empty and "ALUNO" in df_sala.columns:
            alunos_na_sala = sorted(df_sala["ALUNO"].unique().tolist())

    if alunos_na_sala:
        al = st.selectbox("Selecione o Aluno para Lançamento", sorted(alunos_na_sala))
        col_busca_aluno = "ALUNO" if "ALUNO" in df_av.columns else df_av.columns[0]
        historico_aluno = df_av[df_av[col_busca_aluno].apply(normalizar_texto) == normalizar_texto(al)]
        dados_anteriores = historico_aluno.iloc[-1] if not historico_aluno.empty else None

        st.markdown("#### ⭐ Lançamento de Critérios de Desenvolvimento")

        with st.form("f_av_nuvem"):
            tr = st.selectbox("Período Letivo", ["1º Semestre", "2º Semestre"])
            cE, cD = st.columns(2)
            n_l = {}

            for i, cat in enumerate(CATEGORIAS):
                val_anterior = "Maré Enchente"
                if dados_anteriores is not None:
                    for col_av in dados_anteriores.index:
                        if col_av.strip().lower() == cat.strip().lower():
                            val_anterior = dados_anteriores[col_av]
                            break
                try:
                    idx_default = int(val_anterior) - 1 if str(val_anterior).isdigit() else OPCOES_MARE.index(val_anterior)
                except Exception:
                    idx_default = 2
                n_l[cat] = (cE if i < 5 else cD).selectbox(cat, OPCOES_MARE, index=idx_default, key=f"mare_s_{i}")

            obs_anterior = ""
            if dados_anteriores is not None:
                for col_av in dados_anteriores.index:
                    if "OBSERV" in col_av.upper():
                        obs_anterior = dados_anteriores[col_av]
                        break
            obs = st.text_area("Observações de Acompanhamento Pedagógico:", value=obs_anterior)

            if st.form_submit_button("💾 Salvar na Tábua da Maré"):
                if al:
                    sucesso = registrar_tabua_mare(aluno=al, sala=sala_atual, semestre=tr, notas_dict=n_l, obs=obs)
                    if sucesso:
                        st.balloons()
                        st.success(f"Avaliação de {al} registrada localmente com sucesso!")
                        st.rerun()
                else:
                    st.error("Por favor, selecione um aluno válido.")
    else:
        st.warning(f"Sem registros de alunos cadastrados na {sala_atual}.")

# --- MÓDULO 5: TURNO ESTENDIDO ---
elif menu_selecionado == "📖 Turno Estendido":
    st.markdown(f"### 📖 Planejamento de Níveis - Turno Estendido")
    st.info("ℹ️ Os registros de progressão aqui efetuados são gravados temporariamente. Sincronize em 'Dados - Turno Estendido'.")

    df_logica = df_alf.copy()
    col_diag  = next((c for c in ["NIVEL", "DIAGNÓSTICO", "NÍVEL", "DIAGNOSTICO"] if c in df_logica.columns), None)
    col_aluno = "ALUNO" if "ALUNO" in df_logica.columns else None
    col_sala  = "SALA" if "SALA" in df_logica.columns else None

    if not df_logica.empty and col_aluno and col_sala:
        dict_alunos_geral = {
            str(row[col_aluno]).strip(): str(row[col_sala]).strip().upper()
            for _, row in df_logica.iterrows() if str(row[col_aluno]).strip()
        }
        st.session_state["alunos_te_dict"] = dict_alunos_geral
    else:
        dict_alunos_geral = {}

    if os.path.exists(ARQUIVO_BUFFER):
        df_buf = pd.read_csv(ARQUIVO_BUFFER)
        for _, row in df_buf.iterrows():
            nome = str(row.get("ALUNO", "")).strip()
            sala = str(row.get("SALA", "")).strip().upper()
            if nome and nome not in dict_alunos_geral:
                dict_alunos_geral[nome] = sala

    st.write("#### 🔍 Seleção de Aluno")
    lista_nomes_completa = sorted(list(dict_alunos_geral.keys()))
    busca_nome = st.text_input("Filtrar nome de aluno:", placeholder="Escreva para buscar...").strip().upper()
    lista_filtrada = [n for n in lista_nomes_completa if busca_nome in n.upper()] if busca_nome else lista_nomes_completa

    if lista_filtrada:
        aluno_sel = st.selectbox("Selecione o Aluno para Diagnóstico:", lista_filtrada)
        sala_raw = dict_alunos_geral.get(aluno_sel, "NÃO DEFINIDA")
        cor_pilula = C_PRIMARY

        st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;background:#f8fafc;
                        padding:10px;border-radius:12px;border-left:5px solid {cor_pilula}; border:1px solid #e2e8f0;">
                <span style="font-weight:bold;font-size:13px;color:#475569;">Sala Referência:</span>
                <span style="background-color:{C_PRIMARY};color:white;padding:4px 12px;border-radius:50px;
                             font-weight:800;font-size:11px;">{sala_raw}</span>
            </div>""", unsafe_allow_html=True)

        ultimo_nv = obter_ultimo_diagnostico(aluno_sel, df_logica, col_aluno, col_diag)
        st.markdown(f"Diagnóstico mais recente: <span class='sala-badge' style='background:{C_PRIMARY}'>{ultimo_nv}</span>", unsafe_allow_html=True)

        if f"nivel_diag_te_{aluno_sel}" not in st.session_state:
            if ultimo_nv in NIVEIS_ALF:
                st.session_state[f"nivel_diag_te_{aluno_sel}"] = ultimo_nv

        novo_nv = render_legenda_niveis_botoes(aluno_sel, key_prefix="te")
        if not novo_nv:
            novo_nv = ultimo_nv if ultimo_nv in NIVEIS_ALF else NIVEIS_ALF[0]

        st.write("#### 📝 Evidências de Aprendizagem")
        with st.form("form_te_unificado"):
            ano_form = st.selectbox("Ano de Avaliação:", [2026, 2025])
            etapa_av = st.selectbox("Etapa Corrente:", ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"])
            st.divider()
            evs = EVIDENCIAS_POR_NIVEL.get(novo_nv, [])
            st.write(f"**Competências observadas para o estágio {novo_nv}:**")
            cols_ev = st.columns(3)
            selecionadas = [ev for i, ev in enumerate(evs) if cols_ev[i % 3].checkbox(ev, key=f"ev_final_te_{i}")]
            obs_txt = st.text_area("Observações de evolução clínica:")

            if st.form_submit_button("💾 Gravar Progressão Localmente"):
                ok = salvar_buffer_local(
                    aluno=aluno_sel, sala=sala_raw, avaliacao_tipo=etapa_av,
                    nivel=novo_nv, evidencias_list=selecionadas, obs=obs_txt, ano=int(ano_form)
                )
                if ok:
                    st.success(f"✅ Registros gravados com sucesso! Sincronize em 'Dados - Turno Estendido'.")
                    st.rerun()
    else:
        st.warning("Não há correspondências de busca para o termo informado.")

# --- MÓDULO 6: INDICADORES PEDAGÓGICOS ---
elif menu_selecionado == "📈 Indicadores Pedagógicos":
    st.markdown("### 📈 Painel Geral de Indicadores")
    render_botoes_salas("btn_ind", "sel_ind")
    df_h = df_alf.copy()
    if not df_h.empty:
        df_ult = df_h.sort_values("AVALIAÇÃO").groupby("ALUNO").last().reset_index() if "AVALIAÇÃO" in df_h.columns else df_h
        st.dataframe(df_ult, use_container_width=True)
    else:
        st.info("Sem base consolidada de histórico para plotagem de indicadores.")

# --- MÓDULO 7: CANAL DO APADRINHAMENTO ---
elif menu_selecionado == "🌊 Canal do Apadrinhamento":
    st.markdown("### 🤝 Acompanhamento do Apadrinhamento")

    lista_salas = []
    for nome_aba in TURMAS_CONFIG.keys():
        df_t = ler_planilha(nome_aba)
        if not df_t.empty:
            df_t = df_t.copy()
            df_t["SALA_NOME"] = nome_aba
            lista_salas.append(df_t)

    if not lista_salas:
        st.error("⚠️ Falha de comunicação com a base de dados GSheets.")
        st.stop()

    df_total = pd.concat(lista_salas, ignore_index=True)
    col_padrinho = "PADRINHO/MADRINHA"
    padrinhos_lista = (
        sorted([str(p).strip() for p in df_total[col_padrinho].unique()
                if str(p).strip() not in ["", "0", "nan", "None", "NaN"]])
        if col_padrinho in df_total.columns else []
    )

    if st.session_state.perfil == "padrinho":
        p_sel = st.session_state.nome_usuario
    else:
        p_sel = st.selectbox("👤 Filtrar por Padrinho/Madrinha (Acesso Admin):", ["Selecione..."] + padrinhos_lista)

    if p_sel and p_sel not in ["Selecione...", "Nenhum Padrinho Encontrado"]:
        afils_df = df_total[df_total[col_padrinho].astype(str).str.upper() == p_sel.upper()]

        if not afils_df.empty:
            lista_nomes = sorted([str(n).strip() for n in afils_df["ALUNO"].unique()])
            al_af = st.selectbox("👶 Selecione o afilhado para análise:", lista_nomes)

            is_turno = al_af in st.session_state.get("alunos_te_dict", {}) or not obter_historico_te_aluno(al_af).empty
            modo = "🌊 Tábua da Maré (Geral)"

            if is_turno:
                st.markdown(f"""
                <div style="background-color:#f8fafc;padding:20px;border-radius:12px;border-left:5px solid {C_PRIMARY};margin-bottom:20px; border:1px solid #e2e8f0;">
                    <span style="font-size:15px; font-weight:700; color:{C_PRIMARY};">✨ O seu afilhado, {al_af}, participa do nosso Turno Estendido!</span><br>
                    <p style="margin-top:10px;line-height:1.5;font-size:12px;">
                        Essa é uma ação complementar ao nosso projeto principal de alfabetização de forma integrada.
                    </p>
                </div>""", unsafe_allow_html=True)
                modo = st.radio("Selecione o plano de visualização:", ["🌊 Tábua da Maré (Geral)", "📚 Turno Estendido"], horizontal=True)

            st.markdown("---")

            if modo == "🌊 Tábua da Maré (Geral)":
                df_av_canal = obter_tabua_mare_para_visualizacao()
                dados_aluno_mare = df_av_canal[df_av_canal["ALUNO"].astype(str).str.strip() == al_af.strip()]
                if not dados_aluno_mare.empty:
                    dados_aluno_mare = dados_aluno_mare[dados_aluno_mare.apply(linha_tem_avaliacao_tabua, axis=1)]

                aluno_cad = afils_df[afils_df["ALUNO"].astype(str).str.strip() == al_af.strip()].iloc[0]
                sala_cad = aluno_cad.get("SALA_NOME", aluno_cad.get("SALA", ""))
                obs_mare_lista = []
                if not dados_aluno_mare.empty:
                    for _, row_obs in dados_aluno_mare.iterrows():
                        obs_val = str(row_obs.get("OBSERVAÇÕES PEDAGÓGICAS", row_obs.get("OBSERVACOES", ""))).strip()
                        if obs_val and obs_val not in ["nan", "None"] and obs_val not in obs_mare_lista:
                            obs_mare_lista.append(obs_val)
                obs_mare_ficha = "<br>".join(obs_mare_lista) if obs_mare_lista else "Sem observações registradas."

                st.markdown(f"""
                <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:18px;margin-bottom:18px;box-shadow:0 1px 3px rgba(0,0,0,0.02);">
                    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
                        <h4 style="margin:0; font-size:14px;">{al_af}</h4>
                        {render_badge_sala_html(sala_cad)}
                    </div>
                    <p style="margin:4px 0;font-size:12px;"><b>Idade:</b> {aluno_cad.get("IDADE", "---")}</p>
                    <p style="margin:4px 0;font-size:12px;"><b>Comunidade:</b> {aluno_cad.get("COMUNIDADE", "---")}</p>
                    <div style="margin-top:12px;background:#f8fafc;border-left:4px solid {C_ACCENT};padding:10px;border-radius:8px; border:1px solid #e2e8f0;">
                        <b>Histórico de Observações na Tábua da Maré:</b><br><span style="font-size:11.5px; color:#475569;">{obs_mare_ficha}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if not dados_aluno_mare.empty:
                    for _, r in dados_aluno_mare.iterrows():
                        periodo = r.get("SEMESTRE", r.get("PERIODO", "Avaliação"))
                        st.markdown(f"**🗓️ {periodo}**")
                        valores = []
                        mapa_notas = {
                            "MARÉ BAIXA": 1, "MARÉ VAZANTE": 2, "MARÉ ENCHENTE": 3, "MARÉ ALTA": 4, "MARÉ CHEIA": 5,
                        }
                        for cat in CATEGORIAS:
                            v = r.get(cat.upper(), r.get(cat, 1))
                            if isinstance(v, str):
                                n = mapa_notas.get(v.strip().upper(), 1)
                            else:
                                n = v if v else 1
                            valores.append(float(n))

                        c1 = st.columns(5)
                        for i in range(5):
                            with c1[i]: st.markdown(render_vasilha_mare(valores[i], CATEGORIAS[i]), unsafe_allow_html=True)
                        c2 = st.columns(5)
                        for i in range(5, 10):
                            with c2[i - 5]: st.markdown(render_vasilha_mare(valores[i], CATEGORIAS[i]), unsafe_allow_html=True)

                        obs_pedag = r.get("OBSERVAÇÕES PEDAGÓGICAS", r.get("OBSERVACOES", "Sem registro."))
                        st.info(f"**Anotação Pedagógica:** {obs_pedag}")
                else:
                    st.info("Sem registro de avaliação disponível para este semestre.")

            elif modo == "📚 Turno Estendido":
                dados_al = obter_historico_te_aluno(al_af)
                if not dados_al.empty:
                    aluno_cad = afils_df[afils_df["ALUNO"].astype(str).str.strip() == al_af.strip()].iloc[0]
                    u_nv, evidencias, observacoes, niveis_seq, avaliacoes_por_ano = extrair_resumo_te(dados_al)
                    info_al = dados_al.iloc[-1]
                    sala_te = info_al.get("SALA", aluno_cad.get("SALA_NOME", ""))
                    hist_status = niveis_seq if niveis_seq else ([u_nv] if u_nv in MAPA_NIVEIS else [])

                    col_info, col_status = st.columns([1.35, 0.85])
                    with col_info:
                        cor_bg = CORES_EXCLUSIVAS.get(u_nv, "#ddd")
                        st.markdown(f"""
                        <div style="background:#ffffff;border:1px solid #e2e8f0;padding:18px;border-radius:14px;box-shadow:0 1px 3px rgba(0,0,0,0.02);">
                            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
                                <h4 style="margin:0; font-size:14px;">{al_af}</h4>
                                {render_badge_sala_html(sala_te)}
                            </div>
                            <p style="margin:4px 0;font-size:12px;"><b>Idade:</b> {aluno_cad.get("IDADE", "---")}</p>
                            <p style="margin:4px 0;font-size:12px;"><b>Comunidade:</b> {aluno_cad.get("COMUNIDADE", "---")}</p>
                            <p style="margin:10px 0;font-size:12.5px;"><b>Último diagnóstico:</b> <span style="background:{cor_bg};color:{get_text_color(u_nv)};padding:4px 10px;border-radius:15px;font-weight:800;">{u_nv}</span></p>
                            <p style="font-size:11.5px;margin:8px 0; color:#475569;"><b>Evidências:</b> {evidencias}</p>
                            <p style="font-size:11.5px;margin:8px 0; color:#475569;"><b>Observações pedagógicas:</b> {observacoes}</p>
                        </div>""", unsafe_allow_html=True)

                    with col_status:
                        st.markdown(render_status_mare_te_html(u_nv, hist_status), unsafe_allow_html=True)

                    st.markdown("##### 🚀 Trilha de desenvolvimento")
                    render_legenda_niveis()
                    st.markdown(render_trilha_desenvolvimento_html(avaliacoes_por_ano), unsafe_allow_html=True)
                else:
                    st.warning("Sem dados cadastrados de turno estendido para este afilhado.")

# --- MÓDULO 8: TÁBUA DA MARÉ (VISUALIZADOR GERAL) ---
elif menu_selecionado == "🌊 Tábua da Maré":
    st.markdown(f"### 🌊 Painel Geral - Tábua da Maré")

    df_pendentes_mare = carregar_tabua_mare_local()
    if not df_pendentes_mare.empty:
        st.warning(f"Existem {len(df_pendentes_mare)} lançamentos pendentes de confirmação de envio para o Google Sheets.")
        if st.button("✅ Confirmar envio pendente de dados"):
            enviar_tabua_mare_local_para_sheets()

    render_botoes_salas("btn_int", "sel_int")
    df_av = obter_tabua_mare_para_visualizacao()
    df_s = ler_planilha(st.session_state.sel_int)

    if not df_s.empty:
        alunos_sala = sorted([str(n).replace("**", "").strip() for n in df_s["ALUNO"].dropna().unique()])
        cor_sala_exp = TURMAS_CONFIG.get(st.session_state.sel_int, {}).get("cor", "#5cc6d0")

        st.markdown(f"""<style>
        [data-testid="stExpander"] {{
            border: 1px solid {cor_sala_exp}33 !important;
            border-radius: 10px !important; margin-bottom: 8px !important;
        }}
        [data-testid="stExpander"] details summary {{
            background: {cor_sala_exp}0c !important; border-radius: 10px !important;
        }}
        </style>""", unsafe_allow_html=True)

        for al in alunos_sala:
            with st.expander(f"👤 {al}"):
                filtro_aluno = df_s[df_s["ALUNO"].str.strip() == al.strip()]
                if filtro_aluno.empty:
                    st.warning("Sem dados cadastrais localizados.")
                    continue

                aluno_row = filtro_aluno.iloc[0]
                turno = aluno_row.get("TURMA", "")
                sala_nome = st.session_state.sel_int.replace("SALA ", "").title()
                sala_full = f"{sala_nome} - {turno}" if turno else sala_nome

                col_f1, col_f2 = st.columns([1, 2])
                with col_f1:
                    st.markdown(f"""
                        <div style="background-color:#f8fafc;padding:12px;border-radius:10px;border:1px solid #e2e8f0;color:black;">
                            <p style="margin:0;font-size:11.5px;"><b>SALA/TURMA:</b> {sala_full}</p>
                            <p style="margin:5px 0 0;font-size:11.5px;"><b>IDADE:</b> {aluno_row.get("IDADE","---")}</p>
                            <p style="margin:5px 0 0;font-size:11.5px;"><b>COMUNIDADE:</b> {aluno_row.get("COMUNIDADE","---")}</p>
                        </div>""", unsafe_allow_html=True)

                dados_aluno = df_av[df_av["ALUNO"].str.strip() == al.strip()]
                if not dados_aluno.empty:
                    dados_aluno = dados_aluno[dados_aluno.apply(linha_tem_avaliacao_tabua, axis=1)]

                if not dados_aluno.empty:
                    for _, r in dados_aluno.iterrows():
                        periodo = r.get("SEMESTRE", r.get("PERIODO", "Avaliação"))
                        st.write("---")
                        st.markdown(f"**🗓️ {periodo}**")
                        if str(r.get("STATUS_ENVIO", "")).strip().upper() == "PENDENTE":
                            st.caption("Aguardando confirmação de upload")
                        valores = []
                        mapa_notas = {
                            "MARÉ BAIXA": 1, "MARÉ VAZANTE": 2, "MARÉ ENCHENTE": 3, "MARÉ ALTA": 4, "MARÉ CHEIA": 5,
                        }
                        for cat in CATEGORIAS:
                            v = r.get(cat.upper(), r.get(cat, 1))
                            if isinstance(v, str):
                                n = mapa_notas.get(v.strip().upper(), 1)
                            else:
                                n = v if v else 1
                            valores.append(float(n))

                        c1 = st.columns(5)
                        for i in range(5):
                            with c1[i]: st.markdown(render_vasilha_mare(valores[i], CATEGORIAS[i]), unsafe_allow_html=True)
                        c2 = st.columns(5)
                        for i in range(5, 10):
                            with c2[i - 5]: st.markdown(render_vasilha_mare(valores[i], CATEGORIAS[i]), unsafe_allow_html=True)

                        obs_pedag = r.get("OBSERVAÇÕES PEDAGÓGICAS", r.get("OBSERVACOES", "Sem registro."))
                        st.info(f"**Anotação Pedagógica:** {obs_pedag}")
                else:
                    st.info("Nenhuma avaliação cadastrada.")
    else:
        st.warning("A sala selecionada está temporariamente sem registros ou dados associados.")
```
