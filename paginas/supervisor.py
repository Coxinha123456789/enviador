# No arquivo: paginas/supervisor.py

import streamlit as st
from utils import conectar_firebase
from datetime import datetime

# --- Conexão com Firebase ---
db, _ = conectar_firebase()
colecao = 'ColecaoEnviados'

# --- Configuração da Página ---
st.set_page_config(page_title="Painel do Supervisor", layout="wide")

# --- Verificação de Acesso ---
if not (hasattr(st, "user") and getattr(st.user, "is_logged_in", False)):
    st.warning("Você precisa fazer login como supervisor para acessar esta página.")
    st.stop()

email_logado = getattr(st.user, "email", "").lower()
SUPERVISOR_EMAILS = ["thalestatasena@gmail.com"] # Lista de e-mails de supervisores

if email_logado not in SUPERVISOR_EMAILS:
    st.error("Acesso negado. Esta página é restrita a supervisores.")
    st.stop()

# --- Funções ---
def atualizar_status(colaborador_email, nome_arquivo, data_envio, novo_status):
    """Atualiza o status de um envio específico no Firestore."""
    try:
        doc_ref = db.collection(colecao).document(colaborador_email)
        doc = doc_ref.get()
        if doc.exists:
            dados = doc.to_dict()
            envios = dados.get("envios", [])
            
            # Encontra o envio correto para atualizar
            for envio in envios:
                # Compara timestamps para garantir unicidade
                if envio.get('nome_arquivo') == nome_arquivo and envio.get('data_envio').timestamp() == data_envio.timestamp():
                    envio['status'] = novo_status
                    break
            
            doc_ref.set(dados)
            return True
    except Exception as e:
        st.error(f"Erro ao atualizar status: {e}")
        return False

# --- Inicialização do Estado da Sessão ---
if 'confirmation' not in st.session_state:
    st.session_state.confirmation = None

# --- Layout da Página ---
st.title("📊 Painel de Controle do Supervisor")
st.write("Visualize e gerencie os envios dos colaboradores.")
st.divider()

# --- Lógica Principal ---
try:
    docs = db.collection(colecao).stream()
    colaboradores = [doc.id for doc in docs]
except Exception as e:
    st.error(f"Erro ao buscar colaboradores: {e}")
    colaboradores = []

if not colaboradores:
    st.info("Nenhum colaborador realizou envios ainda.")
    st.stop()

# --- Barra Lateral para Seleção ---
st.sidebar.header("Filtros")
colaborador_selecionado = st.sidebar.selectbox(
    "Selecione um colaborador:",
    options=["Todos"] + colaboradores,
    index=0
)

# --- Exibição dos Dados ---
docs_para_exibir = []
if colaborador_selecionado == "Todos":
    docs_para_exibir = db.collection(colecao).stream()
else:
    doc = db.collection(colecao).document(colaborador_selecionado).get()
    if doc.exists:
        docs_para_exibir = [doc]

for doc in docs_para_exibir:
    colaborador_email = doc.id
    dados = doc.to_dict()
    envios = dados.get("envios", [])

    if envios:
        st.header(f"📂 Envios de: {colaborador_email}")
        
        envios_ordenados = sorted(
            [e for e in envios if 'data_envio' in e], 
            key=lambda x: x["data_envio"], 
            reverse=True
        )

        for i, envio in enumerate(envios_ordenados):
            # Identificador único para cada item na sessão
            item_id = f"{colaborador_email}_{i}"
            
            data_envio_obj = envio['data_envio']
            data_formatada = data_envio_obj.strftime('%d/%m/%Y às %H:%M')
            status_atual = envio.get('status', 'Em processo')
            
            with st.container(border=True):
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    if 'url_imagem' in envio:
                        st.image(envio['url_imagem'], caption=f"Arquivo: {envio.get('nome_arquivo', 'N/A')}")

                with col2:
                    st.write(f"**Enviado em:** {data_formatada}")
                    
                    # Exibição do Status
                    if status_atual == 'Aprovado':
                        st.markdown(f"**Status:** <span style='color: #22c55e;'>🟢 Aprovado</span>", unsafe_allow_html=True)
                    elif status_atual == 'Reprovado':
                        st.markdown(f"**Status:** <span style='color: #ef4444;'>🔴 Reprovado</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**Status:** <span style='color: #eab308;'>🟡 Em processo</span>", unsafe_allow_html=True)

                    st.write("**Parecer da IA:**")
                    st.info(envio.get("descricao", "Nenhuma descrição."))

                    # --- LÓGICA DE CONFIRMAÇÃO ---
                    # Se este item está aguardando confirmação
                    if st.session_state.confirmation == item_id:
                        action_text = "aprovar" if st.session_state.action_status == "Aprovado" else "reprovar"
                        st.warning(f"Tem certeza que deseja **{action_text}** este item?")
                        
                        confirm_col1, confirm_col2, _ = st.columns([1, 1, 4])
                        
                        if confirm_col1.button("✅ Sim", key=f"sim_{item_id}"):
                            if atualizar_status(colaborador_email, envio['nome_arquivo'], data_envio_obj, st.session_state.action_status):
                                st.success(f"Item marcado como {st.session_state.action_status}!")
                            st.session_state.confirmation = None # Limpa o estado
                            st.rerun()

                        if confirm_col2.button("❌ Não", key=f"nao_{item_id}"):
                            st.session_state.confirmation = None # Limpa o estado
                            st.rerun()
                    
                    # Exibe botões de ação apenas se não estiver em modo de confirmação e se o status for "Em processo"
                    elif status_atual == "Em processo":
                        action_col1, action_col2, _ = st.columns([1, 1, 4])
                        
                        if action_col1.button("Aprovar", key=f"aprovar_{item_id}"):
                            st.session_state.confirmation = item_id
                            st.session_state.action_status = "Aprovado"
                            st.rerun()

                        if action_col2.button("Reprovar", key=f"reprovar_{item_id}"):
                            st.session_state.confirmation = item_id
                            st.session_state.action_status = "Reprovado"
                            st.rerun()
