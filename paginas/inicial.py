import streamlit as st

st.title("Página Inicial ")

 

if not st.user.is_logged_in:
    st.write(st.user)
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
    
    # Todas as informações disponíveis
    st.json(dict(st.user))
    
    # Explicação dos campos do Google OAuth
    st.subheader("📋 O que significa cada campo:")
    
    explicacoes = {
        "is_logged_in": "Se o usuário está logado",
        "iss": "Emissor do token (Google)",
        "azp": "ID do cliente autorizado (sua app)",
        "aud": "Audiência do token (sua app)",
        "sub": "ID único do usuário no Google",
        "email": "Email do usuário",
        "email_verified": "Se o email foi verificado",
        "at_hash": "Hash do token de acesso",
        "nonce": "Número usado uma vez (segurança)",
        "name": "Nome completo do usuário",
        "picture": "URL da foto do perfil",
        "given_name": "Primeiro nome",
        "family_name": "Sobrenome",
        "iat": "Quando o token foi criado",
        "exp": "Quando o token expira"
    }
    
    for campo, descricao in explicacoes.items():
        if hasattr(st.user, campo):
            st.write(f"**{campo}**: {descricao}")
    
    if st.sidebar.button("Log out"):
        st.logout()
