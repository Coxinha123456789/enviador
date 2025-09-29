import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image
import io
import google.generativeai as genai

# --- Gerenciamento de Configurações e Segredos ---

# Inicializa as variáveis de configuração
GOOGLE_API_KEY = None
EMAIL_SENDER = None
EMAIL_PASSWORD = None
SUPERVISOR_EMAIL = None
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Tenta carregar as configurações do st.secrets (ideal para deploy)
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    SUPERVISOR_EMAIL = st.secrets["SUPERVISOR_EMAIL"]
    
    genai.configure(api_key=GOOGLE_API_KEY)

# Fallback para inputs manuais se secrets.toml não for encontrado (para desenvolvimento local)
except (FileNotFoundError, KeyError):
    st.sidebar.header("🔑 Configurações (Desenvolvimento Local)")
    st.sidebar.warning(
        "Arquivo de segredos não encontrado. "
        "Por favor, insira as informações abaixo para continuar."
    )
    
    st.sidebar.subheader("Configuração da IA")
    GOOGLE_API_KEY = st.sidebar.text_input(
        "Sua Google AI API Key:", 
        type="password", 
        help="Obtenha sua chave em https://aistudio.google.com/app/apikey"
    )
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)

    st.sidebar.subheader("Configuração de E-mail")
    EMAIL_SENDER = st.sidebar.text_input("Seu e-mail de envio:", placeholder="seu_email@exemplo.com")
    EMAIL_PASSWORD = st.sidebar.text_input("Sua senha de app:", type="password", help="Se usar Gmail com 2FA, gere uma 'Senha de App'.")
    SUPERVISOR_EMAIL = st.sidebar.text_input("E-mail do Supervisor:", placeholder="supervisor@exemplo.com")

# -----------------------------------------------------------------

def analyze_image_with_gemini(image_bytes):
    """
    Analisa uma imagem usando o Gemini (modelo Flash) e retorna uma descrição.
    """
    if not GOOGLE_API_KEY:
        return "Análise de IA desabilitada. Nenhuma chave de API fornecida."

    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        image_pil = Image.open(io.BytesIO(image_bytes))
        prompt = "Descreva o que você vê nesta imagem, de forma objetiva em mais ou menos um paragrafo de 2 linhas."
        
        response = model.generate_content([prompt, image_pil])
        return response.text
    except Exception as e:
        return f"Erro ao contatar a API de IA: {e}"


def send_emails(image_bytes, image_name, collaborator_email, image_description):
    """
    Função para enviar os e-mails para o supervisor (com anexo e descrição da IA) e para o colaborador (confirmação).
    """
    try:
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

st.set_page_config(layout="centered")
st.title("📤 App de Envio de Imagem com Análise de IA")

st.write("Faça o upload de uma imagem. Uma IA irá analisá-la e você poderá enviar a imagem com a descrição para seu supervisor.")

# Verifica se todas as configurações estão preenchidas
all_configs_set = all([GOOGLE_API_KEY, EMAIL_SENDER, EMAIL_PASSWORD, SUPERVISOR_EMAIL])
if not all_configs_set:
    st.warning("Faltam configurações na barra lateral. Por favor, preencha todas as informações para habilitar o envio.")


collaborator_email = st.text_input(
    "Digite seu e-mail para receber a confirmação:",
    placeholder="seu_email@exemplo.com"
)

uploaded_file = st.file_uploader(
    "Escolha uma imagem",
    type=["png", "jpg", "jpeg"],
    label_visibility="collapsed",
    disabled=not all_configs_set
)

if uploaded_file is not None and collaborator_email:
    image_bytes = uploaded_file.getvalue()
    image = Image.open(io.BytesIO(image_bytes))

    st.divider()
    st.subheader("🖼️ Visualização da Imagem")
    st.image(image, caption=f"Imagem a ser enviada: {uploaded_file.name}", use_column_width=True)
    
    st.divider()
    st.subheader("🤖 Análise da Imagem por IA (Gemini)")
    
    with st.spinner("Analisando a imagem com a IA..."):
        ai_description = analyze_image_with_gemini(image_bytes)
    st.text_area("Descrição gerada:", value=ai_description, height=200, help="Esta descrição será incluída no corpo do e-mail para o supervisor.")

    st.divider()

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

