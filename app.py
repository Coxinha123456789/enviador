import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image
import io

# --- Configuração de E-mail (PREENCHA COM SUAS INFORMAÇÕES) ---
# ATENÇÃO: É uma má prática de segurança colocar senhas diretamente no código.
# O ideal é usar variáveis de ambiente ou o sistema de secrets do Streamlit.
# Para mais informações: https://docs.streamlit.io/library/advanced-features/secrets-management
SMTP_SERVER = "smtp.gmail.com"  # Ex: "smtp.gmail.com" para o Gmail
SMTP_PORT = 587  # Porta do servidor SMTP (587 para TLS)
EMAIL_SENDER = "thalessena272006@gmail.com"  # Seu endereço de e-mail
EMAIL_PASSWORD = "nfqi xmey kbqx yfki"  # Use uma "senha de app" se usar Gmail com 2FA
SUPERVISOR_EMAIL = "ricardo8610@gmail.com"
# -----------------------------------------------------------------

def send_emails(image_bytes, image_name, collaborator_email):
    """
    Função para enviar os e-mails para o supervisor (com anexo) e para o colaborador (confirmação).
    """
    try:
        # Conectando ao servidor SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Habilita a segurança
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        # --- E-mail para o Supervisor ---
        msg_supervisor = MIMEMultipart()
        msg_supervisor['From'] = EMAIL_SENDER
        msg_supervisor['To'] = SUPERVISOR_EMAIL
        msg_supervisor['Subject'] = f"Nova Imagem Recebida de {collaborator_email}"

        # Corpo do e-mail do supervisor
        body_supervisor = f"Olá,\n\nUma nova imagem foi enviada pelo colaborador {collaborator_email}.\n\nA imagem está em anexo.\n\nAtenciosamente,\nSistema Automático"
        msg_supervisor.attach(MIMEText(body_supervisor, 'plain'))

        # Anexando a imagem
        image = MIMEImage(image_bytes, name=image_name)
        msg_supervisor.attach(image)

        # Enviando o e-mail do supervisor
        server.sendmail(EMAIL_SENDER, SUPERVISOR_EMAIL, msg_supervisor.as_string())

        # --- E-mail de Confirmação para o Colaborador ---
        msg_collaborator = MIMEMultipart()
        msg_collaborator['From'] = EMAIL_SENDER
        msg_collaborator['To'] = collaborator_email
        msg_collaborator['Subject'] = "Confirmação de Envio de Imagem"

        # Corpo do e-mail do colaborador
        body_collaborator = "Olá,\n\nEste é um e-mail de confirmação.\n\nSua imagem foi enviada com sucesso para o seu supervisor.\n\nAtenciosamente,\nSistema Automático"
        msg_collaborator.attach(MIMEText(body_collaborator, 'plain'))

        # Enviando o e-mail do colaborador
        server.sendmail(EMAIL_SENDER, collaborator_email, msg_collaborator.as_string())

        server.quit()
        return True, "E-mails enviados com sucesso!"

    except Exception as e:
        print(f"Erro ao enviar e-mails: {e}")
        return False, f"Ocorreu um erro ao enviar os e-mails: {e}"


# --- Interface do Streamlit ---

st.set_page_config(layout="centered")

st.title("📤 App de Envio de Imagem para Supervisão")

st.write("Faça o upload de uma imagem. Ela será exibida abaixo e você terá a opção de enviá-la para seu supervisor.")

# Input para o e-mail do colaborador
collaborator_email = st.text_input(
    "Digite seu e-mail para receber a confirmação:",
    placeholder="seu_email@exemplo.com"
)

# 1. Input da imagem
uploaded_file = st.file_uploader(
    "Escolha uma imagem",
    type=["png", "jpg", "jpeg"],
    label_visibility="collapsed"
)

# Verifica se um arquivo foi enviado e se o e-mail do colaborador foi preenchido
if uploaded_file is not None and collaborator_email:
    # Para garantir que a imagem possa ser lida várias vezes
    image_bytes = uploaded_file.getvalue()
    
    # Abrindo a imagem para exibição
    image = Image.open(io.BytesIO(image_bytes))

    st.divider()

    # 2. Exibição da imagem
    st.subheader("Visualização da Imagem")
    st.image(image, caption=f"Imagem a ser enviada: {uploaded_file.name}", use_column_width=True)

    st.info("A imagem acima será enviada como anexo para o seu supervisor.")

    # 3. Botão para enviar
    if st.button("🚀 Enviar para Supervisor", use_container_width=True):
        with st.spinner("Enviando e-mails, por favor aguarde..."):
            success, message = send_emails(image_bytes, uploaded_file.name, collaborator_email)
            if success:
                st.success(message)
                st.balloons()
            else:
                st.error(message)

elif uploaded_file and not collaborator_email:
    st.warning("Por favor, insira seu e-mail para continuar.")
