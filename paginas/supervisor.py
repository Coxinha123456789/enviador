# No arquivo: paginas/supervisor.py

import streamlit as st
from utils import conectar_firebase
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- Conexão com Firebase e Configurações ---
db, _ = conectar_firebase()
colecao = 'ColecaoEnviados'
st.set_page_config(page_title="Gerenciar Envios", layout="wide")

# --- Verificação de Acesso ---
# CORREÇÃO APLICADA AQUI: trocado st por st.user
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
        corpo = f"""Olá,\n\nO status do seu documento "{nome_arquivo}" foi atualizado para: **{status}**.\n\nComentário do supervisor:\n--------------------------------------------------\n{comentario if comentario else "Nenhum comentário adicionado."}\n--------------------------------------------------\n\nAtenciosamente,\nSistema Automático"""
        msg.attach(MIMEText(corpo, 'plain'))
        server.sendmail(EMAIL_SENDER, colaborador_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Falha ao enviar e-mail de notificação: {e}")
        return False

def atualizar_status(colaborador_email, envio, novo_status, comentario):
    try:
        doc_ref = db.collection(colecao).document(colaborador_email)
        doc = doc_ref.get()
        if doc.exists:
            dados = doc.to_dict()
            envios = dados.get("envios", [])
            for i, e in enumerate(envios):
                if e['data_envio'] == envio['data_envio']:
                    envios[i]['status'] = novo_status
                    novo_log = {"status": f"{novo_status} pelo supervisor", "timestamp": datetime.now(), "comentario": comentario}
                    envios[i].setdefault('log', []).append(novo_log)
                    break
            doc_ref.set(dados)
            enviar_email_notificacao(colaborador_email, novo_status, comentario, envio['nome_arquivo'])
            return True
    except Exception as e:
        st.error(f"Erro ao atualizar status: {e}")
        return False

def registrar_log_auditoria(colaborador_email, envio, acao):
    try:
        doc_ref = db.collection(colecao).document(colaborador_email)
        doc = doc_ref.get()
        if doc.exists:
            dados = doc.to_dict()
            envios = dados.get("envios", [])
            for i, e in enumerate(envios):
                if e['data_envio'] == envio['data_envio']:
                    novo_log = {"status": acao, "timestamp": datetime.now(), "comentario": f"Realizado por: {email_logado}"}
                    envios[i].setdefault('log', []).append(novo_log)
                    break
            doc_ref.set(dados)
    except Exception as e:
        st.error(f"Erro ao registrar log de auditoria: {e}")

# --- Restante do código (sem alterações) ... ---
if 'confirmation' not in st.session_state:
    st.session_state.confirmation = None
if 'reveal_sensitive' not in st.session_state:
    st.session_state.reveal_sensitive = {}

st.title("🛠️ Gerenciar Envios")
st.write("Analise, aprove ou reprove os documentos pendentes com base no laudo técnico da IA.")
st.divider()

try:
    docs = db.collection(colecao).stream()
    colaboradores = [doc.id for doc in docs]
except Exception as e:
    st.error(f"Erro ao buscar colaboradores: {e}")
    colaboradores = []

if not colaboradores
