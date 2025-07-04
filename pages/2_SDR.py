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
from streamlit_option_menu import option_menu

from funcs import carregar_dataframes, pag_sdr
from sidebar import setup_sidebar


##############################################################################
##                           Autenticação e cache                           ##
##############################################################################

# Configuração da página
st.set_page_config(page_title="Dashboard Métricas SDR", layout="wide")

# Chama a sidebar
setup_sidebar()

if st.button("Limpar Tudo"):
    # Limpa o cache
    st.cache_data.clear()
    st.cache_resource.clear()

    # Limpa o session_state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.success("Cache e estado da sessão limpos! Recarregue os dados.")

    st.switch_page("main.py")

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

pag_sdr(df_sdr=df_sdr, df_discadora=df_discadora)
