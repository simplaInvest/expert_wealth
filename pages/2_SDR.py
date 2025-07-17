##############################################################################
##                                Bibliotecas                               ##
##############################################################################

import streamlit as st  # type: ignore
import json 
import requests  # type: ignore
import os
import datetime
from datetime import date, timedelta, datetime
import pandas as pd  # type: ignore
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import time  # Para controle de atualização automática
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import random
from datetime import datetime, timedelta
import re

from funcs import carregar_dataframes, pag_sdr, precisa_atualizar, pag_sdr_teste
from sidebar import setup_sidebar


##############################################################################
##                           Autenticação e cache                           ##
##############################################################################

# Configuração da página
st.set_page_config(page_title="Dashboard Métricas SDR", layout="wide")
st.logo(image='z_logo_light.png', size = 'large')
st.write("")
st.write("")
st.write("")

# Título do dashboard
#st.title("📊 Dashboard - Métricas SDR")
#st.info("""
#💡 Em desenvolvimento 🥶
#""")
#st.markdown("---")

# Chama a sidebar
setup_sidebar()

with st.sidebar:
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

#######################################################################################
##                           Carregar dfs do session state                           ##
#######################################################################################
if not all(k in st.session_state for k in ["df_sdr", "df_discadora"]):
    carregar_dataframes()

df_sdr = st.session_state.get("df_sdr")
df_discadora = st.session_state.get("df_discadora")

#########################################################################################################
##                                         Início do Layout                                            ##
#########################################################################################################

# pag_sdr(df_sdr=df_sdr, df_discadora=df_discadora)

pag_sdr_teste(df_sdr=df_sdr, df_discadora=df_discadora)