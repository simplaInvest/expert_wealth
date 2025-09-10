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
df_nova_base = st.session_state.get("df_nova_base")
stage_event = st.session_state.get("stage_events")
deals_master = st.session_state.get("deals_master")
####################################################################################################################
planilhas = [
    ("Nova Base", df_nova_base),
    ("stage event", stage_event),
    ("deals master", deals_master)
]

for nome, df in planilhas:
    st.subheader(f"Planilha: {nome}")
    st.dataframe(df)
