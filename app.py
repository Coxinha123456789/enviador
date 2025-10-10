# No arquivo: app.py

import streamlit as st
from utils import conectar_firebase

# --- Configurações Globais ---
SUPERADMIN_EMAIL = "thales.santoseng@gmail.com" # !!! TROQUE PELO SEU E-MAIL !!!

# --- Conexão e Funções de Permissão ---
db, _ = conectar_firebase()

@st.cache_data(ttl=300)
def get_user_role(email):
    """Consulta o Firestore para obter a função (role) de um usuário."""
    if not email:
        return None
    try:
        user_doc = db.collection('users').document(email.lower()).get()
        if user_doc.exists:
            return user_doc.to_dict().get("role")
    except Exception as e:
        st.error(f"Erro ao verificar permissões: {e}")
        return None
    return None

# --- Lógica de Navegação ---
def get_paginas_por_role(role):
    """Retorna as páginas específicas para a função do usuário."""
    if role == "supervisor":
        return {
            "Supervisor": [
                st.Page("paginas/dashboard.py", title="Dashboard", icon='📊'),
                st.Page("paginas/supervisor.py", title="Gerenciar Envios", icon='🛠️')
            ]
        }
    elif role == "colaborador":
        return {
            "Colaborador": [
                st.Page("paginas/pagina1.py", title="Enviar Documento", icon='📤'),
                st.Page("paginas/historico.py", title="Meu Histórico", icon='📜')
            ]
        }
    return {}

# --- Construção do Menu ---
paginas = {
    "Página Principal": [
        st.Page("paginas/inicial.py", title="Início", icon='🚀', default=True)
    ]
}

if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
    email = getattr(st.user, "email", "").lower()
    role = get_user_role(email)
    
    paginas.update(get_paginas_por_role(role))

    if email == SUPERADMIN_EMAIL:
        paginas["Administração"] = [
            st.Page("paginas/superadm.py", title="Painel Super Admin", icon='🔑')
        ]

# Cria e executa a navegação
pg = st.navigation(paginas)
pg.run()
