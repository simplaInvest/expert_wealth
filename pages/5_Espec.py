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

st.set_page_config(page_title="Espectador", page_icon="👀", layout = 'wide')

# Se o usuário estiver logado, exibe a sidebar
# Chama a sidebar
setup_sidebar()


st.title("Modo Espectador")
st.write("Bem-vindo ao modo espectador do Dashboard.")

###########################################################################################################
#                                Carregar dados

if st.button("Limpar Cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("Cache limpo! Recarregue os dados.")

filtered_data = get_last_30_days_data()

st.dataframe(filtered_data)

###########################################################################################################

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        from datetime import datetime, timedelta
        import plotly.express as px
        import streamlit as st

        # Obter data de hoje e amanhã
        today_start = datetime.now().replace(hour=0, minute=0, second=1, microsecond=0)  # Hoje 00:00:01
        tomorrow_start = today_start + timedelta(days=1)  # Amanhã 00:00:01

        # Criar subdataset com chamadas feitas hoje
        filtered_data_today = filtered_data[
            (filtered_data['connect_time'] >= today_start) & 
            (filtered_data['connect_time'] < tomorrow_start)
        ]

        # Contagem de valores e ordenação
        sdr_counts = filtered_data_today['CLI'].value_counts().sort_values(ascending=True)

        # Criar o gráfico de barras com os valores exibidos em cada barra
        bar_fig = px.bar(
            sdr_counts, 
            orientation='h', 
            title='Ligações hoje', 
            labels={'index': 'SDR', 'value': 'Número de Ligações'},
            text=sdr_counts  # Adiciona os valores das barras
        )

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

        # Ajustar o formato do texto nas barras
        bar_fig.update_traces(textposition='outside')  # Posição do texto fora das barras

        # Exibir o gráfico
        st.plotly_chart(bar_fig, use_container_width=True, key="chart_today")

    
    with st.container(border=True):
        # Obter contagem de valores e ordenar em ordem decrescente
        sdr_counts = filtered_data['CLI'].value_counts().sort_values(ascending=True)
        
        # Criar o gráfico de barras com os valores exibidos em cada barra
        bar_fig = px.bar(
            sdr_counts, 
            orientation='h', 
            title='Ligações nos últimos 30 dias', 
            labels={'index': 'SDR', 'value': 'Número de Ligações'},
            text=sdr_counts  # Adiciona os valores das barras
        )
        
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
        
        # Ajustar o formato do texto nas barras
        bar_fig.update_traces(textposition='outside')  # Posição do texto fora das barras
        
        # Exibir o gráfico
        st.plotly_chart(bar_fig, use_container_width=True, key="chart_30_days")

with col2:
    filtered_data_1_min = filtered_data_today[filtered_data['call_time'] >= timedelta(minutes=1)]
    with st.container(border=True):
        # Contagem de valores e ordenação
        sdr_counts = filtered_data_1_min['CLI'].value_counts().sort_values(ascending=True)

        # Criar o gráfico de barras com os valores exibidos em cada barra
        bar_fig = px.bar(
            sdr_counts, 
            orientation='h', 
            title='Ligações atendidas hoje', 
            labels={'index': 'SDR', 'value': 'Número de Ligações'},
            text=sdr_counts  # Adiciona os valores das barras
        )

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

        # Ajustar o formato do texto nas barras
        bar_fig.update_traces(textposition='outside')  # Posição do texto fora das barras

        # Exibir o gráfico
        st.plotly_chart(bar_fig, use_container_width=True, key="chart_today_1_min")

    filtered_data_1_min_30days = filtered_data[filtered_data['call_time'] >= timedelta(minutes=1)]
    with st.container(border=True):
        # Contagem de valores e ordenação
        sdr_counts = filtered_data_1_min_30days['CLI'].value_counts().sort_values(ascending=True)

        # Criar o gráfico de barras com os valores exibidos em cada barra
        bar_fig = px.bar(
            sdr_counts, 
            orientation='h', 
            title='Ligações atendidas nos últimos 30 dias', 
            labels={'index': 'SDR', 'value': 'Número de Ligações'},
            text=sdr_counts  # Adiciona os valores das barras
        )

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

        # Ajustar o formato do texto nas barras
        bar_fig.update_traces(textposition='outside')  # Posição do texto fora das barras

        # Exibir o gráfico
        st.plotly_chart(bar_fig, use_container_width=True, key="chart_30days_1_min")
