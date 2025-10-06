# No arquivo: paginas/supervisor.py

import streamlit as st
from utils import conectar_firebase

db, _ = conectar_firebase()
colecao = 'ColecaoEnviados'

st.set_page_config(page_title="Painel do Supervisor", layout="wide")

if not (hasattr(st, "user") and getattr(st.user, "is_logged_in", False)):
    st.warning("Você precisa fazer login como supervisor para acessar esta página.")
    st.stop()

email_logado = getattr(st.user, "email", "").lower()
SUPERVISOR_EMAILS = ["thalestatasena@gmail.com"]

if email_logado not in SUPERVISOR_EMAILS:
    st.error("Acesso negado. Esta página é restrita a supervisores.")
    st.stop()

st.title("📊 Painel do Supervisor")
st.write("Visualize e aprove os envios realizados pelos colaboradores.")

def atualizar_status(colaborador_email, nome_arquivo, data_envio, novo_status):
    """Atualiza o status de um envio específico no Firestore."""
    try:
        doc_ref = db.collection(colecao).document(colaborador_email)
        doc = doc_ref.get()
        if doc.exists:
            dados = doc.to_dict()
            envios = dados.get("envios", [])
            
            # Encontra o envio correto para atualizar
            for envio in envios:
                if envio.get('nome_arquivo') == nome_arquivo and envio.get('data_envio') == data_envio:
                    envio['status'] = novo_status
                    break
            
            doc_ref.set(dados)
            return True
    except Exception as e:
        st.error(f"Erro ao atualizar status: {e}")
        return False

try:
    docs = db.collection(colecao).stream()
    colaboradores = [doc.id for doc in docs]
except Exception as e:
    st.error(f"Erro ao buscar colaboradores: {e}")
    colaboradores = []

if not colaboradores:
    st.info("Nenhum colaborador enviou imagens ainda.")
    st.stop()

st.sidebar.header("👥 Colaboradores")
colaborador_selecionado = st.sidebar.selectbox("Selecione um colaborador:", colaboradores)

if colaborador_selecionado:
    doc_ref = db.collection(colecao).document(colaborador_selecionado)
    doc = doc_ref.get()

    if doc.exists:
        dados = doc.to_dict()
        envios = dados.get("envios", [])

        if envios:
            st.subheader(f"📂 Histórico de {colaborador_selecionado}")
            
            envios_ordenados = sorted(
                [e for e in envios if 'data_envio' in e], 
                key=lambda x: x["data_envio"], 
                reverse=True
            )

            for i, envio in enumerate(envios_ordenados):
                data_formatada = envio['data_envio'].strftime('%d/%m/%Y %H:%M')
                status_atual = envio.get('status', 'Em processo')

                with st.expander(f"📎 {envio.get('nome_arquivo', 'Sem nome')} — {data_formatada}"):
                    st.write(f"**Status:** {status_atual}")
                    st.write("**Parecer da IA:**")
                    st.info(envio.get("descricao", "Nenhuma descrição."))
                    
                    if 'url_imagem' in envio:
                        st.image(envio['url_imagem'], caption="Imagem Enviada")
                    
                    # --- Botões de Aprovação/Reprovação ---
                    if status_atual == "Em processo":
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Aprovar", key=f"aprovar_{i}"):
                                if atualizar_status(colaborador_selecionado, envio['nome_arquivo'], envio['data_envio'], "Aprovado"):
                                    st.success("Status atualizado para Aprovado!")
                                    st.rerun()
                        with col2:
                            if st.button("❌ Reprovar", key=f"reprovar_{i}"):
                                if atualizar_status(colaborador_selecionado, envio['nome_arquivo'], envio['data_envio'], "Reprovado"):
                                    st.warning("Status atualizado para Reprovado!")
                                    st.rerun()
        else:
            st.info(f"O colaborador **{colaborador_selecionado}** ainda não enviou imagens.")
    else:
        st.warning(f"Nenhum dado encontrado para {colaborador_selecionado}.")
