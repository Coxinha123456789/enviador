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
import json

st.set_page_config(layout="centered", page_title="Envio de Documentos")

# --- REGULAMENTO INTERNO DA EMPRESA ---
REGULAMENTO_ATESTADOS = """
NORMA TÉCNICA NT-RH-001 - VALIDAÇÃO DE ATESTADOS MÉDICOS

Art. 1º - Clareza e Legibilidade:
    a. O atestado deve estar perfeitamente legível, sem rasuras, borrões ou emendas que comprometam a verificação das informações.
    b. A imagem digitalizada ou foto deve ter alta resolução, permitindo a leitura de todos os campos.

Art. 2º - Informações do Colaborador:
    a. O nome completo do colaborador deve estar presente e ser idêntico ao registrado no sistema da empresa.

Art. 3º - Informações do Profissional de Saúde:
    a. O nome completo do médico ou profissional de saúde emissor deve estar legível.
    b. O número de registro no conselho profissional (CRM, CRO, etc.) deve estar claro, válido e acompanhado da sigla do estado.
    c. Carimbo e assinatura do profissional devem estar presentes e nítidos.

Art. 4º - Informações sobre o Afastamento:
    a. A data de emissão do atestado deve ser explícita.
    b. O período de afastamento recomendado (início, fim e/ou total de dias) deve ser claramente informado.
    c. O Código Internacional de Doenças (CID) é opcional. Se presente, deve ser legível.

Art. 5º - Autenticidade e Validade:
    a. O atestado não deve apresentar indícios de adulteração ou montagem digital.
    b. A data de emissão do atestado não pode ser futura.
"""

def analyze_compliance_with_gemini(image_bytes):
    """
    Analisa a imagem de um atestado contra o regulamento da empresa, atuando como um auditor de compliance.
    Retorna um laudo técnico estruturado em JSON.
    """
    try:
        # Recomendo usar um modelo mais robusto para esta tarefa
        model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest') 
        image_pil = Image.open(io.BytesIO(image_bytes))
        
        prompt = f"""
        Você é um especialista em compliance do departamento de RH. Sua tarefa é analisar a imagem de um atestado médico e validá-la rigorosamente contra a norma interna da empresa.

        **Norma Interna de Referência:**
        ---
        {REGULAMENTO_ATESTADOS}
        ---

        **Instruções:**
        1. Analise a imagem fornecida.
        2. Verifique CADA item do regulamento.
        3. Retorne SUA RESPOSTA EXCLUSIVAMENTE EM FORMATO JSON, sem nenhum texto ou formatação adicional antes ou depois.

        **Estrutura do JSON de Saída:**
        {{
          "status_geral": "CONFORME" | "NAO_CONFORME",
          "laudo_tecnico": [
            {{"requisito": "Art. 1º (a) - Legibilidade", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 1º (b) - Resolução da imagem", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 2º (a) - Nome do colaborador", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 3º (a) - Nome do profissional", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 3º (b) - Registro profissional (CRM)", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 3º (c) - Carimbo e Assinatura", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 4º (a) - Data de emissão", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 4º (b) - Período de afastamento", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 5º (a) - Indícios de adulteração", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 5º (b) - Data de emissão não futura", "cumprido": boolean, "observacao": "string"}}
          ],
          "parecer_supervisor": "string com um resumo técnico e recomendação para o supervisor."
        }}

        **Exemplo de 'observacao':** "Requisito cumprido. O nome está legível." ou "Requisito NÃO CUMPRIDO. O número do CRM está parcialmente apagado."
        **Exemplo de 'parecer_supervisor':** "O documento atende a todos os critérios da NT-RH-001. Recomenda-se a aprovação." ou "O documento não cumpre com os Artigos 3(b) e 3(c) da NT-RH-001 devido à ausência de CRM e assinatura. Recomenda-se a reprovação e contato com o colaborador."
        """
        
        response = model.generate_content([prompt, image_pil])
        
        # Limpa a resposta para garantir que seja um JSON válido
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)

    except Exception as e:
        st.error(f"Erro ao contatar ou processar a resposta da IA: {e}")
        return None

# ... (Suas funções send_emails e upload_to_firebase_storage permanecem as mesmas) ...
def send_emails(sender, password, supervisor, collaborator, subject, body, image_bytes, image_name):
    """Envia e-mails para o supervisor (com anexo) e colaborador (confirmação)."""
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)

        # E-mail para o Supervisor
        msg_supervisor = MIMEMultipart()
        msg_supervisor['From'] = sender
        msg_supervisor['To'] = supervisor
        msg_supervisor['Subject'] = subject
        msg_supervisor.attach(MIMEText(body, 'plain'))
        image = MIMEImage(image_bytes, name=image_name)
        msg_supervisor.attach(image)
        server.sendmail(sender, supervisor, msg_supervisor.as_string())

        # E-mail de Confirmação para o Colaborador
        msg_collaborator = MIMEMultipart()
        msg_collaborator['From'] = sender
        msg_collaborator['To'] = collaborator
        msg_collaborator['Subject'] = "Confirmação de Envio de Documento"
        body_collaborator = "Olá,\n\nSeu documento e a análise da IA foram enviados com sucesso para seu supervisor. Você será notificado sobre o status assim que for avaliado.\n\nAtenciosamente,\nSistema Automático"
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
# ... (Carregamento de segredos) ...
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
st.title("📤 Envio de Documentos para Validação")
st.write("Esta ferramenta fará uma pré-validação do seu documento com base na Norma Técnica NT-RH-001.")
st.divider()

with st.expander("Clique para ver a NT-RH-001 - Regras para Atestados"):
    st.code(REGULAMENTO_ATESTADOS, language='text')

uploaded_file = st.file_uploader(
    "Selecione o arquivo de imagem do atestado", 
    type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    image_bytes = uploaded_file.getvalue()
    st.image(image_bytes, caption=f"Arquivo: {uploaded_file.name}", use_container_width=True)
    st.divider()

    if st.button("🔍 Validar Documento", use_container_width=True):
        with st.spinner("Realizando auditoria de compliance com a IA... Isso pode levar um momento."):
            laudo_ia = analyze_compliance_with_gemini(image_bytes)
            st.session_state['laudo_ia'] = laudo_ia

if 'laudo_ia' in st.session_state and st.session_state['laudo_ia']:
    laudo = st.session_state['laudo_ia']
    
    st.subheader("Resultado da Validação (NT-RH-001)")
    
    with st.container(border=True):
        for item in laudo.get("laudo_tecnico", []):
            if item["cumprido"]:
                st.success(f"**{item['requisito']}:** {item['observacao']}", icon="✅")
            else:
                st.error(f"**{item['requisito']}:** {item['observacao']}", icon="❌")
    
    st.divider()
    
    if laudo["status_geral"] == "CONFORME":
        st.success("✅ **Documento em conformidade!** Todos os requisitos obrigatórios foram comprovados. Você já pode enviar para o seu supervisor.")
        pode_enviar = True
    else:
        st.error("❌ **Documento não conforme.** Alguns requisitos da NT-RH-001 não foram cumpridos. Verifique as observações acima e, se necessário, envie um novo arquivo.", icon="⚠️")
        pode_enviar = False

    if pode_enviar:
        if st.button("🚀 Enviar para Supervisor", use_container_width=True, type="primary"):
            with st.spinner("Enviando e salvando..."):
                image_url = upload_to_firebase_storage(image_bytes, collaborator_email, uploaded_file.name)
                
                if image_url:
                    email_subject = f"Novo Documento para Aprovação de {collaborator_email}"
                    parecer_supervisor = laudo.get("parecer_supervisor", "Não foi possível gerar um parecer.")
                    
                    email_body = f"""
                    Olá, Supervisor,

                    Um novo documento foi enviado por {collaborator_email} e pré-validado pelo sistema de IA.

                    **Parecer Técnico da IA (baseado na NT-RH-001):**
                    --------------------------------------------------
                    {parecer_supervisor}
                    --------------------------------------------------

                    Acesse o painel para visualizar os detalhes completos e tomar uma ação.

                    Atenciosamente,
                    Sistema Automático de Validação
                    """
                    
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
                                "analise_ia": laudo, # Salva o laudo completo
                                "nome_arquivo": uploaded_file.name,
                                "data_envio": datetime.now(),
                                "url_imagem": image_url,
                                "status": "Em processo",
                                "log": [
                                    {
                                        "status": "Enviado pelo colaborador",
                                        "timestamp": datetime.now(),
                                        "comentario": "Validação inicial da IA: CONFORME"
                                    }
                                ]
                            }
                            
                            dados.setdefault('envios', []).append(novo_envio)
                            user_ref.set(dados)

                            st.success(f"{email_msg} Registro salvo com sucesso!")
                            st.toast("🚀 Enviado com sucesso!", icon="🚀")
                            st.balloons()
                            del st.session_state['laudo_ia'] # Limpa o estado após o envio
                        except Exception as e:
                            st.error(f"E-mails enviados, mas falha ao salvar o registro: {e}")
                    else:
                        st.error(f"Falha no envio de e-mails: {email_msg}")
