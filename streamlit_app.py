import streamlit as st
import datetime
import os
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

if "dados_carregados" not in st.session_state:
    dados = carregar_banco()
    st.session_state.usuarios = dados["usuarios"]
    st.session_state.nucleos_dados = dados["nucleos_dados"]
    st.session_state.caixa_entrada = dados["caixa_entrada"]
    st.session_state.dados_carregados = True

if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "modo_tela" not in st.session_state: st.session_state.modo_tela = "login"
if "nucleo_selecionado" not in st.session_state: st.session_state.nucleo_selecionado = "Comunicação"

# 3. ESTILOS E FUNÇÕES DE UI
def aplicar_css():
    st.markdown("""
        <style>
        .stApp { background: #fafafa !important; }
        .banner-img { width: 100%; border-radius: 20px; margin-bottom: 20px; }
        .node-circle { width: 50px; height: 50px; border-radius: 50%; background: #e0e0e0; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 20px;}
        .apple-card { background: #ffffff; border-radius: 20px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .trello-col { background: #f0f2f6; padding: 15px; border-radius: 10px; min-height: 300px; }
        .stButton>button { border-radius: 8px; width: 100%; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# ÁREA PÚBLICA (LOGIN/CADASTRO)
# ==========================================
if st.session_state.usuario_logado is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.modo_tela == "login":
            st.title("Acesso Sistema IMLA")
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                if email in st.session_state.usuarios and st.session_state.usuarios[email]["senha"] == senha:
                    st.session_state.usuario_logado = st.session_state.usuarios[email]
                    st.rerun()
                else: st.error("Credenciais inválidas.")
            if st.button("Criar Conta"):
                st.session_state.modo_tela = "cadastro"
                st.rerun()
        else:
            st.title("Cadastro")
            nome = st.text_input("Nome Completo")
            email = st.text_input("Email")
            nucleo = st.selectbox("Núcleo", list(st.session_state.nucleos_dados.keys()))
            senha = st.text_input("Senha", type="password")
            if st.button("Finalizar"):
                st.session_state.usuarios[email] = {"nome": nome, "email": email, "nucleo": nucleo, "senha": senha}
                salvar_banco()
                st.session_state.modo_tela = "login"
                st.rerun()

# ==========================================
# ÁREA PRIVADA (SISTEMA IMLA)
# ==========================================
else:
    aplicar_css()
    
    # BANNER
    if os.path.exists("IMG_3985.jpg"):
        st.image("IMG_3985.jpg", use_container_width=True)
    
    st.title("Sistema IMLA")
    
    # ORGANOGRAMA (Interativo)
    st.markdown("### Organograma")
    cols = st.columns(6)
    nucleos = list(st.session_state.nucleos_dados.keys())
    for i, n in enumerate(nucleos):
        with cols[i]:
            if st.button(f"{n[:10]}...", key=f"btn_{n}"): st.session_state.nucleo_selecionado = n
    
    st.divider()
    n_sel = st.session_state.nucleo_selecionado
    st.subheader(f"Núcleo: {n_sel}")

    aba_feed, aba_tarefas, aba_solicitacoes = st.tabs(["Novidades", "Demandas", "Solicitações"])

    # ABA FEED
    with aba_feed:
        if st.session_state.usuario_logado['nucleo'] == n_sel:
            texto = st.text_area("O que está acontecendo?")
            if st.button("Publicar") and texto:
                st.session_state.nucleos_dados[n_sel]["atualizacoes"].insert(0, {
                    "texto": texto, "autor": st.session_state.usuario_logado['nome'], "data": datetime.datetime.now().strftime("%d/%m")
                })
                salvar_banco()
                st.rerun()
        
        for p in st.session_state.nucleos_dados[n_sel]["atualizacoes"]:
            st.markdown(f"<div class='apple-card'><b>{p['autor']}</b>: {p['texto']} <br><small>{p['data']}</small></div>", unsafe_allow_html=True)

    # ABA TAREFAS (TRELLO STYLE)
    with aba_tarefas:
        if st.session_state.usuario_logado['nucleo'] == n_sel:
            nova_t = st.text_input("Nova demanda:")
            if st.button("Adicionar"):
                st.session_state.nucleos_dados[n_sel]["tarefas"].append({
                    "id": len(st.session_state.nucleos_dados[n_sel]["tarefas"]),
                    "titulo": nova_t, "status": "criado", "criador": st.session_state.usuario_logado['nome']
                })
                salvar_banco()
                st.rerun()

        cols_t = st.columns(3)
        status_ordem = [("criado", "A Fazer", cols_t[0]), ("fazendo", "Fazendo", cols_t[1]), ("feito", "Feito", cols_t[2])]
        
        for s_val, s_label, col in status_ordem:
            with col:
                st.markdown(f"#### {s_label}")
                for t in st.session_state.nucleos_dados[n_sel]["tarefas"]:
                    if t["status"] == s_val:
                        with st.container():
                            st.markdown(f"**{t['titulo']}**<br><small>Por: {t['criador']}</small>", unsafe_allow_html=True)
                            if st.session_state.usuario_logado['nucleo'] == n_sel:
                                novo_s = st.selectbox("Mover:", ["criado", "fazendo", "feito"], index=["criado", "fazendo", "feito"].index(t["status"]), key=f"sel_{t['id']}")
                                if novo_s != t["status"]:
                                    t["status"] = novo_s
                                    salvar_banco()
                                    st.rerun()

    # ABA SOLICITAÇÕES
    with aba_solicitacoes:
        # Apenas comunicação pode ENVIAR
        if st.session_state.usuario_logado['nucleo'] == "Comunicação":
            with st.form("sol"):
                dest = st.selectbox("Destino", list(st.session_state.nucleos_dados.keys()))
                assunto = st.text_input("Assunto")
                msg = st.text_area("Mensagem")
                if st.form_submit_button("Enviar"):
                    st.session_state.caixa_entrada[dest].append({"assunto": assunto, "msg": msg, "de": st.session_state.usuario_logado['nome']})
                    salvar_banco()
                    st.success("Enviado")
        else:
            st.warning("Apenas o núcleo de Comunicação possui permissão para envio de solicitações.")
        
        st.write("### Minhas Mensagens")
        for m in st.session_state.caixa_entrada[n_sel]:
            st.info(f"**{m['assunto']}** (De: {m['de']})\n\n{m['msg']}")
