import streamlit as st
import json
import os

# Configuração Global
st.set_page_config(page_title="Sistema IMLA", layout="wide")

# ARQUIVO DE BANCO
DB_FILE = "imla_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {
        "users": {},
        "nucleos": {
            n: {"feed": [], "tarefas": {"fazer": [], "progresso": [], "concluido": []}, "solicitacoes": []}
            for n in ["Cozinha e Nutrição", "Comunicação", "Captação de Recursos", "Pedagógico", "Financeiro", "Apadrinhamento"]
        }
    }

def save_db():
    with open(DB_FILE, "w") as f: json.dump(st.session_state.db, f)

# Inicialização de Estado
if "db" not in st.session_state: st.session_state.db = load_db()
if "user" not in st.session_state: st.session_state.user = None
if "view" not in st.session_state: st.session_state.view = "login"
if "nucleo_atual" not in st.session_state: st.session_state.nucleo_atual = "Cozinha e Nutrição"

# CSS ESTILO APPLE
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: -apple-system, BlinkMacSystemFont, sans-serif !important; }
    
    .nav-bar { 
        position: fixed; top: 0; left: 0; width: 100%; height: 70px; background: rgba(255,255,255,0.8);
        backdrop-filter: blur(20px); z-index: 999; display: flex; align-items: center; 
        padding: 0 40px; border-bottom: 1px solid rgba(0,0,0,0.1);
    }
    .card { background: #ffffff; padding: 20px; border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .banner { width: 100%; height: 300px; object-fit: cover; border-radius: 24px; margin-top: 80px; }
    </style>
""", unsafe_allow_html=True)

# --- FLUXO DE LOGIN/CADASTRO ---
if st.session_state.user is None:
    if st.session_state.view == "login":
        st.title("Sistema IMLA")
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            user = st.session_state.db["users"].get(email)
            if user and user["senha"] == senha:
                st.session_state.user = user
                st.rerun()
            else: st.error("Credenciais inválidas")
        if st.button("Criar Cadastro"): st.session_state.view = "cadastro"; st.rerun()
    else:
        st.title("Cadastro IMLA")
        nome = st.text_input("Nome Completo")
        email = st.text_input("Seu melhor e-mail")
        nucleo = st.selectbox("Núcleo", list(st.session_state.db["nucleos"].keys()))
        senha = st.text_input("Senha", type="password")
        conf = st.text_input("Confirmar Senha", type="password")
        if st.button("Finalizar"):
            if senha == conf:
                st.session_state.db["users"][email] = {"nome": nome, "email": email, "nucleo": nucleo, "senha": senha}
                save_db()
                st.session_state.view = "login"; st.rerun()
            else: st.error("Senhas não conferem")
        if st.button("Voltar"): st.session_state.view = "login"; st.rerun()

# --- ÁREA PRIVADA ---
else:
    # Barra Superior (Ilha Flutuante)
    st.markdown('<div class="nav-bar">', unsafe_allow_html=True)
    cols = st.columns([1, 6, 2])
    with cols[0]: st.write("### IMLA")
    with cols[1]:
        sub_cols = st.columns(len(st.session_state.db["nucleos"]))
        for i, n in enumerate(st.session_state.db["nucleos"].keys()):
            if sub_cols[i].button(n): st.session_state.nucleo_atual = n; st.rerun()
    with cols[2]:
        with st.popover(f"👤 {st.session_state.user['nome']}"):
            st.write(f"**{st.session_state.user['nome']}**")
            st.write(f"Núcleo: {st.session_state.user['nucleo']}")
            if st.button("Sair"): st.session_state.user = None; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Conteúdo Principal
    st.image("IMG_3985.JPG", use_container_width=True) # Certifique-se que o arquivo está na pasta
    st.title(f"Área: {st.session_state.nucleo_atual}")

    t1, t2, t3 = st.tabs(["Feed", "Tarefas (Kanban)", "Solicitações"])

    with t1:
        st.subheader("Atualizações")
        if st.session_state.user["nucleo"] == st.session_state.nucleo_atual:
            msg = st.text_input("Nova atualização para o núcleo:")
            if st.button("Publicar"):
                st.session_state.db["nucleos"][st.session_state.nucleo_atual]["feed"].insert(0, f"{st.session_state.user['nome']}: {msg}")
                save_db(); st.rerun()
        for post in st.session_state.db["nucleos"][st.session_state.nucleo_atual]["feed"]:
            st.markdown(f'<div class="card">{post}</div>', unsafe_allow_html=True)

    with t2:
        # Kanban Trello Style
        if st.session_state.user["nucleo"] == st.session_state.nucleo_atual:
            new_task = st.text_input("Adicionar tarefa...")
            if st.button("Criar Tarefa"):
                st.session_state.db["nucleos"][st.session_state.nucleo_atual]["tarefas"]["fazer"].append(new_task)
                save_db(); st.rerun()
        
        k1, k2, k3 = st.columns(3)
        cols_map = {"fazer": k1, "progresso": k2, "concluido": k3}
        for status, col in cols_map.items():
            with col:
                st.markdown(f"#### {status.capitalize()}")
                tasks = st.session_state.db["nucleos"][st.session_state.nucleo_atual]["tarefas"][status]
                for idx, task in enumerate(tasks):
                    st.markdown(f'<div class="card">{task}</div>', unsafe_allow_html=True)
                    # Botão para mover tarefas
                    if st.button(f"Mover →", key=f"btn_{status}_{idx}"):
                        # Lógica simples de mover para o próximo status
                        st.session_state.db["nucleos"][st.session_state.nucleo_atual]["tarefas"][status].pop(idx)
                        save_db(); st.rerun()

    with t3:
        st.subheader("Solicitações Entre Núcleos")
        nucleos_lista = list(st.session_state.db["nucleos"].keys())
        target = st.selectbox("Para qual núcleo enviar?", nucleos_lista)
        solicitacao = st.text_area("Descrição da solicitação:")
        if st.button("Enviar Solicitação"):
            st.session_state.db["nucleos"][target]["solicitacoes"].append(f"De: {st.session_state.nucleo_atual} | {solicitacao}")
            save_db(); st.success("Enviado!")
        
        st.divider()
        st.write("Caixa de Entrada:")
        for s in st.session_state.db["nucleos"][st.session_state.nucleo_atual]["solicitacoes"]:
            st.info(s)
