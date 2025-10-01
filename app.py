import streamlit as st
import firebase_admin


# -----------------------------------------------------------------------------
# Lógica de Navegação (como antes)
# -----------------------------------------------------------------------------

# Lista de e-mails de supervisores
SUPERVISOR_EMAILS = ["thalestatasena@gmail.com"]

def get_paginas(user_email):
    """Retorna as páginas específicas para o perfil do usuário."""
    if user_email in SUPERVISOR_EMAILS:
        # Páginas para o supervisor
        return {
            "Supervisor": [
                st.Page("paginas/supervisor.py", title="Painel do Supervisor", icon='🛠️')
            ]
        }
    else:
        # Páginas para o colaborador
        return {
            "Colaborador": [
                st.Page("paginas/pagina1.py", title="Banco de Dados", icon='📤')
            ]
        }

# Páginas visíveis para todos
base_paginas = {
    "Páginas": [
        st.Page("paginas/inicial.py", title="Início", icon='🚀', default=True)
    ]
}

# Verifica se o usuário está logado para montar o menu
if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
    email = getattr(st.user, "email", "").lower()
    # Combina as páginas base com as páginas do perfil do usuário
    paginas = base_paginas | get_paginas(email)
else:
    # Se não estiver logado, mostra apenas as páginas base
    paginas = base_paginas

# Cria e executa a navegação
pg = st.navigation(paginas)
pg.run()
