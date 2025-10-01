import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image
import io
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime
from utils import conectar_firebase 
# --- Configuração da página ---
st.set_page_config(layout="centered", page_title="Envio com IA")


db, bucket = conectar_firebase()

colecao = 'ColecaoEnviados'

# --- Carregamento de Segredos ---
CONFIG_LOADED = False
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    SUPERVISOR_EMAIL = st.secrets.get("SUPERVISOR_EMAIL")

    genai.configure(api_key=GOOGLE_API_KEY)
    CONFIG_LOADED = True
except Exception as e:
    st.error(f"Erro ao carregar segredos: {e}")
    st.stop()

# --- Se não estiver logado ---
if not (hasattr(st, "user") and getattr(st.user, "is_logged_in", False)):
    st.warning("Faça login para continuar.")
    st.stop()

# --- Email do colaborador vem direto do login ---
collaborator_email = getattr(st.user, "email", None)

st.title("📤 App de Envio de Imagem")
st.write(f"Você está logado como: **{collaborator_email}**")
st.write("Faça o upload de uma imagem para enviá-la ao seu supervisor com uma análise automática.")

# --- Upload da imagem ---
uploaded_file = st.file_uploader("Escolha uma imagem", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image_bytes = uploaded_file.getvalue()

    st.divider()
    st.subheader("🖼️ Visualização da Imagem")
    st.image(image_bytes, caption=f"Imagem a ser enviada: {uploaded_file.name}", use_container_width=True)

    st.divider()
    st.subheader("🤖 Análise da Imagem por IA")

    from google.generativeai import GenerativeModel
    model = GenerativeModel(model_name='gemini-2.5-flash')

    with st.spinner("Analisando a imagem..."):
        ai_description = model.generate_content([
            "Descreva o que você vê nesta imagem, de forma objetiva, com no máximo 3 linhas.",
            Image.open(io.BytesIO(image_bytes))
        ]).text

    if ai_description:
        st.text_area("Descrição gerada:", value=ai_description, height=200, disabled=True)

        if st.button("🚀 Enviar para Supervisor"):
            with st.spinner("Enviando e-mails e salvando registro..."):

                # 🔹 Função de envio de e-mails
                def send_emails():
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

                        # --- Supervisor ---
                        msg_supervisor = MIMEMultipart()
                        msg_supervisor['From'] = EMAIL_SENDER
                        msg_supervisor['To'] = SUPERVISOR_EMAIL
                        msg_supervisor['Subject'] = f"Nova Imagem Recebida de {collaborator_email}"
                        body_supervisor = f"""Olá,

Uma nova imagem foi enviada pelo colaborador {collaborator_email}.

Descrição da imagem (IA):
--------------------------------------------------
{ai_description}
--------------------------------------------------

Atenciosamente,
Sistema Automático"""
                        msg_supervisor.attach(MIMEText(body_supervisor, 'plain'))
                        msg_supervisor.attach(MIMEImage(image_bytes, name=uploaded_file.name))
                        server.sendmail(EMAIL_SENDER, SUPERVISOR_EMAIL, msg_supervisor.as_string())

                        # --- Colaborador (confirmação) ---
                        msg_collaborator = MIMEMultipart()
                        msg_collaborator['From'] = EMAIL_SENDER
                        msg_collaborator['To'] = collaborator_email
                        msg_collaborator['Subject'] = "Confirmação de Envio de Imagem"
                        msg_collaborator.attach(MIMEText(
                            "Sua imagem foi enviada com sucesso ao supervisor.\n\nAtenciosamente,\nSistema Automático",
                            'plain'
                        ))
                        server.sendmail(EMAIL_SENDER, collaborator_email, msg_collaborator.as_string())

                        server.quit()
                        return True, "E-mails enviados com sucesso!"
                    except Exception as e:
                        return False, str(e)

                ok, msg = send_emails()
                if ok:
                    try:
                        # 🔹 Upload da imagem para o Firebase Storage
                        bucket = storage.bucket()
                        blob = bucket.blob(f"envios/{collaborator_email}/{uploaded_file.name}")
                        blob.upload_from_string(image_bytes, content_type=uploaded_file.type)
                        blob.make_public()
                        image_url = blob.public_url

                        # 🔹 Salvar no Firestore
                        user_ref = db.collection(colecao).document(collaborator_email)
                        doc = user_ref.get()
                        dados = doc.to_dict() if doc.exists else {}

                        novo_envio = {
                            "descricao": ai_description,
                            "nome_arquivo": uploaded_file.name,
                            "data_envio": datetime.now(),
                            "url_imagem": image_url
                        }
                        dados.setdefault('envios', []).append(novo_envio)
                        user_ref.set(dados)

                        st.success(f"{msg} Registro salvo com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"E-mails enviados, mas falha ao salvar no banco de dados: {e}")
                else:
                    st.error(f"Erro ao enviar e-mails: {msg}")
