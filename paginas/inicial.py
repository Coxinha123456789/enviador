# No arquivo: paginas/inicial.py

import streamlit as st
from utils import conectar_firebase

st.set_page_config(page_title="Início", layout="wide")

if not (hasattr(st, "user") and st.user.is_logged_in):
    st.title("Bem-vindo(a) à Plataforma de Gestão de Documentos")
    st.write("Faça o login para continuar.")
    if st.button("Log in", type="primary"):
        st.login()
    st.stop() 

db, _ = conectar_firebase()
user_email = getattr(st.user, "email", "").lower()
user_name = getattr(st.user, "name", "Usuário")

@st.cache_data(ttl=120)
def get_user_role(email):
    if not email: return None
    try:
        user_doc = db.collection('users').document(email.lower()).get()
        if user_doc.exists: return user_doc.to_dict().get("role")
    except: return None
    return None

@st.cache_data(ttl=120)
def get_supervisor_stats():
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

user_role = get_user_role(user_email)
st.title(f"Bem-vindo(a), {user_name}!")

with st.sidebar:
    st.header("Perfil")
    if hasattr(st.user, 'picture'):
        st.image(st.user.picture, width=100)
    st.write(f"**Email:** {user_email}")
    if st.button("Log out"):
        st.logout()
    st.divider()

if user_role == 'supervisor':
    st.subheader("Portal do Supervisor")
    pendentes_total = get_supervisor_stats()
    st.info(f"Você tem **{pendentes_total}** documento(s) aguardando sua análise.", icon="🔔")
    st.divider()
    st.subheader("Ações Rápidas")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("#### 📊 Dashboard Analítico")
            st.page_link("paginas/dashboard.py", label="Acessar Dashboard", icon="📊")
    with col2:
        with st.container(border=True):
            st.markdown("#### 🛠️ Gerenciar Envios")
            st.page_link("paginas/supervisor.py", label="Gerenciar Documentos", icon="🛠️")
else:
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
            st.page_link("paginas/pagina1.py", label="Iniciar Envio", icon="📤")
    with col2:
        with st.container(border=True):
            st.markdown("#### 📜 Meu Histórico")
            st.page_link("paginas/historico.py", label="Ver Histórico", icon="📜")
