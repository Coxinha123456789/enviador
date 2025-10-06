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

st.set_page_config(layout="centered", page_title="Envio com IA")

def analyze_image_with_gemini(image_bytes):
    """Analisa uma imagem usando o Gemini e retorna uma descrição."""
    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash)
        image_pil = Image.open(io.BytesIO(image_bytes))
        # Prompt ajustado para o contexto profissional
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
        msg_collaborator['Subject'] = "Confirmação de Envio de Imagem"
        body_collaborator = "Olá,\n\nEste é um e-mail de confirmação. Sua imagem e a análise da IA foram enviadas com sucesso para o seu supervisor.\n\nAtenciosamente,\nSistema Automático"
        msg_collaborator.attach(MIMEText(body_collaborator, 'plain'))
        server.sendmail(sender, collaborator, msg_collaborator.as_string())
        
        server.quit()
        return True, "E-mails enviados com sucesso!"
    except Exception as e:
        return False, f"Ocorreu um erro ao enviar os e-mails: {e}"

def upload_to_firebase_storage(image_bytes, user_email, file_name):
    """Faz o upload da imagem para o Firebase Storage e retorna a URL pública."""
    try:
        # A função conectar_firebase agora retorna db e bucket
        _, bucket = conectar_firebase()
        
        # Cria um caminho único para o arquivo no Storage
        path = f"images/{user_email}/{file_name}"
        blob = bucket.blob(path)
        
        # Faz o upload dos bytes da imagem
        blob.upload_from_string(image_bytes, content_type='image/jpeg')
        
        # Torna o arquivo público e obtém a URL
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
st.title("📤 App de Envio de Imagem")
st.write(f"Você está logado como: **{collaborator_email}**")
st.write("Faça o upload de uma imagem para enviá-la ao seu supervisor com uma análise automática.")

uploaded_file = st.file_uploader("Escolha uma imagem", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image_bytes = uploaded_file.getvalue()
    st.image(image_bytes, caption=f"Imagem a ser enviada: {uploaded_file.name}", use_container_width=True)
    st.divider()

    st.subheader("🤖 Análise da Imagem por IA")
    with st.spinner("Analisando a imagem..."):
        ai_description = analyze_image_with_gemini(image_bytes)
    
    if ai_description:
        st.text_area("Parecer da IA:", value=ai_description, height=150, disabled=True)
        
        if st.button("🚀 Enviar para Supervisor"):
            with st.spinner("Enviando e salvando..."):
                image_url = upload_to_firebase_storage(image_bytes, collaborator_email, uploaded_file.name)
                
                if image_url:
                    email_subject = f"Nova Imagem Recebida de {collaborator_email}"
                    email_body = f"""Olá,\n\nUma nova imagem foi enviada pelo colaborador {collaborator_email}.\n\nParecer da IA:\n--------------------------------------------------\n{ai_description}\n--------------------------------------------------\n\nAtenciosamente,\nSistema Automático"""
                    
                    email_ok, email_msg = send_emails(
                        EMAIL_SENDER, EMAIL_PASSWORD, SUPERVISOR_EMAIL, collaborator_email,
                        email_subject, email_body, image_bytes, uploaded_file.name
                    )

                    if email_ok:
                        try:
                            user_ref = db.collection(colecao).document(collaborator_email)
                            doc = user_ref.get()
                            dados = doc.to_dict() if doc.exists else {}

                            novo_envio = {
                                "descricao": ai_description,
                                "nome_arquivo": uploaded_file.name,
                                "data_envio": datetime.now(),
                                "url_imagem": image_url,
                                "status": "Em processo"  # Novo campo de status
                            }
                            
                            dados.setdefault('envios', []).append(novo_envio)
                            user_ref.set(dados)

                            st.success(f"{email_msg} Registro salvo com sucesso no banco de dados!")
                            st.balloons()

                        except Exception as e:
                            st.error(f"E-mails enviados, mas falha ao salvar o registro no banco de dados: {e}")
                    else:
                        st.error(f"Falha no envio de e-mails: {email_msg}")
