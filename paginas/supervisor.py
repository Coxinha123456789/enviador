import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from app import conectar_firebase
db, bucket = conectar_firebase()

st.set_page_config(page_title="Painel do Supervisor", layout="wide")

# --- Conectar ao Firestore ---
@st.cache_resource
def conectar_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = conectar_firebase()
colecao = 'ColecaoEnviados'

# --- Verificação de login ---
if not (hasattr(st, "user") and getattr(st.user, "is_logged_in", False)):
    st.warning("Você precisa fazer login como supervisor para acessar esta página.")
    st.stop()

email_logado = getattr(st.user, "email", "").lower()
SUPERVISOR_EMAILS = ["thalestatasena@gmail.com"]

if email_logado not in SUPERVISOR_EMAILS:
    st.error("Acesso negado. Esta página é restrita a supervisores.")
    st.stop()

# --- Layout ---
st.title("📊 Painel do Supervisor")
st.write("Visualize os envios realizados pelos colaboradores.")

# --- Listar colaboradores que já enviaram algo ---
docs = db.collection(colecao).stream()
colaboradores = [doc.id for doc in docs]

if not colaboradores:
    st.info("Nenhum colaborador enviou imagens ainda.")
    st.stop()

# --- Sidebar para selecionar colaborador ---
st.sidebar.header("👥 Colaboradores")
colaborador_selecionado = st.sidebar.selectbox("Selecione um colaborador:", colaboradores)

if colaborador_selecionado:
    doc_ref = db.collection(colecao).document(colaborador_selecionado)
    doc = doc_ref.get()

    if doc.exists:
        dados = doc.to_dict()
        envios = dados.get("envios", [])

        if envios:
            st.subheader(f"📂 Histórico de {colaborador_selecionado}")
            
            for envio in sorted(envios, key=lambda x: x["data_envio"], reverse=True):
                with st.expander(f"📎 {envio['nome_arquivo']} — {envio['data_envio']}"):
                    st.write("**Descrição da IA:**")
                    st.write(envio["descricao"])

                    if "url_imagem" in envio:
                        st.image(envio["url_imagem"], caption=envio["nome_arquivo"], use_container_width=True)
                    else:
                        st.warning("Imagem não disponível.")
        else:
            st.info(f"O colaborador **{colaborador_selecionado}** ainda não enviou imagens.")
    else:
        st.warning(f"Nenhum dado encontrado para {colaborador_selecionado}.")
