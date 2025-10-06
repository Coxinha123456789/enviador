# No arquivo: paginas/pagina1.py

import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image
import io
import google.generativeai as genai
from datetime import datetime
from utils import conectar_firebase
from google.api_core.exceptions import Forbidden

st.set_page_config(layout="centered", page_title="Envio de Documentos")

# ... (o resto das suas funções `analyze_image_with_gemini`, `send_emails`, `upload_to_firebase_storage` permanecem iguais) ...

def analyze_image_with_gemini(image_bytes):
    """Analisa uma imagem usando o Gemini e retorna uma descrição."""
    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        image_pil = Image.open(io.BytesIO(image_bytes))
        prompt = """
        Aja como uma assistente profissional para um supervisor. A imagem a seguir é um documento enviado por um colaborador (como um atestado médico, um recibo para reembolso, etc.). 
        Sua tarefa é analisar a imagem e fornecer um breve parecer para o supervisor, destacando as informações mais importantes e sugerindo se o documento parece estar em conformidade para aprovação.
        
        Seu parecer deve ser objetivo e conciso (máximo de 4 linhas), contendo:
        1. O tipo de documento que parece ser.
        2. As informações chave contidas nele (ex: datas, valores, nomes).
        3. Uma recomendação inicial (ex: "Parece legítimo para aprovação", "Requer verificação adicional", "Informações parecem inconsistentes").
        """
        response = model.generate_content([prompt, image_pil])
        return response.text
    except Exception as e:
        st.error(f"Erro ao contatar a API de IA: {e}")
        return None

def send_emails(sender, password, supervisor, collaborator, subject, body, image_bytes, image_name):
    """Envia e-mails para o supervisor (com anexo) e colaborador (confirmação)."""
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)

        # --- E-mail para o Supervisor ---
        msg_supervisor = MIMEMultipart()
        msg_supervisor['From'] = sender
        msg_supervisor['To'] = supervisor
        msg_supervisor['Subject'] = subject
        msg_supervisor.attach(MIMEText(body, 'plain'))
        image = MIMEImage(image_bytes, name=image_name)
        msg_supervisor.attach(image)
        server.sendmail(sender, supervisor, msg_supervisor.as_string())

        # --- E-mail de Confirmação para o Colaborador ---
        msg_collaborator = MIMEMultipart()
        msg_collaborator['From'] = sender
        msg_collaborator['To'] = collaborator
        msg_collaborator['Subject'] = "Confirmação de Envio de Documento"
        body_collaborator = "Olá,\n\nEste é um e-mail de confirmação. Seu documento e a análise da IA foram enviados com sucesso para seu supervisor.\n\nAtenciosamente,\nSistema Automático"
        msg_collaborator.attach(MIMEText(body_collaborator, 'plain'))
        server.sendmail(sender, collaborator, msg_collaborator.as_string())
        
        server.quit()
        return True, "E-mails enviados com sucesso!"
    except Exception as e:
        return False, f"Ocorreu um erro ao enviar os e-mails: {e}"

def upload_to_firebase_storage(image_bytes, user_email, file_name):
    """Faz o upload da imagem para o Firebase Storage e retorna a URL pública."""
    try:
        _, bucket = conectar_firebase()
        path = f"images/{user_email}/{file_name}"
        blob = bucket.blob(path)
        blob.upload_from_string(image_bytes, content_type='image/jpeg')
        blob.make_public()
        return blob.public_url
    except Exception as e:
        st.error(f"Erro ao fazer upload para o Firebase Storage: {e}")
        return None

# --- LÓGICA PRINCIPAL ---
db, _ = conectar_firebase() 
colecao = 'ColecaoEnviados'

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    SUPERVISOR_EMAIL = st.secrets.get("SUPERVISOR_EMAIL")
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"Erro fatal ao carregar segredos: {e}. Verifique o arquivo secrets.toml.")
    st.stop()

if not (hasattr(st, "user") and getattr(st.user, "is_logged_in", False)):
    st.warning("Faça login para continuar.")
    st.stop()

collaborator_email = getattr(st.user, "email", "não identificado")
st.title("📤 Envio de Documentos")
st.write(f"Logado como: **{collaborator_email}**")
st.write("Faça o upload de um documento (atestado, recibo, etc.) para análise e aprovação.")
st.divider()

with st.container(border=True):
    uploaded_file = st.file_uploader(
        "Selecione o arquivo de imagem", 
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed"
    )

if uploaded_file is not None:
    image_bytes = uploaded_file.getvalue()
    
    with st.container(border=True):
        st.subheader("Visualização")
        st.image(image_bytes, caption=f"Arquivo: {uploaded_file.name}", use_container_width=True)
