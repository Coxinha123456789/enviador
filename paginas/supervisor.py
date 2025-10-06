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
if not (hasattr(st, "user") and getattr(st.user, "is_logged_in", False)):
    st.warning("Você precisa fazer login como supervisor para acessar esta página.")
    st.stop()

email_logado = getattr(st.user, "email", "").lower()
SUPERVISOR_EMAILS = ["thalestatasena@gmail.com"]
if email_logado not in SUPERVISOR_EMAILS:
    st.error("Acesso negado. Esta página é restrita a supervisores.")
    st.stop()

# --- Funções (sem alterações) ---
def enviar_email_notificacao(colaborador_email, status, comentario, nome_arquivo):
    # ... (código da função) ...
    return True

def atualizar_status(colaborador_email, envio, novo_status, comentario):
    # ... (código da função) ...
    return True

def registrar_log_auditoria(colaborador_email, envio, acao):
    # ... (código da função) ...
    pass

# --- Inicialização do Estado ---
if 'confirmation' not in st.session_state:
    st.session_state.confirmation = None
if 'reveal_sensitive' not in st.session_state:
    st.session_state.reveal_sensitive = {}

# --- Layout da Página ---
st.title("🛠️ Gerenciar Envios")
st.write("Analise, aprove ou reprove os documentos pendentes com base no laudo técnico da IA.")
st.divider()

# --- Carregamento de Dados ---
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

# --- Exibição dos Envios ---
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
                    # --- CORREÇÃO APLICADA AQUI ---
                    # Lógica robusta para lidar com estruturas de dados antigas e novas
                    imagem_a_exibir = None
                    url_original = None

                    # Prioriza a nova estrutura de dados
                    if 'url_imagem_exibicao' in envio:
                        imagem_a_exibir = envio.get('url_imagem_exibicao')
                        url_original = envio.get('url_imagem_original')
                        if st.session_state.reveal_sensitive.get(item_id):
                            imagem_a_exibir = url_original
                    # Fallback para a estrutura antiga
                    elif 'url_imagem' in envio:
                        imagem_a_exibir = envio.get('url_imagem')

                    # Só exibe a imagem se uma URL válida foi encontrada
                    if imagem_a_exibir:
                        st.image(imagem_a_exibir, caption=f"Arquivo: {envio.get('nome_arquivo', 'N/A')}")
                    else:
                        st.warning("URL da imagem não encontrada para este envio.")
                    # --- FIM DA CORREÇÃO ---
                    
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
                    st.subheader(f"Análise de: {envio.get('tipo_documento', 'Documento Genérico')}")
                    laudo = envio.get('analise_ia')
                    
                    if laudo:
                        st.info(f"**Recomendação:** {laudo.get('parecer_supervisor', 'N/A')}")
                        with st.expander("Ver laudo de compliance detalhado"):
                            # ... (código do laudo) ...
                    elif 'descricao' in envio: # Compatibilidade com laudo antigo
                        st.info(f"**Parecer da IA (antigo):** {envio.get('descricao')}")
                    else:
                        st.warning("Não foi encontrado um laudo técnico da IA para este envio.")

                    st.divider()

                    # Lógica de confirmação e botões
                    if st.session_state.confirmation == item_id:
                        # ... (código da confirmação) ...
                        pass
                    
                    elif envio.get('status') == "Em processo":
                        # ... (código dos botões de ação) ...
                        pass
