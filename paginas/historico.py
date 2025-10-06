# No arquivo: paginas/historico.py

import streamlit as st
from utils import conectar_firebase

st.set_page_config(page_title="Meu Histórico", layout="wide")

# --- Conexão com Firebase ---
db, _ = conectar_firebase()
colecao = 'ColecaoEnviados'

# --- Verificação de Login ---
if not (hasattr(st, "user") and getattr(st.user, "is_logged_in", False)):
    st.warning("Faça login para ver seu histórico.")
    st.stop()

collaborator_email = getattr(st.user, "email", "não identificado")

# --- Layout ---
st.title("📜 Meu Histórico de Envios")
st.write(f"Acompanhe o status dos documentos que você enviou, **{collaborator_email}**.")
st.divider()

# --- Busca os dados no Firestore ---
try:
    doc_ref = db.collection(colecao).document(collaborator_email)
    doc = doc_ref.get()

    if doc.exists:
        dados = doc.to_dict()
        envios = dados.get("envios", [])

        if envios:
            envios_ordenados = sorted(
                [e for e in envios if 'data_envio' in e],
                key=lambda x: x['data_envio'],
                reverse=True
            )

            # Exibe cada envio
            for envio in envios_ordenados:
                with st.container(border=True):
                    data_formatada = envio['data_envio'].strftime('%d/%m/%Y às %H:%M')
                    status = envio.get('status', 'Em processo')
                    
                    st.subheader(f"Enviado em: {data_formatada}")
                    
                    # Define cor e ícone com base no status
                    if status == 'Aprovado':
                        st.markdown(f"**Status:** <span style='color: #22c55e;'>🟢 Aprovado</span>", unsafe_allow_html=True)
                    elif status == 'Reprovado':
                        st.markdown(f"**Status:** <span style='color: #ef4444;'>🔴 Reprovado</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**Status:** <span style='color: #eab308;'>🟡 Em processo</span>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if 'url_imagem' in envio:
                            st.image(envio['url_imagem'], caption=envio.get('nome_arquivo', ''))
                    
                    with col2:
                        st.write("**Parecer da IA:**")
                        st.info(envio.get("descricao", "Nenhuma descrição."))
        else:
            st.info("Você ainda não enviou nenhum documento.")
    else:
        st.info("Você ainda não enviou nenhum documento.")

except Exception as e:
    st.error(f"Ocorreu um erro ao buscar seu histórico: {e}")
