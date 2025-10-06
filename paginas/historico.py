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
st.write(f"Aqui estão todas as imagens que você, **{collaborator_email}**, já enviou.")

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

            for envio in envios_ordenados:
                data_formatada = envio['data_envio'].strftime('%d/%m/%Y %H:%M')
                status = envio.get('status', 'Em processo') # Pega o status, com 'Em processo' como padrão
                
                # Define cor e ícone com base no status
                if status == 'Aprovado':
                    status_display = f"Status: 🟢 **{status}**"
                elif status == 'Reprovado':
                    status_display = f"Status: 🔴 **{status}**"
                else:
                    status_display = f"Status: 🟡 **{status}**"
                
                st.subheader(f"Enviado em: {data_formatada}")
                st.markdown(status_display)

                col1, col2 = st.columns(2)
                
                with col1:
                    if 'url_imagem' in envio:
                        st.image(envio['url_imagem'], caption=envio.get('nome_arquivo', ''))
                
                with col2:
                    st.write("**Parecer da IA:**")
                    st.info(envio.get("descricao", "Nenhuma descrição."))
                
                st.divider()

        else:
            st.info("Você ainda não enviou nenhuma imagem.")
    else:
        st.info("Você ainda não enviou nenhuma imagem.")

except Exception as e:
    st.error(f"Ocorreu um erro ao buscar seu histórico: {e}")
