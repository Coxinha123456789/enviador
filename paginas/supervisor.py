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
st.write("Visualize os envios realizados pelos colaboradores.")

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

            for envio in envios_ordenados:
                data_formatada = envio['data_envio'].strftime('%d/%m/%Y %H:%M')
                with st.expander(f"📎 {envio.get('nome_arquivo', 'Sem nome')} — {data_formatada}"):
                    st.write("**Descrição da IA:**")
                    st.write(envio.get("descricao", "Nenhuma descrição."))
                    
                    # Mostra a imagem a partir da URL salva
                    if 'url_imagem' in envio:
                        st.image(envio['url_imagem'], caption="Imagem Enviada")

        else:
            st.info(f"O colaborador **{colaborador_selecionado}** ainda não enviou imagens.")
    else:
        st.warning(f"Nenhum dado encontrado para {colaborador_selecionado}.")
