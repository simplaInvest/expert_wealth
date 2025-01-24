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

from funcs import load_calls, format_data

##############################
##      Sistema de Login    ##
##############################

# Configurar a página
st.set_page_config(page_title="Main_page", layout="wide")

# Definir a senha
CORRECT_PASSWORD = "rumoaobi"

# Usar o estado da sessão para verificar login
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    # Tela de login
    st.title("Expert Comercial Wealth - Login")
    st.subheader("Insira a senha para acessar o dashboard.")
    
    # Campo de entrada de senha
    password = st.text_input("Senha", type="password")
    
    # Botão para enviar a senha
    if st.button("Entrar"):
        if password == CORRECT_PASSWORD:
            st.session_state["authenticated"] = True
            st.success("Login bem-sucedido! Redirecionando...")
        else:
            st.error("Senha incorreta. Tente novamente.")
else:
    ##############################
    ##      Início do Layout    ##
    ##############################

    st.title("Expert Comercial Wealth")

    cols_filters = st.columns(3)

    # Filtrar por data
    with cols_filters[0]:
        # Define valores padrão: hoje e amanhã
        default_start_date = datetime.now().date()  # Hoje
        default_end_date = (datetime.now() + timedelta(days=1)).date()  # Amanhã

        # Solicita que o usuário selecione um intervalo de datas
        date_range = st.date_input(
            "Selecione o intervalo de datas",
            value=(default_start_date, default_end_date),  # Valores padrão
            help="Escolha a data inicial e a data final"
        )

        # Verifica se o intervalo de datas é válido e converte para datetime
        if isinstance(date_range, tuple) and len(date_range) == 2:
            # Converte as datas selecionadas para datetime com hora 00:00:00
            start_date = datetime.combine(date_range[0], datetime.min.time())
            end_date = datetime.combine(date_range[1], datetime.min.time())
        else:
            st.warning("Por favor, selecione um intervalo válido.")

        filtered_data = format_data(load_calls(start_date, end_date))

    with cols_filters[1]:
        sdrs = [
            '1002 (3231420312 - Daniel)',
            '1004 (3231420313 - Toledo)',
            '1006 (3231420314 - Pedro Vieira)',
            '1008 (3231420315 - Saint Clair)',
            '1010 (3231420316 - Rúbio)',
            '1012 (3231420310 - Marioti)',
            '1014 (3231420317 - Gustavo B)',
            '1015 (3231420319 - Gabriel)',
            '1018 (3231420380 - Micaelli)',
            '1021 (3231420381 - Lucas)',
            '1023 (3231420382 - Douglas)',
            '1025 (3231420383 - Tiago)'
        ]
        selected_sdr = st.selectbox("Escolha um SDR", ["Visão Geral"] + sdrs, help="Escolha o SDR que quer analisar")

        if selected_sdr != "Visão Geral":
            filtered_data = filtered_data[filtered_data['CLI'] == selected_sdr]

    with cols_filters[2]:
        duration_options = ["Zero", "Menos de 1 min", "Mais de 1 min", "Mais de 2 min"]
        selected_durations = st.multiselect("Escolha a duração das chamadas", duration_options, help="Não está funcionando ainda")

    st.divider()

    cols_grafs = st.columns(3)

    with cols_grafs[0].container():
        sdr_counts = filtered_data['CLI'].value_counts()
        bar_fig = px.bar(sdr_counts, orientation='h', title='Número de Ligações por SDR', labels={'index': 'SDR', 'value': 'Número de Ligações'})

        # Calcular a média das ligações por SDR
        avg_calls = sdr_counts.mean()

        # Adicionar linha vertical pontilhada vermelha para a média
        bar_fig.add_shape(
            type='line',
            x0=avg_calls, y0=-0.5, x1=avg_calls, y1=len(sdr_counts) - 0.5,
            line=dict(color='red', width=2, dash='dot')
        )

        # Adicionar anotação para o valor da média no eixo x
        bar_fig.add_annotation(
            x=avg_calls, y=len(sdr_counts) - 0.5, text=f"Média: {avg_calls:.2f}",
            showarrow=True, arrowhead=2, ax=0, ay=-40,
            bgcolor="red"
        )

        st.plotly_chart(bar_fig, use_container_width=True)

    with cols_grafs[1].container():
        filtered_data['Data'] = filtered_data['connect_time'].dt.date
        line_data = filtered_data.groupby('Data').size().reset_index(name='counts')
        line_fig = px.line(line_data, x='Data', y='counts', markers=True, title='Número de Ligações ao Longo do Tempo')
        if selected_sdr == "Visão Geral":
            for sdr in sdrs:
                sdr_data = filtered_data[filtered_data['CLI'] == sdr]
                sdr_line_data = sdr_data.groupby('Data').size().reset_index(name=sdr)
                line_fig.add_scatter(x=sdr_line_data['Data'], y=sdr_line_data[sdr], mode='lines+markers', name=sdr)

        st.plotly_chart(line_fig, use_container_width=True)

    with cols_grafs[2].container():
        filtered_data['Hora'] = filtered_data['connect_time'].dt.hour + filtered_data['connect_time'].dt.minute / 60
        hist_fig = px.histogram(filtered_data, x='Hora', nbins=14, title='Distribuição de Ligações por Hora do Dia',
                                labels={'Hora': 'Hora do Dia'}, range_x=[7, 25])
        hist_fig.update_traces(marker_line_width=2, marker_line_color='black')
        hist_fig.update_layout(xaxis=dict(tickmode='linear', dtick=1))
        st.plotly_chart(hist_fig, use_container_width=True)
