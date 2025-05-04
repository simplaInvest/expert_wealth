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
import time
from sidebar import setup_sidebar
from funcs import load_calls, format_data, get_last_30_days_data

st.set_page_config(page_title="Espectador", page_icon="👀", layout='wide')

# Configurar sidebar
setup_sidebar()

st.title("Modo Espectador")
st.write("Bem-vindo ao modo espectador do Dashboard.")

###########################################################################################################

###########################################################################################################

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        today_start = datetime.now().replace(hour=0, minute=0, second=1, microsecond=0)  # Hoje 00:00:01
        tomorrow_start = today_start + timedelta(days=1)  # Amanhã 00:00:01

        # Filtrar dados de hoje
        filtered_data_today = filtered_data[
            (filtered_data['connect_time'] >= today_start) & 
            (filtered_data['connect_time'] < tomorrow_start)
        ]

        # Contagem de SDRs
        sdr_counts = filtered_data_today['CLI'].value_counts().sort_values(ascending=True).reset_index()
        sdr_counts.columns = ['SDR', 'Número de Ligações']

        if not sdr_counts.empty:
            # Criar gráfico
            bar_fig = px.bar(
                sdr_counts, 
                x='Número de Ligações',
                y='SDR',
                orientation='h', 
                title='Ligações hoje',
                text='Número de Ligações'
            )

            # Adicionar linha média
            avg_calls = sdr_counts["Número de Ligações"].mean()
            bar_fig.add_shape(
                type='line',
                x0=avg_calls, y0=-0.5, x1=avg_calls, y1=len(sdr_counts) - 0.5,
                line=dict(color='red', width=2, dash='dot')
            )
            bar_fig.add_annotation(
                x=avg_calls, y=len(sdr_counts) - 0.5, text=f"Média: {avg_calls:.2f}",
                showarrow=True, arrowhead=2, ax=0, ay=-40, bgcolor="red"
            )

            # Exibir gráfico
            st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.warning("Nenhum dado disponível para exibição no gráfico.")

    with st.container(border=True):
        sdr_counts = filtered_data['CLI'].value_counts().sort_values(ascending=True).reset_index()
        sdr_counts.columns = ['SDR', 'Número de Ligações']

        if not sdr_counts.empty:
            bar_fig = px.bar(
                sdr_counts, 
                x='Número de Ligações',
                y='SDR',
                orientation='h', 
                title='Ligações nos últimos 30 dias',
                text='Número de Ligações'
            )
            avg_calls = sdr_counts["Número de Ligações"].mean()
            bar_fig.add_shape(
                type='line',
                x0=avg_calls, y0=-0.5, x1=avg_calls, y1=len(sdr_counts) - 0.5,
                line=dict(color='red', width=2, dash='dot')
            )
            bar_fig.add_annotation(
                x=avg_calls, y=len(sdr_counts) - 0.5, text=f"Média: {avg_calls:.2f}",
                showarrow=True, arrowhead=2, ax=0, ay=-40, bgcolor="red"
            )

            st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.warning("Nenhum dado disponível para exibição no gráfico.")

with col2:
    filtered_data_1_min = filtered_data_today[filtered_data_today['call_time'] >= timedelta(minutes=1)]
    with st.container(border=True):
        sdr_counts = filtered_data_1_min['CLI'].value_counts().sort_values(ascending=True).reset_index()
        sdr_counts.columns = ['SDR', 'Número de Ligações']

        if not sdr_counts.empty:
            bar_fig = px.bar(
                sdr_counts, 
                x='Número de Ligações',
                y='SDR',
                orientation='h', 
                title='Ligações atendidas hoje',
                text='Número de Ligações'
            )

            avg_calls = sdr_counts["Número de Ligações"].mean()
            bar_fig.add_shape(
                type='line',
                x0=avg_calls, y0=-0.5, x1=avg_calls, y1=len(sdr_counts) - 0.5,
                line=dict(color='red', width=2, dash='dot')
            )
            bar_fig.add_annotation(
                x=avg_calls, y=len(sdr_counts) - 0.5, text=f"Média: {avg_calls:.2f}",
                showarrow=True, arrowhead=2, ax=0, ay=-40, bgcolor="red"
            )

            st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.warning("Nenhum dado disponível para exibição no gráfico.")

    filtered_data_1_min_30days = filtered_data.loc[filtered_data['call_time'] >= timedelta(minutes=1)]
    with st.container(border=True):
        sdr_counts = filtered_data_1_min_30days['CLI'].value_counts().sort_values(ascending=True).reset_index()
        sdr_counts.columns = ['SDR', 'Número de Ligações']

        if not sdr_counts.empty:
            bar_fig = px.bar(
                sdr_counts, 
                x='Número de Ligações',
                y='SDR',
                orientation='h', 
                title='Ligações atendidas nos últimos 30 dias',
                text='Número de Ligações'
            )

            avg_calls = sdr_counts["Número de Ligações"].mean()
            bar_fig.add_shape(
                type='line',
                x0=avg_calls, y0=-0.5, x1=avg_calls, y1=len(sdr_counts) - 0.5,
                line=dict(color='red', width=2, dash='dot')
            )
            bar_fig.add_annotation(
                x=avg_calls, y=len(sdr_counts) - 0.5, text=f"Média: {avg_calls:.2f}",
                showarrow=True, arrowhead=2, ax=0, ay=-40, bgcolor="red"
            )

            st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.warning("Nenhum dado disponível para exibição no gráfico.")
