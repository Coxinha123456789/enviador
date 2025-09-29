import streamlit as st
import asyncio
from streamlit_oauth import OAuth2Component
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image
import io
import google.generativeai as genai
import smtplib

# --- Configuração da Página ---
st.set_page_config(layout="centered", page_title="Login com Google")

# --- Configuração de Segredos (lidos do st.secrets) ---
try:
    # OAuth
    CLIENT_ID = st.secrets["oauth"]["client_id"]
    CLIENT_SECRET = st.secrets["oauth"]["client_secret"]
    REDIRECT_URI = st.secrets["oauth"]["redirect_uri"]
    
    # Gemini API
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)

    # Email
    EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    SUPERVISOR_EMAIL = st.secrets["SUPERVISOR_EMAIL"]

    CONFIG_LOADED = True
except (KeyError, FileNotFoundError):
    st.error("Erro: As configurações de segredos (secrets.toml) não foram encontradas ou estão incompletas. Verifique seu arquivo de segredos no Streamlit Cloud.")
    CONFIG_LOADED = False

# --- Configurações do Google OAuth ---
AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"


# --- Funções Auxiliares (IA e E-mail) ---
def analyze_image_with_gemini(image_bytes):
    """Analisa uma imagem usando o Gemini e retorna uma descrição."""
    if not GOOGLE_API_KEY:
        return "Análise de IA desabilitada. Nenhuma chave de API fornecida."
    try:
        # A ÚNICA MODIFICAÇÃO NECESSÁRIA É AQUI:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        
        image_pil = Image.open(io.BytesIO(image_bytes))
        prompt = "Descreva o que você vê nesta imagem, de forma objetiva, entorno de 2 linhas de texto."
        
        response = model.generate_content([prompt, image_pil])
        return response.text
    except Exception as e:
        st.error(f"Erro ao contatar a API de IA: {e}")
        return None

def send_emails(image_bytes, image_name, collaborator_email, image_description):
    """Envia e-mails para o supervisor e para o colaborador."""
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
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
        image = MIMEImage(image_bytes, name=image_name)
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


# --- Páginas do Aplicativo ---

def render_upload_page():
    """Mostra a página principal do app após o login."""
    user_info = st.session_state.get("user_info", {})
    user_name = user_info.get("name", "Usuário")
    user_email = user_info.get("email", "")
    
    st.title(f"Bem-vindo(a), {user_name}!")
    st.write("Você está logado. Agora você pode enviar uma imagem para análise.")

    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.pop("user_info", None) # Limpa as informações do usuário
        st.rerun()

    st.divider()

    # Funcionalidade de Upload
    uploaded_file = st.file_uploader("Escolha uma imagem", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        image_bytes = uploaded_file.getvalue()
        st.image(image_bytes, caption="Imagem a ser enviada", use_column_width=True)

        if st.button("Analisar e Enviar para Supervisor", use_container_width=True):
            with st.spinner("Analisando imagem..."):
                description = analyze_image_with_gemini(image_bytes)
            
            if description:
                st.text_area("Descrição Gerada:", value=description, height=150)
                with st.spinner("Enviando e-mails..."):
                    success, message = send_emails(image_bytes, uploaded_file.name, user_email, description)
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)

def render_login_page():
    """Mostra o botão de login do Google."""
    st.title("Login do Aplicativo")
    st.write("Por favor, use sua conta Google para acessar o sistema.")
    
    oauth2 = OAuth2Component(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        authorize_endpoint=AUTHORIZE_ENDPOINT,
        token_endpoint=TOKEN_ENDPOINT,
        refresh_token_endpoint=None,
        revoke_token_endpoint=REVOKE_ENDPOINT,
    )

    if 'token' not in st.session_state:
        st.session_state.token = None

    if st.session_state.token is None:
        result = asyncio.run(oauth2.authorize_button(
            name="Login com o Google",
            icon="https://www.google.com.br/favicon.ico",
            redirect_uri=REDIRECT_URI,
            scope="openid email profile",
            key="google",
            use_container_width=True,
        ))
        if result and "token" in result:
            st.session_state.token = result.get("token")
            st.rerun()
    else:
        token = st.session_state.token
        user_info = token.get("userinfo")
        if user_info:
            st.session_state.user_info = user_info
        st.rerun()


# --- Lógica Principal (Router) ---
if not CONFIG_LOADED:
    st.stop()

if 'user_info' not in st.session_state:
    render_login_page()
else:
    render_upload_page()
