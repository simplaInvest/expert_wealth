##############################################################################
##                                Bibliotecas                               ##
##############################################################################

import streamlit as st  # type: ignore
import numpy as np
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
from teste1 import projetar_dados_teste
from sidebar import setup_sidebar


##############################################################################
##                           Autenticação e cache                           ##
##############################################################################

st.set_page_config(page_title="Metrics", page_icon="🔧", layout = 'wide')
st.logo(image='z_logo_light.png', size = 'large')

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
st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# CSS customizado para os filtros - Versão Compacta e Modo Noturno
st.markdown("""
<style>
/* Importar fonte moderna */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Tema principal dark */
.stApp {
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
    font-family: 'Inter', sans-serif;
}

.filter-container {
    background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 12px;
    padding: 1rem;
    margin: 0.5rem 0;
    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.filter-container:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.2);
    border-color: rgba(99, 102, 241, 0.4);
}

.filter-header {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.6rem;
    text-align: center;
    padding: 0.8rem;
    border-radius: 8px;
    box-shadow: 0 3px 12px rgba(99, 102, 241, 0.3);
    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
}

.filter-section {
    background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
    border-radius: 8px;
    padding: 0.8rem;
    margin: 0.5rem 0;
    box-shadow: 0 3px 12px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(99, 102, 241, 0.1);
    backdrop-filter: blur(5px);
}

.filter-title {
    color: #f8fafc;
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid #6366f1;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
}

.metric-display {
    background: linear-gradient(135deg, #059669 0%, #047857 100%);
    color: white;
    padding: 0.8rem;
    border-radius: 8px;
    text-align: center;
    font-size: 1rem;
    font-weight: 600;
    margin-top: 0.6rem;
    box-shadow: 0 6px 20px rgba(5, 150, 105, 0.3);
    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
}

.metric-display:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(5, 150, 105, 0.4);
}

.info-box {
    background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
    color: white;
    padding: 0.6rem;
    border-radius: 6px;
    margin: 0.3rem 0;
    text-align: center;
    font-weight: 500;
    font-size: 0.85rem;
    box-shadow: 0 3px 12px rgba(217, 119, 6, 0.3);
    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
}

.period-info {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    padding: 0.6rem;
    border-radius: 6px;
    margin: 0.3rem 0;
    text-align: center;
    font-weight: 500;
    font-size: 0.85rem;
    box-shadow: 0 3px 12px rgba(99, 102, 241, 0.3);
    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
}

.filters-main-header {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
    color: white;
    padding: 1.2rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    text-align: center;
    font-size: 1.3rem;
    font-weight: 700;
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);
    backdrop-filter: blur(10px);
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

/* Customização dos elementos de input */
.stRadio > div {
    flex-direction: row;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.stRadio > div > label {
    background: linear-gradient(135deg, #4b5563 0%, #6b7280 100%) !important;
    color: #f8fafc !important;
    padding: 0.4rem 0.8rem !important;
    border-radius: 6px !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
}

.stRadio > div > label:hover {
    border-color: rgba(99, 102, 241, 0.5) !important;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 3px 10px rgba(99, 102, 241, 0.3) !important;
}

.stRadio > div > label[data-checked="true"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    border-color: #d946ef !important;
    box-shadow: 0 3px 12px rgba(99, 102, 241, 0.4) !important;
}

/* Customização para multiselect e selectbox */
.stMultiSelect > div > div {
    background: linear-gradient(135deg, #374151 0%, #4b5563 100%) !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    border-radius: 6px !important;
    color: #f8fafc !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
}

.stMultiSelect > div > div > div {
    background: rgba(31, 41, 55, 0.8) !important;
    color: #f8fafc !important;
}

.stSelectbox > div > div {
    background: linear-gradient(135deg, #374151 0%, #4b5563 100%) !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    border-radius: 6px !important;
    color: #f8fafc !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
}

.stSelectbox > div > div > div {
    background: rgba(31, 41, 55, 0.8) !important;
    color: #f8fafc !important;
}

.stDateInput > div > div {
    background: linear-gradient(135deg, #374151 0%, #4b5563 100%) !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    border-radius: 6px !important;
    color: #f8fafc !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
}

/* Melhor contraste para textos */
.stMarkdown {
    color: #f8fafc;
}

/* Ajustes para labels dos inputs */
.stRadio > div > label > div {
    color: #f8fafc !important;
}

/* Customização da sidebar */
.css-1d391kg {
    background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
}

.css-1d391kg .css-1v3fvcr {
    background: rgba(31, 41, 55, 0.8);
}

/* Ajustes para dropdowns */
.stSelectbox [data-baseweb="select"] > div {
    background: linear-gradient(135deg, #374151 0%, #4b5563 100%) !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    color: #f8fafc !important;
    border-radius: 6px !important;
}

.stMultiSelect [data-baseweb="select"] > div {
    background: linear-gradient(135deg, #374151 0%, #4b5563 100%) !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    color: #f8fafc !important;
    border-radius: 6px !important;
}

/* Redução significativa de espaçamentos */
.element-container {
    margin-bottom: 0.3rem !important;
}

.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
}

/* Compactar elementos ao máximo */
.stRadio {
    margin-bottom: 0.3rem !important;
}

.stSelectbox {
    margin-bottom: 0.3rem !important;
}

.stMultiSelect {
    margin-bottom: 0.3rem !important;
}

.stDateInput {
    margin-bottom: 0.3rem !important;
}

/* Reduzir espaçamento entre campos */
.stRadio > label {
    margin-bottom: 0.2rem !important;
}

.stSelectbox > label {
    margin-bottom: 0.2rem !important;
}

.stMultiSelect > label {
    margin-bottom: 0.2rem !important;
}

.stDateInput > label {
    margin-bottom: 0.2rem !important;
}

/* Compactar ainda mais os containers */
.css-1y4p8pa {
    gap: 0.3rem !important;
}

.css-12oz5g7 {
    gap: 0.3rem !important;
}

/* Efeitos de hover para containers */
.filter-section:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.15);
}

/* Scrollbar customizada */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: #374151;
    border-radius: 3px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%);
}

/* Botões com estilo moderno */
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    box-shadow: 0 3px 12px rgba(99, 102, 241, 0.3);
    transition: all 0.3s ease;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 0.85rem;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}

/* Reduzir altura dos inputs */
.stSelectbox [data-baseweb="select"] {
    min-height: 36px !important;
}

.stMultiSelect [data-baseweb="select"] {
    min-height: 36px !important;
}

/* Compactar labels */
.stRadio > label,
.stSelectbox > label,
.stMultiSelect > label,
.stDateInput > label {
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    margin-bottom: 0.2rem !important;
}

/* Reduzir padding interno dos containers principais */
.css-1d391kg {
    padding: 0.5rem !important;
}

/* Ajustar espaçamento entre seções */
.css-1y4p8pa > div {
    margin-bottom: 0.3rem !important;
}

/* Compactar métricas */
.metric-container {
    margin: 0.3rem 0 !important;
}
</style>
""", unsafe_allow_html=True)

# Cabeçalho principal dos filtros
st.markdown("""
<div class="filters-main-header">
    ⚙️ Painel de Controle e Filtros
</div>
""", unsafe_allow_html=True)

# Layout horizontal melhorado
col_filtros = st.columns([2.5, 1.5, 1.2, 2.8], gap="medium")

# Cópias filtradas dos DataFrames
df_rmarcadas_filtrado = df_rmarcadas.copy()
df_rrealizadas_filtrado = df_rrealizadas.copy()
df_cassinados_filtrado = df_cassinados.copy()
df_ligacoes_filtered = df_ligacoes.copy()

# 1. Filtro de Período
with col_filtros[0]:
    st.markdown("""
    <div class="filter-container">
        <div class="filter-header">
            📅 Período de Análise
        </div>
    """, unsafe_allow_html=True)
    
    hoje = date.today()
    primeiro_dia_semana = hoje - timedelta(days=hoje.weekday())
    primeiro_dia_mes = hoje.replace(day=1)

    st.markdown('<div class="filter-title">🎯 Selecione o Período:</div>', unsafe_allow_html=True)
    
    periodo = st.radio(
        "periodo_selector",
        ["Dia", "Semana", "Mês", "Personalizado"], 
        horizontal=True,
        label_visibility="collapsed"
    )

    # Define datas com base na seleção
    if periodo == "Dia":
        data_inicio = data_fim = hoje
        periodo_display = f"📊 Hoje: {hoje.strftime('%d/%m/%Y')}"
    elif periodo == "Semana":
        data_inicio = primeiro_dia_semana
        data_fim = hoje
        periodo_display = f"📊 Semana: {data_inicio.strftime('%d/%m')} - {data_fim.strftime('%d/%m/%Y')}"
    elif periodo == "Mês":
        data_inicio = primeiro_dia_mes
        data_fim = hoje
        periodo_display = f"📊 Mês: {data_inicio.strftime('%d/%m')} - {data_fim.strftime('%d/%m/%Y')}"
    else:  # Personalizado
        st.markdown('<div class="filter-title">🗓️ Período Personalizado:</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("📅 Data inicial", hoje.replace(day=1))
        with col2:
            data_fim = st.date_input("📅 Data final", hoje)
        periodo_display = f"📊 Personalizado: {data_inicio.strftime('%d/%m')} - {data_fim.strftime('%d/%m/%Y')}"

    # Cálculos que devem ser mantidos
    dias_selecionados = np.busday_count(data_inicio, data_fim + timedelta(days=1))
    mes_inicio = int(data_inicio.strftime("%m"))
    mes_fim = int(data_fim.strftime("%m"))

    # Exibir informações do período
    st.markdown(f"""
    <div class="period-info">
        {periodo_display}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="info-box">
        📊 Dias selecionados: {dias_selecionados}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

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

mes_inicio = int(data_inicio.strftime("%m"))
mes_fim = int(data_fim.strftime("%m"))

# Pré-processamento para df_ligacoes_filtered
df_ligacoes_filtered["Linha"] = df_ligacoes_filtered["Usuário"].str.extract(r"\((\d{10,})\s*-")

df_linhas_validas = df_metas_individuais.copy()
df_linhas_validas["LINHA"] = df_linhas_validas["LINHA"].astype(str).str.strip()
df_linhas_validas = df_linhas_validas[df_linhas_validas["LINHA"].str.match(r"^\d+$")]

mapa_linha_consultor = df_linhas_validas.set_index("LINHA")["CONSULTOR"].to_dict()
mapa_linha_time = df_linhas_validas.set_index("LINHA")["TIME"].to_dict()

df_ligacoes_filtered["Consultor"] = df_ligacoes_filtered["Linha"].map(mapa_linha_consultor)
df_ligacoes_filtered["Time"] = df_ligacoes_filtered["Linha"].map(mapa_linha_time)

# 2. Filtro de Segmentação
with col_filtros[1]:
    st.markdown("""
    <div class="filter-container">
        <div class="filter-header">
            👥 Segmentação
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="filter-title">🎯 Visualizar por:</div>', unsafe_allow_html=True)
    
    segmentacao = st.radio(
        "segmentacao_selector",
        ["Geral", "Time", "Consultor"], 
        horizontal=False,
        label_visibility="collapsed"
    )

    if segmentacao == "Geral":
        geral = ["TEAM BRAVO", "TEAM POWER"]

        df_rmarcadas_filtrado = df_rmarcadas_filtrado[df_rmarcadas_filtrado["TIME"].isin(geral)]
        df_rrealizadas_filtrado = df_rrealizadas_filtrado[df_rrealizadas_filtrado["TIME"].isin(geral)]
        df_cassinados_filtrado = df_cassinados_filtrado[df_cassinados_filtrado["TIME"].isin(geral)]
        df_ligacoes_filtered = df_ligacoes_filtered[df_ligacoes_filtered["Time"].isin(geral)]
        df_metas_individuais = df_metas_individuais[df_metas_individuais["TIME"].isin(geral)]

    if segmentacao == "Time":
        st.markdown('<div class="filter-title">🏆 Selecione o Time:</div>', unsafe_allow_html=True)
        time_selecionado = st.selectbox(
            "time_selector",
            ["TEAM BRAVO", "TEAM POWER"],
            label_visibility="collapsed"
        )
        
        df_rmarcadas_filtrado = df_rmarcadas_filtrado[df_rmarcadas_filtrado["TIME"] == time_selecionado]
        df_rrealizadas_filtrado = df_rrealizadas_filtrado[df_rrealizadas_filtrado["TIME"] == time_selecionado]
        df_cassinados_filtrado = df_cassinados_filtrado[df_cassinados_filtrado["TIME"] == time_selecionado]
        df_ligacoes_filtered = df_ligacoes_filtered[df_ligacoes_filtered["Time"] == time_selecionado]
        df_metas_individuais = df_metas_individuais[df_metas_individuais["TIME"] == time_selecionado]
        
        st.markdown(f"""
        <div class="info-box">
            🏆 Time: {time_selecionado}
        </div>
        """, unsafe_allow_html=True)

    elif segmentacao == "Consultor":
        st.markdown('<div class="filter-title">👤 Selecione o Consultor:</div>', unsafe_allow_html=True)
        consultores = df_metas_individuais[df_metas_individuais["TIME"].isin(["TEAM BRAVO", "TEAM POWER"])]["CONSULTOR"].dropna().unique()
        consultor_selecionado = st.selectbox(
            "consultor_selector",
            sorted(consultores),
            label_visibility="collapsed"
        )

        df_rmarcadas_filtrado = df_rmarcadas_filtrado[df_rmarcadas_filtrado["CONSULTOR"] == consultor_selecionado]
        df_rrealizadas_filtrado = df_rrealizadas_filtrado[df_rrealizadas_filtrado["CONSULTOR"] == consultor_selecionado]
        df_cassinados_filtrado = df_cassinados_filtrado[df_cassinados_filtrado["CONSULTOR"] == consultor_selecionado]
        df_ligacoes_filtered = df_ligacoes_filtered[df_ligacoes_filtered["Consultor"] == consultor_selecionado]
        df_metas_individuais = df_metas_individuais[df_metas_individuais["CONSULTOR"] == consultor_selecionado]
        
        st.markdown(f"""
        <div class="info-box">
            👤 Consultor: {consultor_selecionado}
        </div>
        """, unsafe_allow_html=True)

    # Determina os consultores filtrados
    if segmentacao == "Geral":
        consultores_filtrados = df_metas_individuais["CONSULTOR"].dropna().unique()
        n_consultores = len(consultores_filtrados)
    elif segmentacao == "Time":
        consultores_filtrados = df_metas_individuais["CONSULTOR"].dropna().unique()
        n_consultores = len(consultores_filtrados)
        if time_selecionado == "SDR":
            n_sdr = 2
        else:
            n_sdr = 0
    elif segmentacao == "Consultor":
        consultores_filtrados = [consultor_selecionado]
        n_consultores = len(consultores_filtrados)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 3. Contador de Consultores
with col_filtros[2]:
    st.markdown("""
    <div class="filter-container">
        <div class="filter-header">
            📊 Métricas
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="metric-display">
        👥 Consultores<br>
        <span style="font-size: 1.6rem; font-weight: 700;">{n_consultores}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Informações adicionais baseadas na segmentação
    if segmentacao == "Geral":
        st.markdown("""
        <div class="info-box">
            🌐 Visão Geral
        </div>
        """, unsafe_allow_html=True)
    elif segmentacao == "Time":
        st.markdown(f"""
        <div class="info-box">
            🏆 {time_selecionado}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-box">
            👤 Individual
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Define o número de ligações atendidas para o funil
ligações_atendidas = df_ligacoes_filtered[df_ligacoes_filtered['Tempo da ligação'] >= timedelta(minutes=1)].shape[0]

# 4. Filtro de Duração das Chamadas
with col_filtros[3]:
    st.markdown("""
    <div class="filter-container">
        <div class="filter-header">
            ⏱️ Duração das Chamadas
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="filter-title">🎯 Filtrar por Duração:</div>', unsafe_allow_html=True)
    
    duration_options = ["Todos", "Zero", "Menos de 1 min", "Mais de 1 min", "Mais de 2 min"]
    selected_durations = st.multiselect(
        "Escolha a duração das chamadas",
        duration_options,
        help="Filtro aplicado apenas para Linha Virtual",
        label_visibility="collapsed"
    )
    
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
        
        # Exibir informações dos filtros aplicados
        st.markdown(f"""
        <div class="info-box">
            🔍 Filtros: {', '.join(selected_durations)}
        </div>
        """, unsafe_allow_html=True)
    
    # Estatísticas das ligações
    total_ligacoes = len(df_ligacoes_filtered)
    ligacoes_atendidas = len(df_ligacoes_filtered[df_ligacoes_filtered['Tempo da ligação'] >= timedelta(minutes=1)])
    
    st.markdown(f"""
    <div class="metric-display">
        📞 Total de Ligações<br>
        <span style="font-size: 1.2rem; font-weight: 600;">{total_ligacoes:,}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if total_ligacoes > 0:
        taxa_atendimento = (ligacoes_atendidas / total_ligacoes) * 100
        st.markdown(f"""
        <div class="period-info">
            ✅ Atendimento: {taxa_atendimento:.1f}%<br>
            ({ligacoes_atendidas:,} de {total_ligacoes:,})
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

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
meta_con_rm = 2 * dias_selecionados
meta_con_rr = 0.7 * meta_con_rm
meta_con_ca = 0.5 * meta_con_rr

metas_consultor = {
    "Reuniões Marcadas": meta_con_rm,
    "Reuniões Realizadas": meta_con_rr,
    "Contratos Assinados": meta_con_ca
}

multiplicador_mes = mes_fim - mes_inicio + 1


# Meta acumulada = dias * meta_diária * número de consultores
metas_acumuladas = {
    etapa: valor_diario * n_consultores
    for etapa, valor_diario in metas_consultor.items()
}

projetar_dados_teste(
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
    dias_selecionados,
    data_inicio,
    data_fim
)