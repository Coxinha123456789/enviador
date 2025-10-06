# No arquivo: paginas/dashboard.py

import streamlit as st
from utils import conectar_firebase
import pandas as pd

st.set_page_config(page_title="Dashboard", layout="wide")

# --- Conexão com Firebase ---
db, _ = conectar_firebase()
colecao = 'ColecaoEnviados'

# --- Verificação de Acesso ---
if not (hasattr(st, "user") and getattr(st.user, "is_logged_in", False)):
    st.warning("Você precisa fazer login como supervisor para acessar esta página.")
    st.stop()

email_logado = getattr(st.user, "email", "").lower()
SUPERVISOR_EMAILS = ["thalestatasena@gmail.com"]

if email_logado not in SUPERVISOR_EMAILS:
    st.error("Acesso negado. Esta página é restrita a supervisores.")
    st.stop()

st.title(f"📊 Dashboard de Análise")
st.write(f"Bem-vindo, {getattr(st.user, 'name', 'Supervisor')}. Aqui está um resumo da atividade dos colaboradores.")
st.divider()

# --- Carregar e Processar Dados ---
@st.cache_data(ttl=600)
def carregar_dados():
    todos_envios = []
    docs = db.collection(colecao).stream()
    for doc in docs:
        colaborador = doc.id
        dados = doc.to_dict()
        envios = dados.get("envios", [])
        for envio in envios:
            envio['colaborador'] = colaborador
            todos_envios.append(envio)
    return todos_envios

envios_globais = carregar_dados()

if not envios_globais:
    st.info("Ainda não há dados de envios para exibir no dashboard.")
    st.stop()

# --- Métricas Principais ---
total_envios = len(envios_globais)
pendentes = sum(1 for e in envios_globais if e.get('status') == 'Em processo')
aprovados = sum(1 for e in envios_globais if e.get('status') == 'Aprovado')
reprovados = sum(1 for e in envios_globais if e.get('status') == 'Reprovado')

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Envios", f"{total_envios} 📄")
col2.metric("Pendentes de Análise", f"{pendentes} 🟡")
col3.metric("Documentos Aprovados", f"{aprovados} 🟢")
col4.metric("Documentos Reprovados", f"{reprovados} 🔴")

st.divider()

# --- Gráficos ---
df = pd.DataFrame(envios_globais)
df['data_envio'] = pd.to_datetime(df['data_envio'])
df['data'] = df['data_envio'].dt.date

col1, col2 = st.columns(2)

with col1:
    st.subheader("Envios por Status")
    status_counts = df['status'].value_counts()
    st.bar_chart(status_counts, color=["#eab308", "#22c55e", "#ef4444"]) # Amarelo, Verde, Vermelho

with col2:
    st.subheader("Envios por Colaborador")
    colaborador_counts = df['colaborador'].value_counts()
    st.bar_chart(colaborador_counts)

st.subheader("Atividade Recente (Últimos 7 dias)")
ultimos_7_dias = df[df['data_envio'] >= (pd.to_datetime('today') - pd.Timedelta(days=7))]
envios_por_dia = ultimos_7_dias.groupby('data').size()
st.line_chart(envios_por_dia)
