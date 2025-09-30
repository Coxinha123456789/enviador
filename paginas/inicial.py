import streamlit as st

st.title("Página Inicial ")

 

if not st.user.is_logged_in:
    if st.button("Log in"):
        st.login()
        
else:
    st.write(f"Oi, {getattr(st.user, 'name', 'Usuário')}!")
    
    # Mostrar foto do usuário
    if hasattr(st.user, 'picture'):
        st.image(st.user.picture, width=100)
    
    # Mostrar informações básicas do usuário
    if hasattr(st.user, 'email'):
        st.write(f"Email: {st.user.email}")
    
    if hasattr(st.user, 'id'):
        st.write(f"ID: {st.user.id}")

    
    if st.sidebar.button("Log out"):
        st.logout()
