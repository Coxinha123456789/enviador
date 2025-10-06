# Dentro do arquivo: utils.py

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage

@st.cache_resource
def conectar_firebase():
    """
    Inicializa o Firebase e retorna o cliente do Firestore e o bucket do Storage.
    """
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        # Adicione a URL do seu bucket do Storage aqui
        firebase_admin.initialize_app(cred, {
            'storageBucket': st.secrets["firebase"]["storage_bucket_url"]
        })
    
    db = firestore.client()
    bucket = storage.bucket()
    return db, bucket
