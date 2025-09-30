import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image
import io
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

# CORREÇÃO 2: st.set_page_config() movido para o topo.
st.set_page_config(layout="centered", page_title="Envio com IA")

@st.cache_resource
def conectar_firebase():
    """Initializes the Firebase app and returns a Firestore client."""
    # CORREÇÃO 3: Linhas reescritas para remover caracteres inválidos.
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = conectar_firebase()
colecao = 'ColecaoEnviados'

# --- Carregamento de Segredos e Configurações ---
CONFIG_LOADED = False
try:
    # CORREÇÃO 3: Linhas reescritas para remover caracteres inválidos.
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    SUPERVISOR_EMAIL = st.secrets.get("SUPERVISOR_EMAIL") # Usar .get() é mais seguro

    genai.configure(api_key=GOOGLE_API_KEY)
    CONFIG_LOADED = True
except (FileNotFoundError, KeyError) as e:
    st.error(f"Erro ao carregar segredos: {e}. Por favor, configure os secrets no painel do Streamlit Cloud.")

# Só continue se as configurações foram carregadas
if CONFIG_LOADED:
    st.title("Aplicativo Principal")
    
    # Este bloco só deve ser executado se o usuário estiver logado
    if hasattr(st, "user") and hasattr(st.user, "email"):
        user_ref = db.collection(colecao).document(st.user.email)
        doc = user_ref.get()
        # CORREÇÃO 1: Método corrigido para to_dict()
        dados = doc.to_dict() if doc.exists else {}
    else:
        st.warning("Faça login para continuar.")
        dados = {} # Garante que 'dados' exista mesmo sem login
else:
    st.stop() # Interrompe a execução se os segredos não foram carregados

# --- Funções Auxiliares ---

def analyze_image_with_gemini(image_bytes):
    """Analisa uma imagem usando o Gemini e retorna uma descrição."""
    if not GOOGLE_API_KEY:
        return "Análise de IA desabilitada. Nenhuma chave de API fornecida."
    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        image_pil = Image.open(io.BytesIO(image_bytes))
        prompt = "Descreva o que você vê nesta imagem, de forma objetiva, com no maximo 3 linhas."
        
        response = model.generate_content([prompt, image_pil])
        return response.text
    except Exception as e:
        st.error(f"Erro ao contatar a API de IA: {e}")
        return None


def send_emails(image_bytes, image_name, collaborator_email, image_description):
    """Envia e-mails para o supervisor (com anexo e descrição) e para o colaborador (confirmação)."""
    try:
        # Configurações do servidor SMTP
        SMTP_SERVER = "smtp.gmail.com"
        SMTP_PORT = 587

        # Conectando ao servidor
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        # --- E-mail para o Supervisor ---
        msg_supervisor = MIMEMultipart()
        msg_supervisor['From'] = EMAIL_SENDER
        msg_supervisor['To'] = SUPERVISOR_EMAIL
        msg_supervisor['Subject'] = f"Nova Imagem Recebida de {collaborator_email}"

        body_supervisor = f"""Olá,

Uma nova imagem foi enviada pelo colaborador {collaborator_email}.

Abaixo está uma descrição da imagem gerada por IA:
--------------------------------------------------
{image_description}
--------------------------------------------------

A imagem original está em anexo para sua referência.

Atenciosamente,
Sistema Automático"""
        msg_supervisor.attach(MIMEText(body_supervisor, 'plain'))
        
        # Anexando a imagem
        image = MIMEImage(image_bytes)
        image.add_header('Content-Disposition', 'attachment', filename=image_name)
        msg_supervisor.attach(image)
        
        server.sendmail(EMAIL_SENDER, SUPERVISOR_EMAIL, msg_supervisor.as_string())

        # --- E-mail de Confirmação para o Colaborador ---
        msg_collaborator = MIMEMultipart()
        msg_collaborator['From'] = EMAIL_SENDER
        msg_collaborator['To'] = collaborator_email
        msg_collaborator['Subject'] = "Confirmação de Envio de Imagem"

        body_collaborator = "Olá,\n\nEste é um e-mail de confirmação. Sua imagem e a análise da IA foram enviadas com sucesso para o seu supervisor.\n\nAtenciosamente,\nSistema Automático"
        msg_collaborator.attach(MIMEText(body_collaborator, 'plain'))
        
        server.sendmail(EMAIL_SENDER, collaborator_email, msg_collaborator.as_string())
        
        server.quit()
        return True, "E-mails enviados com sucesso!"

    except Exception as e:
        return False, f"Ocorreu um erro ao enviar os e-mails: {e}"

# --- Interface do Streamlit ---

st.title("📤 App de Envio de Imagem")
st.write("Faça o upload de uma imagem, digite seu e-mail e envie o material para seu supervisor com uma análise automática.")

if CONFIG_LOADED:
    # Input para o e-mail do colaborador
    collaborator_email = st.text_input(
        "Digite seu e-mail para receber a confirmação:",
        placeholder="seu_email@suaempresa.com"
    )

    # Input da imagem
    uploaded_file = st.file_uploader(
        "Escolha uma imagem",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_file is not None and collaborator_email:
        image_bytes = uploaded_file.getvalue()
        
        st.divider()
        st.subheader("🖼️ Visualização da Imagem")
        st.image(
            image_bytes,
            caption=f"Imagem a ser enviada: {uploaded_file.name}",
            width="stretch"   # atualizado
        )
        
        st.divider()
        st.subheader("🤖 Análise da Imagem por IA")
        
        with st.spinner("Analisando a imagem..."):
            ai_description = analyze_image_with_gemini(image_bytes)
        
        if ai_description:
            st.text_area("Descrição gerada:", value=ai_description, height=200, disabled=True)
            
                if st.button("🚀 Enviar para Supervisor"):
                    with st.spinner("Enviando e-mails e salvando registro..."):
                        success, message = send_emails(
                            image_bytes, 
                            uploaded_file.name, 
                            collaborator_email, 
                            ai_description
                        )
                        
                        if success:
                            try:

                                novo_envio = {
                                    "descricao": ai_description,
                                    "nome_arquivo": uploaded_file.name,
                                    "data_envio": datetime.now() # Salva a data e hora também
                                }
                                dados.setdefault('envios', []).append(novo_envio)

                                user_ref.set(dados)
                                
                                st.success(f"{message} Registro salvo com sucesso!")
                                st.balloons()

                            except Exception as e:
                                st.error(f"E-mails enviados, mas falha ao salvar no banco de dados: {e}")
                        else:
                            st.error(message)

    elif uploaded_file and not collaborator_email:
        st.warning("Por favor, insira seu e-mail para continuar.")

