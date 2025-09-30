import streamlit as st

# Definição da estrutura da página usando um dicionário
paginas = {
    "Páginas": [
        st.Page("paginas/inicial.py", title="Início", icon='🚓', default=True)
    ],
    "Exemplo": [
        st.Page("paginas/pagina1.py", title="Banco de Dados", icon='🚙'),
        # st.Page("paginas/pagina2.py", title="Exemplo", icon='⚡') # Página comentada
    ]
}

# Cria o objeto de navegação
pg = st.navigation(paginas)

# Executa o aplicativo
pg.run()
