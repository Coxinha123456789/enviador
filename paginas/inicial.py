# No arquivo: paginas/inicial.py

import streamlit as st
from utils import conectar_firebase

st.set_page_config(page_title="Início", layout="wide")

# --- Verificação de Login ---
if not (hasattr(st, "user") and st.user.is_logged_in):
    st.title("Bem-vindo(a) à Plataforma de Gestão de Documentos")
    st.write("Faça o login para continuar.")
    if st.button("Log in", type="primary"):
        st.login()
    st.stop()

# --- Conexão com Firebase e Definições ---
db, _ = conectar_firebase()
SUPERVISOR_EMAILS = ["thalestatasena@gmail.com"] # Mantenha esta lista sincronizada com app.py
user_email = getattr(st.user, "email", "").lower()
user_name = getattr(st.user, "name", "Usuário")

# --- Funções de busca de dados ---
@st.cache_data(ttl=120) # Cache de 2 minutos para evitar leituras excessivas
def get_supervisor_stats():
    """Busca o número total de envios pendentes para todos os colaboradores."""
    pendentes = 0
    try:
        docs = db.collection('ColecaoEnviados').stream()
        for doc in docs:
            envios = doc.to_dict().get("envios", [])
            pendentes += sum(1 for e in envios if e.get('status') == 'Em processo')
    except Exception as e:
        st.error(f"Não foi possível carregar as estatísticas: {e}")
    return pendentes

@st.cache_data(ttl=120)
def get_collaborator_stats(email):
    """Busca as estatísticas de envios para um colaborador específico."""
    stats = {'pendentes': 0, 'aprovados': 0, 'reprovados': 0}
    try:
        doc_ref = db.collection('ColecaoEnviados').document(email)
        doc = doc_ref.get()
        if doc.exists:
            envios = doc.to_dict().get("envios", [])
            stats['pendentes'] = sum(1 for e in envios if e.get('status') == 'Em processo')
            stats['aprovados'] = sum(1 for e in envios if e.get('status') == 'Aprovado')
            stats['reprovados'] = sum(1 for e in envios if e.get('status') == 'Reprovado')
    except Exception as e:
        st.error(f"Não foi possível carregar suas estatísticas: {e}")
    return stats

# --- Renderização da Página ---
st.title(f"Bem-vindo(a), {user_name}!")

# Adiciona informações do usuário na barra lateral
with st.sidebar:
    st.header("Perfil")
    if hasattr(st.user, 'picture'):
        st.image(st.user.picture, width=100)
    st.write(f"**Email:** {user_email}")
    if st.button("Log out"):
        st.logout()
    st.divider()


# --- Exibição Condicional (Supervisor vs Colaborador) ---
if user_email in SUPERVISOR_EMAILS:
    # --- VISÃO DO SUPERVISOR ---
    st.subheader("Portal do Supervisor")
    pendentes_total = get_supervisor_stats()

    st.info(f"Você tem **{pendentes_total}** documento(s) aguardando sua análise.", icon="🔔")
    st.divider()

    st.subheader("Ações Rápidas")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("#### 📊 Dashboard Analítico")
            st.write("Visualize métricas, gráficos e a performance geral do processo.")
            st.page_link("paginas/dashboard.py", label="Acessar Dashboard", icon="📊")
    
    with col2:
        with st.container(border=True):
            st.markdown("#### 🛠️ Gerenciar Envios")
            st.write("Analise, aprove ou reprove os documentos enviados pelos colaboradores.")
            st.page_link("paginas/supervisor.py", label="Gerenciar Documentos", icon="🛠️")

else:
    # --- VISÃO DO COLABORADOR ---
    st.subheader("Seu Resumo")
    stats = get_collaborator_stats(user_email)

    col1, col2, col3 = st.columns(3)
    col1.metric("Pendentes", f"{stats['pendentes']} 🟡")
    col2.metric("Aprovados", f"{stats['aprovados']} 🟢")
    col3.metric("Reprovados", f"{stats['reprovados']} 🔴")
    st.divider()

    st.subheader("Ações Rápidas")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("#### 📤 Enviar Novo Documento")
            st.write("Faça o upload de um novo atestado ou documento para validação.")
            st.page_link("paginas/pagina1.py", label="Iniciar Envio", icon="📤")

    with col2:
        with st.container(border=True):
            st.markdown("#### 📜 Meu Histórico")
            st.write("Acompanhe o status e a linha do tempo de todos os seus envios.")
            st.page_link("paginas/historico.py", label="Ver Histórico", icon="📜")
