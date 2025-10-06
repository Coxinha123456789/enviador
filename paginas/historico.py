# No arquivo: paginas/historico.py

import streamlit as st
from utils import conectar_firebase

st.set_page_config(page_title="Meu Histórico", layout="wide")

# --- Conexão com Firebase ---
db, _ = conectar_firebase()
colecao = 'ColecaoEnviados'

# --- Verificação de Login ---
if not (hasattr(st, "user") and st.user.is_logged_in):
    st.warning("Faça login para ver seu histórico.")
    st.stop()

collaborator_email = getattr(st.user, "email", "não identificado")

# --- Layout ---
st.title("📜 Meu Histórico de Envios")
st.write(f"Acompanhe o status e o progresso dos documentos que você enviou.")
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

            for envio in envios_ordenados:
                with st.container(border=True):
                    status_final = envio.get('status', 'Em processo')
                    
                    st.subheader(f"Arquivo: {envio.get('nome_arquivo', 'Sem nome')}")
                    
                    if status_final == 'Aprovado': st.markdown(f"**Status Final:** <span style='color: #22c55e;'>🟢 Aprovado</span>", unsafe_allow_html=True)
                    elif status_final == 'Reprovado': st.markdown(f"**Status Final:** <span style='color: #ef4444;'>🔴 Reprovado</span>", unsafe_allow_html=True)
                    else: st.markdown(f"**Status Final:** <span style='color: #eab308;'>🟡 Em processo</span>", unsafe_allow_html=True)

                    col1, col2 = st.columns([2, 3])
                    
                    with col1:
                        # --- CORREÇÃO APLICADA AQUI ---
                        # Lógica robusta para encontrar a URL da imagem em estruturas de dados novas e antigas.
                        # Prioriza a 'url_imagem_exibicao' (nova) e usa 'url_imagem' (antiga) como fallback.
                        url_para_exibir = envio.get('url_imagem_exibicao') or envio.get('url_imagem')

                        if url_para_exibir:
                            st.image(url_para_exibir)
                        else:
                            st.warning("Imagem não encontrada para este envio.")
                        # --- FIM DA CORREÇÃO ---
                    
                    with col2:
                        st.write("**Linha do Tempo do Processo:**")
                        log_ordenado = sorted(envio.get('log', []), key=lambda x: x['timestamp'])

                        for log in log_ordenado:
                            data_log = log['timestamp'].strftime('%d/%m/%Y às %H:%M')
                            st.markdown(f"- **{log['status']}** em {data_log}")
                            if log.get('comentario'):
                                st.info(f"Comentário: {log['comentario']}")

        else:
            st.info("Você ainda não enviou nenhum documento.")
    else:
        st.info("Você ainda não enviou nenhum documento.")

except Exception as e:
    st.error(f"Ocorreu um erro ao buscar seu histórico: {e}")
