# No arquivo: paginas/supervisor.py

import streamlit as st
from utils import conectar_firebase
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ... (Conexão e verificação de acesso permanecem iguais) ...
# --- Conexão com Firebase ---
db, _ = conectar_firebase()
colecao = 'ColecaoEnviados'

# --- Configuração da Página ---
st.set_page_config(page_title="Gerenciar Envios", layout="wide")

# --- Verificação de Acesso ---
if not (hasattr(st, "user") and getattr(st.user, "is_logged_in", False)):
    st.warning("Você precisa fazer login como supervisor para acessar esta página.")
    st.stop()

email_logado = getattr(st.user, "email", "").lower()
SUPERVISOR_EMAILS = ["thalestatasena@gmail.com"]

if email_logado not in SUPERVISOR_EMAILS:
    st.error("Acesso negado. Esta página é restrita a supervisores.")
    st.stop()

# --- Funções ---
def enviar_email_notificacao(colaborador_email, status, comentario, nome_arquivo):
    """Envia um e-mail de notificação de status para o colaborador."""
    try:
        EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
        EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = colaborador_email
        msg['Subject'] = f"Atualização de Status: Seu documento foi {status}"
        
        corpo = f"""
        Olá,

        O status do seu documento "{nome_arquivo}" foi atualizado para: **{status}**.

        Comentário do supervisor:
        --------------------------------------------------
        {comentario if comentario else "Nenhum comentário adicionado."}
        --------------------------------------------------

        Atenciosamente,
        Sistema Automático
        """
        msg.attach(MIMEText(corpo, 'plain'))
        server.sendmail(EMAIL_SENDER, colaborador_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Falha ao enviar e-mail de notificação: {e}")
        return False

def atualizar_status(colaborador_email, nome_arquivo, data_envio, novo_status, comentario):
    """Atualiza o status, adiciona ao log e envia notificação."""
    try:
        doc_ref = db.collection(colecao).document(colaborador_email)
        doc = doc_ref.get()
        if doc.exists:
            dados = doc.to_dict()
            envios = dados.get("envios", [])
            
            for envio in envios:
                if envio.get('nome_arquivo') == nome_arquivo and envio.get('data_envio').timestamp() == data_envio.timestamp():
                    envio['status'] = novo_status
                    novo_log = {
                        "status": f"{novo_status} pelo supervisor",
                        "timestamp": datetime.now(),
                        "comentario": comentario
                    }
                    envio.setdefault('log', []).append(novo_log)
                    break
            
            doc_ref.set(dados)
            enviar_email_notificacao(colaborador_email, novo_status, comentario, nome_arquivo)
            return True
    except Exception as e:
        st.error(f"Erro ao atualizar status: {e}")
        return False

# ... (Inicialização do estado e layout permanecem os mesmos) ...
if 'confirmation' not in st.session_state:
    st.session_state.confirmation = None

st.title("🛠️ Gerenciar Envios")
st.write("Analise, aprove ou reprove os documentos pendentes com base no laudo técnico da IA.")
st.divider()

# ... (Lógica para carregar colaboradores e filtrar) ...
try:
    docs = db.collection(colecao).stream()
    colaboradores = [doc.id for doc in docs]
except Exception as e:
    st.error(f"Erro ao buscar colaboradores: {e}")
    colaboradores = []

if not colaboradores:
    st.info("Nenhum colaborador realizou envios ainda.")
    st.stop()

st.sidebar.header("Filtros")
colaborador_selecionado = st.sidebar.selectbox("Selecione um colaborador:", options=["Todos"] + colaboradores)

# --- Exibição dos Dados ---
docs_para_exibir = []
if colaborador_selecionado == "Todos":
    docs_para_exibir = db.collection(colecao).stream()
else:
    doc = db.collection(colecao).document(colaborador_selecionado).get()
    if doc.exists:
        docs_para_exibir = [doc]
        
for doc in docs_para_exibir:
    colaborador_email = doc.id
    dados = doc.to_dict()
    envios = dados.get("envios", [])

    if envios:
        st.header(f"📂 Envios de: {colaborador_email}")
        envios_ordenados = sorted([e for e in envios if 'data_envio' in e], key=lambda x: x["data_envio"], reverse=True)

        for i, envio in enumerate(envios_ordenados):
            item_id = f"{colaborador_email}_{i}"
            data_envio_obj = envio['data_envio']
            status_atual = envio.get('status', 'Em processo')
            
            with st.container(border=True):
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    if 'url_imagem' in envio:
                        st.image(envio['url_imagem'], caption=f"Arquivo: {envio.get('nome_arquivo', 'N/A')}")

                with col2:
                    st.subheader("Parecer Técnico da IA")
                    laudo = envio.get('analise_ia')
                    
                    if laudo:
                        st.info(f"**Recomendação:** {laudo.get('parecer_supervisor', 'N/A')}")
                        with st.expander("Ver laudo de compliance detalhado (NT-RH-001)"):
                            for item in laudo.get("laudo_tecnico", []):
                                if item["cumprido"]:
                                    st.write(f"✅ **{item['requisito']}:** {item['observacao']}")
                                else:
                                    st.write(f"❌ **{item['requisito']}:** {item['observacao']}")
                    else:
                        st.warning("Não foi encontrado um laudo técnico da IA para este envio.")

                    st.divider()
                    
                    # ... (Lógica de confirmação e botões permanece a mesma) ...
                    if st.session_state.confirmation == item_id:
                        action_text = "aprovar" if st.session_state.action_status == "Aprovado" else "reprovar"
                        st.warning(f"Tem certeza que deseja **{action_text}** este item?")
                        
                        comentario = st.text_area("Adicionar comentário (obrigatório para reprovação):", key=f"comment_{item_id}", height=100)
                        
                        confirm_col1, confirm_col2, _ = st.columns([1, 1, 3])
                        
                        if confirm_col1.button("✅ Sim, confirmar", key=f"sim_{item_id}"):
                            if st.session_state.action_status == "Reprovado" and not comentario:
                                st.error("O comentário é obrigatório para reprovar um documento.")
                            else:
                                if atualizar_status(colaborador_email, envio['nome_arquivo'], data_envio_obj, st.session_state.action_status, comentario):
                                    st.toast(f"Item marcado como {st.session_state.action_status}!", icon="🎉")
                                st.session_state.confirmation = None
                                st.rerun()

                        if confirm_col2.button("❌ Não, cancelar", key=f"nao_{item_id}"):
                            st.session_state.confirmation = None
                            st.rerun()
                    
                    elif status_atual == "Em processo":
                        action_col1, action_col2, _ = st.columns([1, 1, 3])
                        if action_col1.button("Aprovar", key=f"aprovar_{item_id}"):
                            st.session_state.confirmation = item_id
                            st.session_state.action_status = "Aprovado"
                            st.rerun()
                        if action_col2.button("Reprovar", key=f"reprovar_{item_id}"):
                            st.session_state.confirmation = item_id
                            st.session_state.action_status = "Reprovado"
                            st.rerun()
