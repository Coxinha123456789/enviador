# Dentro do novo arquivo: utils.py

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage

@st.cache_resource
def conectar_firebase():
    """
    Inicializa o Firebase de forma centralizada e retorna os clientes 
    do Firestore e do Storage.
    """
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(
            cred, 
            {
                'storageBucket': st.secrets.firebase.storageBucket 
            }
        )
    
    db = firestore.client()
    bucket = storage.bucket()
    return db, bucket
