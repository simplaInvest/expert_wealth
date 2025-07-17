import streamlit as st
import pandas as pd
from funcs import carregar_dataframes, precisa_atualizar
from datetime import datetime, timedelta
from sidebar import setup_sidebar
import time

st.set_page_config(page_title="Planilhas", page_icon="📝", layout = 'wide')
st.logo(image='z_logo_light.png', size = 'large')

# Chama a sidebar
setup_sidebar()

if precisa_atualizar():
    carregar_dataframes()
    st.session_state["ultima_atualizacao"] = time.time()

if st.button(label = '🔄 Recarregar Planilhas'):
    carregar_dataframes()  # sua função para carregar dados das planilhas
    st.session_state["ultima_atualizacao"] = time.time()

if "ultima_atualizacao" in st.session_state:
    st.sidebar.markdown(
        f"🕒 Dados atualizados pela última vez em: "
        f"{time.strftime('%H:%M:%S', time.localtime(st.session_state['ultima_atualizacao']))}"
    )

####################################################################################################################
if not all(k in st.session_state for k in ["df_ligacoes", "df_rmarcadas","df_rrealizadas", "df_cassinados", "df_metas_individuais", "df_captação"]):
    carregar_dataframes()

df_ligacoes = st.session_state.get("df_ligacoes")
df_rmarcadas = st.session_state.get("df_rmarcadas")
df_rrealizadas = st.session_state.get("df_rrealizadas")
df_cassinados = st.session_state.get("df_cassinados")
df_metas_individuais = st.session_state.get("df_metas_individuais")
df_captação_mes = st.session_state.get("df_captação")
####################################################################################################################
planilhas = [
    ("Ligações", df_ligacoes),
    ("Reuniões Marcadas", df_rmarcadas),
    ("Reuniões Realizadas", df_rrealizadas),
    ("Clientes Assinados", df_cassinados),
    ("Metas Individuais", df_metas_individuais),
    ("Captação do Mês", df_captação_mes)
]

for nome, df in planilhas:
    st.subheader(f"Planilha: {nome}")
    st.dataframe(df)
