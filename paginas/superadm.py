# No arquivo: paginas/superadm.py

import streamlit as st
import pandas as pd
from utils import conectar_firebase

# --- Configuração e Segurança ---
st.set_page_config(page_title="Super Administrador", layout="wide")

# Conecte-se ao Firebase
db, _ = conectar_firebase()
users_collection = db.collection('users')

# Defina o e-mail do Super Admin. SOMENTE ESTE E-MAIL PODERÁ ACESSAR ESTA PÁGINA.
SUPERADMIN_EMAIL = "thales.santoseng@gmail.com" # !!! TROQUE PELO SEU E-MAIL !!!

# Verificação de Acesso
if not (hasattr(st, "user") and st.user.is_logged_in and getattr(st.user, "email", "").lower() == SUPERADMIN_EMAIL):
    st.error("Acesso negado. Esta página é restrita ao Super Administrador.")
    st.stop()

st.title("🔑 Painel do Super Administrador")
st.write("Gerencie os usuários e suas permissões no sistema.")
st.divider()

# --- Função para carregar usuários ---
@st.cache_data(ttl=60)
def load_users():
    users = []
    docs = users_collection.stream()
    for doc in docs:
        user_data = doc.to_dict()
        users.append({
            "email": doc.id,
            "role": user_data.get("role", "indefinido")
        })
    return pd.DataFrame(users)

# --- Adicionar Novo Usuário ---
st.subheader("Adicionar Novo Usuário")
with st.form("new_user_form", clear_on_submit=True):
    new_email = st.text_input("E-mail do novo usuário")
    new_role = st.selectbox("Função (Role)", ["colaborador", "supervisor"])
    submitted = st.form_submit_button("Adicionar Usuário")

    if submitted and new_email:
        try:
            users_collection.document(new_email.lower()).set({"role": new_role})
            st.success(f"Usuário {new_email} adicionado como {new_role}!")
            st.cache_data.clear() # Limpa o cache para recarregar a lista
        except Exception as e:
            st.error(f"Erro ao adicionar usuário: {e}")

st.divider()

# --- Gerenciar Usuários Existentes ---
st.subheader("Gerenciar Usuários Existentes")
df_users = load_users()

if not df_users.empty:
    df_users_editable = df_users[df_users["email"] != SUPERADMIN_EMAIL].copy()
    df_users_editable["deletar"] = False

    st.info("Para alterar a função de um usuário, edite o campo 'role' e pressione Enter. Para remover, marque a caixa 'deletar'.")
    
    edited_df = st.data_editor(
        df_users_editable,
        column_config={
            "email": st.column_config.TextColumn("E-mail (não pode ser alterado)", disabled=True),
            "role": st.column_config.SelectboxColumn("Função (Role)", options=["colaborador", "supervisor"], required=True),
            "deletar": st.column_config.CheckboxColumn("Deletar Usuário", default=False),
        },
        hide_index=True,
        use_container_width=True
    )

    if st.button("Salvar Alterações"):
        with st.spinner("Salvando..."):
            for index, row in edited_df.iterrows():
                email = row["email"]
                
                if row["deletar"]:
                    users_collection.document(email).delete()
                    st.toast(f"Usuário {email} removido.", icon="🗑️")
                else:
                    original_role = df_users_editable.loc[index, "role"]
                    if row["role"] != original_role:
                        users_collection.document(email).set({"role": row["role"]})
                        st.toast(f"Função de {email} alterada para {row['role']}.", icon="🔄")
            
            st.cache_data.clear()
            st.success("Alterações salvas com sucesso!")
            st.rerun()

else:
    st.info("Nenhum usuário cadastrado ainda (além de você).")
