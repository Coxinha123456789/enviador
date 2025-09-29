import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from PIL import Image
import io
import google.generativeai as genai
import pyrebase
import datetime

# --- Configuração da Página ---
st.set_page_config(layout="wide")

# --- Gerenciamento de Configurações e Segredos ---

# Tenta carregar as configurações do st.secrets (ideal para deploy)
try:
    # Google Gemini API
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)

    # Email
    EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    # Firebase
    firebase_config = st.secrets["firebase"]
    firebase = pyrebase.initialize_app(firebase_config)
    auth = firebase.auth()
    db = firebase.database()
    storage = firebase.storage()
    
    CONFIG_LOADED = True

# Fallback para inputs manuais se secrets.toml não for encontrado (para desenvolvimento local)
except (FileNotFoundError, KeyError):
    st.error("Arquivo de segredos não configurado para deploy. Use a barra lateral para configurações locais.")
    CONFIG_LOADED = False


# --- Funções Auxiliares (Firebase, IA, Email) ---

def analyze_image_with_gemini(image_bytes):
    """Analisa uma imagem usando o Gemini e retorna uma descrição."""
    if not GOOGLE_API_KEY:
        return "Análise de IA desabilitada. Nenhuma chave de API fornecida."
    try:
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        image_pil = Image.open(io.BytesIO(image_bytes))
        prompt = "Descreva detalhadamente o que você vê nesta imagem, de forma objetiva. Esta descrição será enviada em um e-mail para um supervisor, para que ele entenda o conteúdo da imagem sem precisar abri-la."
        response = model.generate_content([prompt, image_pil])
        return response.text
    except Exception as e:
        return f"Erro ao contatar a API de IA: {e}"

def send_notification_email(supervisor_email, employee_email, image_description):
    """Envia um e-mail de notificação para o supervisor."""
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = supervisor_email
        msg['Subject'] = f"Nova Imagem Recebida de {employee_email}"

        body = f"""Olá,

O colaborador {employee_email} enviou uma nova imagem para sua avaliação.

Abaixo está uma descrição da imagem gerada por IA:
--------------------------------------------------
{image_description}
--------------------------------------------------

Por favor, acesse o dashboard para visualizar a imagem e tomar as ações necessárias.

Atenciosamente,
Sistema Automático"""
        msg.attach(MIMEText(body, 'plain'))
        server.sendmail(EMAIL_SENDER, supervisor_email, msg.as_string())
        server.quit()
        return True, "Notificação enviada com sucesso!"
    except Exception as e:
        return False, f"Ocorreu um erro ao enviar o e-mail de notificação: {e}"


# --- Lógica de Interface (UI) ---

def render_login_page():
    """Renderiza a página de login."""
    st.title("Bem-vindo ao Portal de Imagens")
    st.write("Por favor, faça o login para continuar.")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        submit_button = st.form_submit_button("Entrar")

        if submit_button:
            if not email or not password:
                st.error("Por favor, preencha o email e a senha.")
                return

            try:
                with st.spinner("Autenticando..."):
                    user = auth.sign_in_with_email_and_password(email, password)
                    user_info = db.child("users").child(user['localId']).get().val()
                    
                    st.session_state['user'] = user
                    st.session_state['user_info'] = user_info
                    st.success("Login realizado com sucesso!")
                    st.rerun() # Re-executa o script para ir para o dashboard

            except Exception as e:
                st.error(f"Falha no login. Verifique suas credenciais. Detalhe: {e}")

def render_employee_dashboard():
    """Renderiza o dashboard do funcionário."""
    st.title(f"Dashboard do Funcionário: {st.session_state['user_info']['name']}")
    st.write("Aqui você pode enviar imagens para seu supervisor e ver seu histórico de envios.")
    
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

    # --- Seção de Upload ---
    st.header("📤 Enviar Nova Imagem")
    uploaded_file = st.file_uploader("Escolha uma imagem", type=["png", "jpg", "jpeg"])
    
    if uploaded_file:
        image_bytes = uploaded_file.getvalue()
        st.image(image_bytes, caption="Imagem a ser enviada", width=300)

        if st.button("Analisar e Enviar para Supervisor"):
            with st.spinner("Analisando imagem com IA..."):
                description = analyze_image_with_gemini(image_bytes)
            st.text_area("Descrição Gerada pela IA:", value=description, height=150, disabled=True)
            
            with st.spinner("Enviando imagem e dados..."):
                # 1. Enviar para o Storage
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                user_id = st.session_state['user']['localId']
                file_path_on_storage = f"images/{user_id}/{timestamp}_{uploaded_file.name}"
                storage.child(file_path_on_storage).put(image_bytes)
                image_url = storage.child(file_path_on_storage).get_url()

                # 2. Salvar dados no Realtime Database/Firestore
                supervisor_id = st.session_state['user_info']['supervisor_id']
                supervisor_info = db.child("users").child(supervisor_id).get().val()

                image_data = {
                    "employee_id": user_id,
                    "employee_email": st.session_state['user_info']['email'],
                    "supervisor_id": supervisor_id,
                    "image_url": image_url,
                    "description": description,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "status": "pending"
                }
                db.child("images").push(image_data)
                
                # 3. Enviar notificação por e-mail
                send_notification_email(supervisor_info['email'], st.session_state['user_info']['email'], description)

            st.success("Imagem enviada com sucesso para o supervisor!")
            st.balloons()
    
    # --- Seção de Histórico ---
    st.divider()
    st.header("📜 Histórico de Envios")
    
    with st.spinner("Carregando histórico..."):
        all_images = db.child("images").order_by_child("employee_id").equal_to(st.session_state['user']['localId']).get().val()
        if not all_images:
            st.info("Você ainda não enviou nenhuma imagem.")
        else:
            # Ordena por data (mais recente primeiro)
            sorted_images = sorted(all_images.items(), key=lambda item: item[1]['timestamp'], reverse=True)
            for _, image in sorted_images:
                with st.expander(f"Enviado em: {datetime.datetime.fromisoformat(image['timestamp']).strftime('%d/%m/%Y %H:%M')} - Status: {image['status']}"):
                    st.image(image['image_url'], width=200)
                    st.write("**Descrição da IA:**")
                    st.write(image['description'])

def render_supervisor_dashboard():
    """Renderiza o dashboard do supervisor."""
    st.title(f"Dashboard do Supervisor: {st.session_state['user_info']['name']}")
    st.write("Visualize e gerencie as imagens enviadas pelos funcionários.")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
    
    with st.spinner("Carregando imagens pendentes..."):
        supervisor_id = st.session_state['user']['localId']
        pending_images = db.child("images").order_by_child("supervisor_id").equal_to(supervisor_id).get().val()
        
        if not pending_images:
            st.success("🎉 Nenhuma imagem pendente para revisão!")
            return

        # Filtra apenas as pendentes
        pending_list = {k: v for k, v in pending_images.items() if v.get('status', 'pending') == 'pending'}

        if not pending_list:
            st.success("🎉 Nenhuma imagem pendente para revisão!")
            return

        st.subheader(f"Você tem {len(pending_list)} imagem(ns) para revisar.")
        
        # Ordena por data (mais recente primeiro)
        sorted_images = sorted(pending_list.items(), key=lambda item: item[1]['timestamp'], reverse=True)

        for image_key, image in sorted_images:
            st.divider()
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(image['image_url'], caption=f"Enviado por: {image['employee_email']}")
            with col2:
                st.write(f"**Data de Envio:** {datetime.datetime.fromisoformat(image['timestamp']).strftime('%d/%m/%Y %H:%M')}")
                st.write("**Descrição da IA:**")
                st.caption(image['description'])
                if st.button("Marcar como Visualizado", key=image_key):
                    db.child("images").child(image_key).update({"status": "viewed"})
                    st.success("Status atualizado!")
                    st.rerun()


# --- Lógica Principal (Router) ---

if not CONFIG_LOADED:
    st.stop()

if 'user' not in st.session_state:
    render_login_page()
else:
    user_role = st.session_state.get('user_info', {}).get('role')
    if user_role == 'employee':
        render_employee_dashboard()
    elif user_role == 'supervisor':
        render_supervisor_dashboard()
    else:
        st.error("Seu usuário não tem um papel ('role') definido no banco de dados. Contate o administrador.")
        if st.button("Fazer Logout"):
            st.session_state.clear()
            st.rerun()

