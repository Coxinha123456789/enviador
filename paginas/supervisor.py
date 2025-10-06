# No arquivo: paginas/supervisor.py

import streamlit as st
from utils import conectar_firebase
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ... (conexão, verificação de acesso e funções de email/status) ...
db, _ = conectar_firebase()
colecao = 'ColecaoEnviados'
if not (hasattr(st, "user") and getattr(st.user, "is_logged_in", False)):
    st.warning("Você precisa fazer login como supervisor para acessar esta página.")
    st.stop()
email_logado = getattr(st.user, "email", "").lower()
SUPERVISOR_EMAILS = ["thalestatasena@gmail.com"]
if email_logado not in SUPERVISOR_EMAILS:
    st.error("Acesso negado. Esta página é restrita a supervisores.")
    st.stop()
def enviar_email_notificacao(colaborador_email, status, comentario, nome_arquivo):
    # ... (código da função) ...
    return True

def atualizar_status(colaborador_email, envio, novo_status, comentario):
    """Atualiza o status de um envio específico."""
    try:
        doc_ref = db.collection(colecao).document(colaborador_email)
        doc = doc_ref.get()
        if doc.exists:
            dados = doc.to_dict()
            envios = dados.get("envios", [])
            
            # Encontra o envio para atualizar usando a data de envio como identificador único
            for i, e in enumerate(envios):
                if e['data_envio'] == envio['data_envio']:
                    envios[i]['status'] = novo_status
                    novo_log = {
                        "status": f"{novo_status} pelo supervisor",
                        "timestamp": datetime.now(),
                        "comentario": comentario
                    }
                    envios[i].setdefault('log', []).append(novo_log)
                    break
            
            doc_ref.set(dados)
            enviar_email_notificacao(colaborador_email, novo_status, comentario, envio['nome_arquivo'])
            return True
    except Exception as e:
        st.error(f"Erro ao atualizar status: {e}")
        return False

def registrar_log_auditoria(colaborador_email, envio, acao):
    """Registra uma ação de auditoria no log do documento."""
    try:
        doc_ref = db.collection(colecao).document(colaborador_email)
        doc = doc_ref.get()
        if doc.exists:
            dados = doc.to_dict()
            envios = dados.get("envios", [])
            
            for i, e in enumerate(envios):
                if e['data_envio'] == envio['data_envio']:
                    novo_log = {
                        "status": acao,
                        "timestamp": datetime.now(),
                        "comentario": f"Realizado por: {email_logado}"
                    }
                    envios[i].setdefault('log', []).append(novo_log)
                    break
            doc_ref.set(dados)
    except Exception as e:
        st.error(f"Erro ao registrar log de auditoria: {e}")

if 'confirmation' not in st.session_state:
    st.session_state.confirmation = None
if 'reveal_sensitive' not in st.session_state:
    st.session_state.reveal_sensitive = {}

st.title("🛠️ Gerenciar Envios")
# ... (restante do código da página) ...
st.write("Analise, aprove ou reprove os documentos pendentes com base no laudo técnico da IA.")
st.divider()

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
            
            with st.container(border=True):
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    # Lógica de exibição de imagem (mascarada vs original)
                    imagem_a_exibir = envio.get('url_imagem_exibicao')
                    if st.session_state.reveal_sensitive.get(item_id):
                        imagem_a_exibir = envio.get('url_imagem_original')

                    st.image(imagem_a_exibir, caption=f"Arquivo: {envio.get('nome_arquivo', 'N/A')}")
                    
                    if envio.get("dados_mascarados"):
                        if not st.session_state.reveal_sensitive.get(item_id):
                            if st.button("🔒 Revelar Informação Sensível", key=f"reveal_{item_id}"):
                                st.session_state.reveal_sensitive[item_id] = True
                                registrar_log_auditoria(colaborador_email, envio, "Informação sensível revelada")
                                st.rerun()
                        else:
                            if st.button("👁️ Ocultar Informação Sensível", key=f"hide_{item_id}"):
                                st.session_state.reveal_sensitive[item_id] = False
                                st.rerun()

                with col2:
                    st.subheader(f"Análise de: {envio.get('tipo_documento', 'Documento')}")
                    laudo = envio.get('analise_ia')
                    
                    # ... (exibição do laudo e lógica de aprovação/reprovação) ...
                    if laudo:
                        st.info(f"**Recomendação:** {laudo.get('parecer_supervisor', 'N/A')}")
                        with st.expander("Ver laudo de compliance detalhado"):
                            for item in laudo.get("laudo_tecnico", []):
                                if item["cumprido"]:
                                    st.write(f"✅ **{item['requisito']}:** {item['observacao']}")
                                else:
                                    st.write(f"❌ **{item['requisito']}:** {item['observacao']}")
                    else:
                        st.warning("Não foi encontrado um laudo técnico da IA para este envio.")

                    st.divider()

                    if st.session_state.confirmation == item_id:
                        # ... (lógica de confirmação) ...
                        action_text = "aprovar" if st.session_state.action_status == "Aprovado" else "reprovar"
                        st.warning(f"Tem certeza que deseja **{action_text}** este item?")
                        
                        comentario = st.text_area("Adicionar comentário (obrigatório para reprovação):", key=f"comment_{item_id}", height=100)
                        
                        confirm_col1, confirm_col2, _ = st.columns([1, 1, 3])
                        
                        if confirm_col1.button("✅ Sim, confirmar", key=f"sim_{item_id}"):
                            if st.session_state.action_status == "Reprovado" and not comentario:
                                st.error("O comentário é obrigatório para reprovar um documento.")
                            else:
                                if atualizar_status(colaborador_email, envio, st.session_state.action_status, comentario):
                                    st.toast(f"Item marcado como {st.session_state.action_status}!", icon="🎉")
                                st.session_state.confirmation = None
                                st.rerun()

                        if confirm_col2.button("❌ Não, cancelar", key=f"nao_{item_id}"):
                            st.session_state.confirmation = None
                            st.rerun()
                    
                    elif envio.get('status') == "Em processo":
                        # ... (botões de ação) ...
                        action_col1, action_col2, _ = st.columns([1, 1, 3])
                        if action_col1.button("Aprovar", key=f"aprovar_{item_id}"):
                            st.session_state.confirmation = item_id
                            st.session_state.action_status = "Aprovado"
                            st.rerun()
                        if action_col2.button("Reprovar", key=f"reprovar_{item_id}"):
                            st.session_state.confirmation = item_id
                            st.session_state.action_status = "Reprovado"
                            st.rerun()
