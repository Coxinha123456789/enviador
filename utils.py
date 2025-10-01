# Dentro do arquivo: utils.py (Versão Simplificada)

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

@st.cache_resource
def conectar_firebase():
    """
    Inicializa o Firebase e retorna APENAS o cliente do Firestore.
    """
    try:
        firebase_admin.get_app()
    except ValueError:
        # A inicialização não precisa mais da opção 'storageBucket'
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    
    # Retorna apenas o cliente do Firestore
    db = firestore.client()
    return db
