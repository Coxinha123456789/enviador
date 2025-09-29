import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image
import io
import google.generativeai as genai

# --- Configuração da Página ---
st.set_page_config(layout="centered", page_title="Envio com IA")

# --- Gerenciamento de Configurações e Segredos ---

# Tenta carregar as configurações do st.secrets (ideal para deploy)
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    SUPERVISOR_EMAIL = st.secrets["SUPERVISOR_EMAIL"]
    
    genai.configure(api_key=GOOGLE_API_KEY)
    CONFIG_LOADED = True

# Fallback para inputs manuais se secrets.toml não for encontrado (para desenvolvimento local)
except (FileNotFoundError, KeyError):
    CONFIG_LOADED = False
    st.error("Arquivo de segredos não configurado para deploy. Por favor, configure os secrets no painel do Streamlit Cloud.")

# --- Funções Auxiliares ---

def analyze_image_with_gemini(image_bytes):
    """Analisa uma imagem usando o Gemini e retorna uma descrição."""
    if not GOOGLE_API_KEY:
        return "Análise de IA desabilitada. Nenhuma chave de API fornecida."
    try:
        # A ÚNICA MODIFICAÇÃO NECESSÁRIA É AQUI:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        
        image_pil = Image.open(io.BytesIO(image_bytes))
        prompt = "Descreva detalhadamente o que você vê nesta imagem, de forma objetiva. Esta descrição será enviada em um e-mail para um supervisor, para que ele entenda o conteúdo da imagem sem precisar abri-la."
        
        response = model.generate_content([prompt, image_pil])
        return response.text
    except Exception as e:
        st.error(f"Erro ao contatar a API de IA: {e}")
        return None


def send_emails(image_bytes, image_name, collaborator_email, image_description):
    """
    Envia e-mails para o supervisor (com anexo e descrição) e para o colaborador (confirmação).
    """
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

# --- Interface do Streamlit ---

st.title("📤 App de Envio de Imagem com Análise de IA")
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
        st.image(image_bytes, caption=f"Imagem a ser enviada: {uploaded_file.name}", use_column_width=True)
        
        st.divider()
        st.subheader("🤖 Análise da Imagem por IA")
        
        with st.spinner("Analisando a imagem..."):
            ai_description = analyze_image_with_gemini(image_bytes)
        
        if ai_description:
            st.text_area("Descrição gerada:", value=ai_description, height=200, disabled=True)
            
            if st.button("🚀 Enviar para Supervisor", use_container_width=True):
                with st.spinner("Enviando e-mails, por favor aguarde..."):
                    success, message = send_emails(image_bytes, uploaded_file.name, collaborator_email, ai_description)
                
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)

    elif uploaded_file and not collaborator_email:
        st.warning("Por favor, insira seu e-mail para continuar.")

