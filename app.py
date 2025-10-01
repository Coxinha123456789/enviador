import streamlit as st

# 🔑 Lista (ou um único) de e-mails de supervisores
SUPERVISOR_EMAILS = ["thalestatasena@gmail.com"]

# Função que monta o menu de navegação
def get_paginas(user_email):
    if user_email in SUPERVISOR_EMAILS:
        # Se for supervisor
        return {
            "Supervisor": [
                st.Page("paginas/supervisor.py", title="Painel do Supervisor", icon='🛠️')
            ]
        }
    else:
        # Se for colaborador
        return {
            "Colaborador": [
                st.Page("paginas/pagina1.py", title="Banco de Dados", icon='📤')
            ]
        }

# Página inicial sempre visível
base_paginas = {
    "Páginas": [
        st.Page("paginas/inicial.py", title="Início", icon='🚀', default=True)
    ]
}

# 🔐 Verifica se o usuário está logado
if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
    email = getattr(st.user, "email", "").lower()

    # Monta as páginas específicas do perfil
    paginas = base_paginas | get_paginas(email)

else:
    # Se não estiver logado, mostra apenas a inicial
    paginas = base_paginas

# Cria o objeto de navegação
pg = st.navigation(paginas)

# Executa o aplicativo
pg.run()
