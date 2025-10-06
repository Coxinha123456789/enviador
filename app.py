import streamlit as st

# -----------------------------------------------------------------------------
# Lógica de Navegação Aprimorada
# -----------------------------------------------------------------------------

# Lista de e-mails de supervisores
SUPERVISOR_EMAILS = ["thalestatasena@gmail.com"]

def get_paginas(user_email):
    """Retorna as páginas específicas para o perfil do usuário."""
    if user_email in SUPERVISOR_EMAILS:
        # Páginas para o supervisor com Dashboard
        return {
            "Supervisor": [
                st.Page("paginas/dashboard.py", title="Dashboard", icon='📊'),
                st.Page("paginas/supervisor.py", title="Gerenciar Envios", icon='🛠️')
            ]
        }
    else:
        # Páginas para o colaborador
        return {
            "Colaborador": [
                st.Page("paginas/pagina1.py", title="Enviar Documento", icon='📤'),
                st.Page("paginas/historico.py", title="Meu Histórico", icon='📜')
            ]
        }

# Páginas visíveis para todos
base_paginas = {
    "Página Principal": [
        st.Page("paginas/inicial.py", title="Início", icon='🚀', default=True)
    ]
}

# Verifica se o usuário está logado para montar o menu
if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
    email = getattr(st.user, "email", "").lower()
    paginas = base_paginas | get_paginas(email)
else:
    paginas = base_paginas

# Cria e executa a navegação
pg = st.navigation(paginas)
pg.run()
