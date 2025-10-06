# No arquivo: paginas/pagina1.py

import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image, ImageFilter
import io
import google.generativeai as genai
from datetime import datetime
from utils import conectar_firebase
import json

st.set_page_config(layout="centered", page_title="Envio de Documentos")

# --- BANCO DE REGRAS E PROMPTS POR TIPO DE DOCUMENTO ---

DOCUMENT_RULES = {
    "Atestado Médico": {
        "norma_id": "NT-RH-001",
        "regulamento": """
NORMA TÉCNICA NT-RH-001 - VALIDAÇÃO DE ATESTADOS MÉDICOS
Art. 1º - Legibilidade: O documento deve ser legível, sem rasuras. A imagem deve ter boa resolução.
Art. 2º - Identificação do Colaborador: O nome completo do colaborador deve estar visível.
Art. 3º - Identificação do Profissional: Nome, CRM, carimbo e assinatura do médico devem estar presentes.
Art. 4º - Detalhes do Afastamento: Data de emissão e período de afastamento devem ser claros.
Art. 5º - Autenticidade: O documento não pode ter indícios de adulteração ou data futura. O CID é um dado sensível.
""",
        "prompt_ia": """
        Você é um auditor de compliance de RH. Valide a imagem de um Atestado Médico contra a NT-RH-001.
        Sua tarefa é dupla:
        1.  Validar cada requisito da norma.
        2.  Identificar a localização (bounding box) de dados sensíveis, especificamente o CID.

        Retorne SUA RESPOSTA EXCLUSIVAMENTE EM FORMATO JSON.

        Estrutura do JSON:
        {{
          "status_geral": "CONFORME" | "NAO_CONFORME",
          "laudo_tecnico": [
            {{"requisito": "Art. 1º - Legibilidade", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 2º - Identificação do Colaborador", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 3º - Identificação do Profissional", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 4º - Detalhes do Afastamento", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 5º - Autenticidade", "cumprido": boolean, "observacao": "string"}}
          ],
          "dados_sensiveis": {{
            "cid_bbox": [x_min, y_min, x_max, y_max]
          }},
          "parecer_supervisor": "string com um resumo técnico e recomendação para o supervisor."
        }}
        Se o CID não for encontrado, retorne [0,0,0,0] para "cid_bbox".
        """
    },
    "Recibo para Reembolso": {
        "norma_id": "NT-FIN-001",
        "regulamento": """
NORMA TÉCNICA NT-FIN-001 - VALIDAÇÃO DE RECIBOS PARA REEMBOLSO
Art. 1º - Legibilidade: O recibo deve ser legível e a imagem de boa qualidade.
Art. 2º - Dados do Prestador: Nome/Razão Social e CNPJ/CPF do prestador de serviço devem estar claros.
Art. 3º - Dados do Pagamento: Data da despesa, descrição detalhada dos itens/serviços e o valor total devem ser explícitos.
Art. 4º - Validade: O recibo deve ser um documento fiscal válido (Nota Fiscal, cupom, etc.) e não pode ter rasuras.
""",
        "prompt_ia": """
        Você é um auditor de compliance do departamento Financeiro. Valide a imagem de um Recibo contra a NT-FIN-001.
        Retorne SUA RESPOSTA EXCLUSIVAMENTE EM FORMATO JSON.

        Estrutura do JSON:
        {{
          "status_geral": "CONFORME" | "NAO_CONFORME",
          "laudo_tecnico": [
            {{"requisito": "Art. 1º - Legibilidade", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 2º - Dados do Prestador", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 3º - Dados do Pagamento", "cumprido": boolean, "observacao": "string"}},
            {{"requisito": "Art. 4º - Validade", "cumprido": boolean, "observacao": "string"}}
          ],
          "dados_sensiveis": {{}},
          "parecer_supervisor": "string com um resumo técnico e recomendação para o supervisor."
        }}
        """
    }
}


# --- Funções ---

def mask_sensitive_data(image_bytes, bbox):
    """Aplica um desfoque na área do bounding box."""
    if not bbox or sum(bbox) == 0:
        return image_bytes, False # Retorna imagem original se não houver bbox

    try:
        image = Image.open(io.BytesIO(image_bytes))
        # A IA pode retornar as coordenadas relativas ao tamanho da imagem
        x_min, y_min, x_max, y_max = bbox

        # Garante que as coordenadas estão dentro dos limites da imagem
        x_min = max(0, x_min)
        y_min = max(0, y_min)
        x_max = min(image.width, x_max)
        y_max = min(image.height, y_max)

        if x_max > x_min and y_max > y_min:
            crop_area = image.crop((x_min, y_min, x_max, y_max))
            # Aplica um desfoque pesado
            blurred_crop = crop_area.filter(ImageFilter.GaussianBlur(radius=20))
            image.paste(blurred_crop, (x_min, y_min, x_max, y_max))

            # Salva a imagem modificada em bytes
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return buffer.getvalue(), True
        return image_bytes, False
    except Exception as e:
        st.warning(f"Não foi possível aplicar o mascaramento de dados: {e}")
        return image_bytes, False

def analyze_document_with_gemini(image_bytes, doc_type):
    """Chama a IA com o prompt correto para o tipo de documento."""
    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        image_pil = Image.open(io.BytesIO(image_bytes))
        prompt = DOCUMENT_RULES[doc_type]["prompt_ia"]
        
        response = model.generate_content([prompt, image_pil])
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)
    except Exception as e:
        st.error(f"Erro ao processar a resposta da IA: {e}")
        return None

# ... (outras funções como send_emails, upload_to_firebase_storage permanecem iguais) ...
def send_emails(sender, password, supervisor, collaborator, subject, body, image_bytes, image_name):
    # ... (código de envio de email) ...
    return True, "E-mails enviados com sucesso!"

def upload_to_firebase_storage(image_bytes, user_email, file_name, is_masked=False):
    """Faz o upload da imagem e retorna a URL pública."""
    try:
        _, bucket = conectar_firebase()
        suffix = "_masked" if is_masked else "_original"
        # Adiciona um timestamp para evitar sobreescrever arquivos com mesmo nome
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        path = f"images/{user_email}/{timestamp}_{file_name}{suffix}"
        
        blob = bucket.blob(path)
        blob.upload_from_string(image_bytes, content_type='image/png')
        blob.make_public()
        return blob.public_url
    except Exception as e:
        st.error(f"Erro ao fazer upload para o Firebase Storage: {e}")
        return None

# --- LÓGICA PRINCIPAL ---
# ... (conexão com firebase, carregamento de segredos e login) ...
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

if not (hasattr(st, "user") and st.user.is_logged_in):
    st.warning("Faça login para continuar.")
    st.stop()

collaborator_email = getattr(st.user, "email", "não identificado")

st.title("📤 Plataforma de Envio de Documentos")
st.write("Selecione o tipo de documento para iniciar a validação.")

doc_type_selected = st.selectbox(
    "**1. Qual tipo de documento você deseja enviar?**",
    options=list(DOCUMENT_RULES.keys()),
    index=None,
    placeholder="Selecione uma opção"
)

if doc_type_selected:
    norma = DOCUMENT_RULES[doc_type_selected]
    st.info(f"O documento será validado contra a norma **{norma['norma_id']}**.")
    with st.expander(f"Clique para ver a {norma['norma_id']}"):
        st.code(norma['regulamento'], language='text')

    uploaded_file = st.file_uploader(
        "**2. Selecione o arquivo de imagem**",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_file:
        image_bytes = uploaded_file.getvalue()
        st.image(image_bytes, caption=f"Arquivo: {uploaded_file.name}", use_container_width=True)

        if st.button("🔍 Validar Documento", use_container_width=True):
            with st.spinner("Realizando auditoria de compliance..."):
                laudo_ia = analyze_document_with_gemini(image_bytes, doc_type_selected)
                st.session_state['laudo_ia'] = laudo_ia
                st.session_state['image_bytes'] = image_bytes
                st.session_state['doc_type'] = doc_type_selected
                st.session_state['file_name'] = uploaded_file.name
        
if 'laudo_ia' in st.session_state and st.session_state.get('laudo_ia'):
    laudo = st.session_state['laudo_ia']
    image_bytes = st.session_state['image_bytes']
    doc_type = st.session_state['doc_type']
    file_name = st.session_state['file_name']

    st.subheader(f"Resultado da Validação ({DOCUMENT_RULES[doc_type]['norma_id']})")
    
    with st.container(border=True):
        # ... (exibição do laudo) ...
        for item in laudo.get("laudo_tecnico", []):
            if item["cumprido"]:
                st.success(f"**{item['requisito']}:** {item['observacao']}", icon="✅")
            else:
                st.error(f"**{item['requisito']}:** {item['observacao']}", icon="❌")

    if st.button("🚀 Enviar para Supervisor", use_container_width=True, type="primary"):
        with st.spinner("Processando e salvando..."):
            
            # Mascaramento de dados se necessário
            masked_image_bytes, was_masked = mask_sensitive_data(
                image_bytes, 
                laudo.get("dados_sensiveis", {}).get("cid_bbox")
            )

            # Upload da imagem original e da mascarada
            original_url = upload_to_firebase_storage(image_bytes, collaborator_email, file_name, is_masked=False)
            masked_url = upload_to_firebase_storage(masked_image_bytes, collaborator_email, file_name, is_masked=True) if was_masked else original_url

            if original_url and masked_url:
                # ... (lógica de envio de email e salvamento no firebase) ...
                user_ref = db.collection(colecao).document(collaborator_email)
                doc = user_ref.get()
                dados = doc.to_dict() if doc.exists else {}

                novo_envio = {
                    "analise_ia": laudo,
                    "nome_arquivo": file_name,
                    "tipo_documento": doc_type,
                    "data_envio": datetime.now(),
                    "url_imagem_exibicao": masked_url, # URL a ser mostrada por padrão
                    "url_imagem_original": original_url, # URL segura
                    "dados_mascarados": was_masked,
                    "status": "Em processo",
                    "log": [
                        {
                            "status": "Enviado pelo colaborador",
                            "timestamp": datetime.now(),
                            "comentario": f"Validação IA: {laudo.get('status_geral')}"
                        }
                    ]
                }
                dados.setdefault('envios', []).append(novo_envio)
                user_ref.set(dados)

                st.success("Documento enviado com sucesso!")
                st.balloons()
                # Limpa o estado para um novo envio
                for key in ['laudo_ia', 'image_bytes', 'doc_type', 'file_name']:
                    if key in st.session_state:
                        del st.session_state[key]
