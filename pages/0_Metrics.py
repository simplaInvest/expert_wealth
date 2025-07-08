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

from funcs import projetar_dados, carregar_dataframes, precisa_atualizar
from sidebar import setup_sidebar


##############################################################################
##                           Autenticação e cache                           ##
##############################################################################

st.set_page_config(page_title="Metrics", page_icon="🔧", layout = 'wide')
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

#######################################################################################
##                           Carregar dfs do session state                           ##
#######################################################################################
if not all(k in st.session_state for k in ["df_ligacoes", "df_rmarcadas","df_rrealizadas", "df_cassinados", "df_metas_individuais", "df_captação"]):
    carregar_dataframes()

df_ligacoes = st.session_state.get("df_ligacoes")
df_rmarcadas = st.session_state.get("df_rmarcadas")
df_rrealizadas = st.session_state.get("df_rrealizadas")
df_cassinados = st.session_state.get("df_cassinados")
df_metas_individuais = st.session_state.get("df_metas_individuais")
df_captação_mes = st.session_state.get("df_captação")

#########################################################################################################
##                                         Início do Layout                                            ##
#########################################################################################################

##############################################################################
##                           Filtros Globais                                ##
##############################################################################

# Layout horizontal
col_filtros = st.columns([2, 1, 1, 2])  # [segmentação, período]

# Cópias filtradas dos DataFrames
df_rmarcadas_filtrado = df_rmarcadas.copy()
df_rrealizadas_filtrado = df_rrealizadas.copy()
df_cassinados_filtrado = df_cassinados.copy()
df_ligacoes_filtered =df_ligacoes.copy()

# 1. Filtro de Período com fundo cinza claro
with col_filtros[0]:
    with st.container(height =187,border = True):
        #st.markdown("<br>", unsafe_allow_html=True)

        hoje = date.today()
        primeiro_dia_semana = hoje - timedelta(days=hoje.weekday())
        primeiro_dia_mes = hoje.replace(day=1)

        periodo = st.radio("Selecione o período:", ["Dia", "Semana", "Mês", "Personalizado"], horizontal=True)

        # Define datas com base na seleção
        if periodo == "Dia":
            data_inicio = data_fim = hoje
        elif periodo == "Semana":
            data_inicio = primeiro_dia_semana
            data_fim = hoje
        elif periodo == "Mês":
            data_inicio = primeiro_dia_mes
            data_fim = hoje
        else:  # Personalizado
            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input("Data inicial", hoje.replace(day=1))
            with col2:
                data_fim = st.date_input("Data final", hoje)

        # Cálculos que devem ser mantidos
        dias_selecionados = (data_fim - data_inicio).days + 1
        mes_inicio = int(data_inicio.strftime("%m"))
        mes_fim = int(data_fim.strftime("%m"))


        #st.markdown("</div>", unsafe_allow_html=True)

    dias_selecionados = (data_fim - data_inicio).days + 1  # Inclui a data final

    # Converte as colunas "DATA" para datetime.date corretamente
    for df in [df_rmarcadas_filtrado, df_rrealizadas_filtrado, df_cassinados_filtrado]:
        if df["DATA"].dtype == object:
            df["DATA"] = pd.to_datetime(df["DATA"], format="%d/%m/%Y", errors="coerce").dt.date
        else:
            df["DATA"] = pd.to_datetime(df["DATA"]).dt.date

    # Aplica o filtro de data em cada DataFrame
    df_rmarcadas_filtrado = df_rmarcadas_filtrado[
        (df_rmarcadas_filtrado["DATA"] >= data_inicio) & 
        (df_rmarcadas_filtrado["DATA"] <= data_fim)
    ]

    df_rrealizadas_filtrado = df_rrealizadas_filtrado[
        (df_rrealizadas_filtrado["DATA"] >= data_inicio) & 
        (df_rrealizadas_filtrado["DATA"] <= data_fim)
    ]

    df_cassinados_filtrado = df_cassinados_filtrado[
        (df_cassinados_filtrado["DATA"] >= data_inicio) & 
        (df_cassinados_filtrado["DATA"] <= data_fim)
    ]

    # Novo bloco para df_ligacoes_filtered
    if df_ligacoes_filtered["Data"].dtype != 'O':
        df_ligacoes_filtered["Data"] = pd.to_datetime(df_ligacoes_filtered["Data"]).dt.date

    df_ligacoes_filtered = df_ligacoes_filtered[
        (df_ligacoes_filtered["Data"] >= data_inicio) & 
        (df_ligacoes_filtered["Data"] <= data_fim)
    ]

    mes_inicio = int(data_inicio.strftime("%m"))  # mês de data_inicio como int
    mes_fim = int(data_fim.strftime("%m"))        # mês de data_fim como int

# 1. Filtro de Segmentação
# --- Pré-processamento para df_ligacoes_filtered ---
# Extrair número da linha do campo "Usuário"
df_ligacoes_filtered["Linha"] = df_ligacoes_filtered["Usuário"].str.extract(r"\((\d{10,})\s*-")

df_linhas_validas = df_metas_individuais.copy()
df_linhas_validas["LINHA"] = df_linhas_validas["LINHA"].astype(str).str.strip()
df_linhas_validas = df_linhas_validas[df_linhas_validas["LINHA"].str.match(r"^\d+$")]

# Agora o mapa é criado só com LINHAS válidas
mapa_linha_consultor = df_linhas_validas.set_index("LINHA")["CONSULTOR"].to_dict()
mapa_linha_time = df_linhas_validas.set_index("LINHA")["TIME"].to_dict()


# Preenche o df_ligacoes_filtered com base nos mapas
df_ligacoes_filtered["Consultor"] = df_ligacoes_filtered["Linha"].map(mapa_linha_consultor)
df_ligacoes_filtered["Time"] = df_ligacoes_filtered["Linha"].map(mapa_linha_time)

with col_filtros[1]:
    segmentacao = st.radio("Segmentar por:", ["Geral", "Time", "Consultor"], horizontal=False)

    if segmentacao == "Time":
        with col_filtros[1]:
            time_selecionado = st.selectbox("Selecione o time:", ["TEAM BRAVO", "TEAM FARMER", "TEAM POWER", "SDR"])
            
            df_rmarcadas_filtrado = df_rmarcadas_filtrado[df_rmarcadas_filtrado["TIME"] == time_selecionado]
            df_rrealizadas_filtrado = df_rrealizadas_filtrado[df_rrealizadas_filtrado["TIME"] == time_selecionado]
            df_cassinados_filtrado = df_cassinados_filtrado[df_cassinados_filtrado["TIME"] == time_selecionado]
            df_ligacoes_filtered = df_ligacoes_filtered[df_ligacoes_filtered["Time"] == time_selecionado]

    elif segmentacao == "Consultor":
        with col_filtros[1]:
            consultores = df_metas_individuais["CONSULTOR"].dropna().unique()
            consultor_selecionado = st.selectbox("Selecione o consultor:", sorted(consultores))

            df_rmarcadas_filtrado = df_rmarcadas_filtrado[df_rmarcadas_filtrado["CONSULTOR"] == consultor_selecionado]
            df_rrealizadas_filtrado = df_rrealizadas_filtrado[df_rrealizadas_filtrado["CONSULTOR"] == consultor_selecionado]
            df_cassinados_filtrado = df_cassinados_filtrado[df_cassinados_filtrado["CONSULTOR"] == consultor_selecionado]
            df_ligacoes_filtered = df_ligacoes_filtered[df_ligacoes_filtered["Consultor"] == consultor_selecionado]

    # 2. Determina os consultores filtrados
    if segmentacao == "Geral":
        consultores_filtrados = df_metas_individuais["CONSULTOR"].dropna().unique()
        n_consultores = len(consultores_filtrados)-3 # exclui os líderes da meta
    elif segmentacao == "Time":
        consultores_filtrados = df_metas_individuais[df_metas_individuais["TIME"] == time_selecionado]["CONSULTOR"].dropna().unique()
        n_consultores = len(consultores_filtrados)
    elif segmentacao == "Consultor":
        consultores_filtrados = [consultor_selecionado]
        n_consultores = len(consultores_filtrados)

with col_filtros[2]:
    st.write(f'Número de consultores selecionados: {n_consultores}')

# Define o número de ligações atendidas para o funil
ligações_atendidas = df_ligacoes_filtered[df_ligacoes_filtered['Tempo da ligação'] >= timedelta(minutes=1)].shape[0]

with col_filtros[3]:
    duration_options = ["Todos", "Zero", "Menos de 1 min", "Mais de 1 min", "Mais de 2 min"]
    selected_durations = st.multiselect("Escolha a duração mínima das chamadas (Apenas para Linha Virtual)", duration_options, help="")
    
    if selected_durations:
        duration_filters = []
        if "Zero" in selected_durations:
            duration_filters.append(df_ligacoes_filtered['Tempo da ligação'] == timedelta(seconds=0))
        if "Menos de 1 min" in selected_durations:
            duration_filters.append((df_ligacoes_filtered['Tempo da ligação'] > timedelta(seconds=0)) & 
                                    (df_ligacoes_filtered['Tempo da ligação'] < timedelta(minutes=1)))
        if "Mais de 1 min" in selected_durations:
            duration_filters.append(df_ligacoes_filtered['Tempo da ligação'] >= timedelta(minutes=1))
        if "Mais de 2 min" in selected_durations:
            duration_filters.append(df_ligacoes_filtered['Tempo da ligação'] >= timedelta(minutes=2))
        if "Todos" in selected_durations:
            duration_filters.append(df_ligacoes_filtered['Tempo da ligação'] >= timedelta(minutes=0))
        df_ligacoes_filtered = df_ligacoes_filtered[pd.concat(duration_filters, axis=1).any(axis=1)]

#########################################################################################################
##                                                 Funil                                               ##
#########################################################################################################

##############################################################################
##                           Velocimetros e Funil                           ##
##############################################################################

# Valores do funil
valores = {
    "Reuniões Marcadas": len(df_rmarcadas_filtrado),
    "Reuniões Realizadas": len(df_rrealizadas_filtrado),
    "Contratos Assinados": len(df_cassinados_filtrado)
}

# Metas por dia por consultor
metas = {
    "Reuniões Marcadas": 40,
    "Reuniões Realizadas": 28,
    "Contratos Assinados": 7
}

multiplicador_mes = mes_fim - mes_inicio + 1

# Meta acumulada = dias * meta_diária * número de consultores
metas_acumuladas = {
    etapa: multiplicador_mes * valor_mensal * n_consultores
    for etapa, valor_mensal in metas.items()
}

projetar_dados(
    df_ligacoes_filtered,
    df_rmarcadas_filtrado,
    df_rrealizadas_filtrado,
    df_cassinados_filtrado,
    df_metas_individuais,
    df_captação_mes,
    df_linhas_validas,
    valores,
    metas_acumuladas,
    multiplicador_mes,
    n_consultores,
    data_inicio,
    data_fim
)

