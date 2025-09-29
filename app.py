import streamlit as st 

paginas = {
    "Páginas": [ st.Page("paginas/inicial.py", title="Início", icon='🚓', default=True)],
    
    "Exemplo": [ st.Page("paginas/pagina1.py", title="Banco de Dados", icon='🚙'), 
            #     st.Page("paginas/pagina2.py", title="Exemplo", icon='⚡')
            ]
}

# Usa a estrutura de páginas final (com ou sem Admin)
pg = st.navigation(paginas)
pg.run()
