# No arquivo: paginas/dashboard.py

import streamlit as st
from utils import conectar_firebase
import pandas as pd
from datetime import timedelta

st.set_page_config(page_title="Dashboard", layout="wide")

# ... (conexão e verificação de acesso) ...
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


st.title(f"📊 Dashboard de Análise de Processos")
st.write(f"Bem-vindo, {getattr(st.user, 'name', 'Supervisor')}. Monitore a eficiência e a conformidade dos envios.")
st.divider()

# --- Carregar e Processar Dados ---
@st.cache_data(ttl=300)
def carregar_dados():
    # ... (código para carregar dados) ...
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

# ... (métricas principais) ...
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

df = pd.DataFrame(envios_globais)
df['data_envio'] = pd.to_datetime(df['data_envio'])

# --- NOVA SEÇÃO: ANÁLISE DE CAUSA RAIZ ---
st.subheader("Análise de Causa Raiz de Não Conformidade")

nao_conformes = [
    item["requisito"]
    for envio in envios_globais
    if envio.get("analise_ia", {}).get("status_geral") == "NAO_CONFORME"
    for item in envio["analise_ia"].get("laudo_tecnico", [])
    if not item["cumprido"]
]

if nao_conformes:
    causa_raiz_df = pd.DataFrame(nao_conformes, columns=["Motivo da Falha"]).value_counts().reset_index(name='Ocorrências')
    st.bar_chart(causa_raiz_df.set_index('Motivo da Falha'))
else:
    st.success("Nenhuma falha de conformidade detectada nos envios recentes.")

st.divider()


# --- Gráficos Anteriores ---
# ... (código dos gráficos de status, colaborador e atividade recente) ...
df['data'] = df['data_envio'].dt.date

col1, col2 = st.columns(2)

with col1:
    st.subheader("Envios por Status")
    status_counts = df['status'].value_counts()
    
    color_map = {
        "Em processo": "#eab308",    
        "Aprovado": "#22c55e",       
        "Reprovado": "#ef4444"       
    }
    
    status_df = pd.DataFrame({
        'status': status_counts.index,
        'count': status_counts.values
    })
    
    status_df['color'] = status_df['status'].map(color_map)
    st.bar_chart(status_df.set_index('status'), y='count', color='color')

with col2:
    st.subheader("Envios por Colaborador")
    colaborador_counts = df['colaborador'].value_counts()
    st.bar_chart(colaborador_counts)

st.subheader("Atividade Recente (Últimos 7 dias)")
hoje_utc = pd.Timestamp.now(tz='UTC')
limite_data = hoje_utc - timedelta(days=7)
ultimos_7_dias = df[df['data_envio'] >= limite_data]
envios_por_dia = ultimos_7_dias.groupby('data').size()
st.line_chart(envios_por_dia)
