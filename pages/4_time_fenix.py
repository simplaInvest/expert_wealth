import streamlit as st
from sidebar import setup_sidebar  # Importa a sidebar
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
from funcs import load_calls, format_data

st.set_page_config(page_title="Time Fênix", page_icon="🐦", layout="wide")

# Verifica autenticação
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Acesso negado. Faça login para acessar esta página.")
    st.switch_page("main.py")

# Permite acesso se for admin ou líder do Time fenix
if st.session_state.user_type == "admin" or (st.session_state.user_type == "líder" and st.session_state.team == "time_fenix"):
    
    # Exibe a sidebar configurada corretamente
    setup_sidebar()

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("time_fnx.png", use_container_width=True)


    # Conteúdo da página
    st.title("Painel do Time Fênix")
    st.write("Bem-vinda à página do Time Fênix, Fernanda.")

else:
    st.warning("Acesso negado.")
    st.switch_page("main.py")

df_ligacoes = st.session_state.get("df_chamadas")

# Carrega os dados e formata
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

    # Filtra o DataFrame com base nas datas selecionadas
    filtered_data = df_ligacoes[
        (df_ligacoes["Início da ligação"] >= start_date) &
        (df_ligacoes["Início da ligação"] <= end_date)
    ]

    st.write(f"Exibindo {len(filtered_data)} chamadas entre {start_date.date()} e {end_date.date()}")
    


# filtrar somente os membros do time
col_to_filter = [
        '2016 (3231420318 - Victor Corrêa)',
        '2018 (3231420386 - Débora Bordonal)',
        '2014 (3231420112 - Douglas Santos)',
        '2020 (3231420387 - Victor Hugo)',
        '2015 (3231420113 - Marlon Mendes)'
    ]

filtered_data = filtered_data.loc[filtered_data['Usuário'].isin(col_to_filter)]

with cols_filters[1]:
    sdrs_dict = {
        '2016 (3231420318 - Victor Corrêa)' : 'Victor C',
        '2018 (3231420386 - Débora Bordonal)': 'Débora',
        '2014 (3231420112 - Douglas Santos)': 'Douglas',
        '2020 (3231420387 - Victor Hugo)': 'Victor H',
        '2015 (3231420113 - Marlon Mendes)': 'Marlon'
    }
    
    # Lista apenas os nomes para exibição
    sdr_name = ["Visão Geral"] + list(sdrs_dict.values())

    selected_sdr_name = st.selectbox("Escolha um SDR", sdr_name, help="Escolha o SDR que quer analisar")

    if selected_sdr_name != "Visão Geral":
        # Obtém a chave (Usuário) correspondente ao nome escolhido
        selected_sdr = next(cli for cli, name in sdrs_dict.items() if name == selected_sdr_name)
        
        # Filtra os dados com base no Usuário correspondente
        filtered_data = filtered_data[filtered_data['Usuário'] == selected_sdr]

with cols_filters[2]:
    duration_options = ["Todos", "Zero", "Menos de 1 min", "Mais de 1 min", "Mais de 2 min"]
    selected_durations = st.multiselect("Escolha a duração das chamadas", duration_options, help="")
    
    if selected_durations:
        duration_filters = []
        if "Zero" in selected_durations:
            duration_filters.append(filtered_data['call_time'] == timedelta(seconds=0))
        if "Menos de 1 min" in selected_durations:
            duration_filters.append((filtered_data['call_time'] > timedelta(seconds=0)) & 
                                    (filtered_data['call_time'] < timedelta(minutes=1)))
        if "Mais de 1 min" in selected_durations:
            duration_filters.append(filtered_data['call_time'] >= timedelta(minutes=1))
        if "Mais de 2 min" in selected_durations:
            duration_filters.append(filtered_data['call_time'] >= timedelta(minutes=2))
        if "Todos" in selected_durations:
            duration_filters.append(filtered_data['call_time'] >= timedelta(minutes=0))
        filtered_data = filtered_data[pd.concat(duration_filters, axis=1).any(axis=1)]

st.divider()

cols_grafs = st.columns(2)

with cols_grafs[0].container():
    # Obter contagem de valores e ordenar em ordem decrescente
    sdr_counts = filtered_data['Usuário'].value_counts().sort_values(ascending=True)
    
    df_sdr = sdr_counts.reset_index()
    df_sdr.columns = ['SDR', 'Número de Ligações']
    bar_fig = px.bar(
        df_sdr, 
        x='Número de Ligações', 
        y='SDR', 
        orientation='h',
        title='Número de Ligações por SDR', 
        text='Número de Ligações'
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
        x=avg_calls, y=len(sdr_counts) - 0.5, text=f'Média: {avg_calls:.2f}',
        showarrow=True, arrowhead=2, ax=0, ay=-40,
        bgcolor='red'
    )
    
    # Ajustar o formato do texto nas barras
    bar_fig.update_traces(textposition='outside')  # Posição do texto fora das barras
    
    # Exibir o gráfico
    st.plotly_chart(bar_fig, use_container_width=True)


with cols_grafs[1].container():
    # Converter o tempo para horas decimais
    filtered_data['Hora'] = filtered_data['Início da ligação'].dt.hour + filtered_data['Início da ligação'].dt.minute / 60
    
    # Criar o histograma com os valores exibidos em cada barra
    hist_fig = px.histogram(
        filtered_data, 
        x='Hora', 
        nbins=14, 
        title='Distribuição de Ligações por Hora do Dia',
        labels={'Hora': 'Hora do Dia'}, 
        range_x=[7, 25],
        text_auto=True  # Exibe os valores diretamente nas barras
    )
    
    # Configurações visuais para o histograma
    hist_fig.update_traces(marker_line_width=2, marker_line_color='black')  # Borda das barras
    hist_fig.update_traces(textposition='outside')  # Posiciona os textos fora das barras
    
    # Ajuste do eixo x para exibir intervalos de 1 hora
    hist_fig.update_layout(xaxis=dict(tickmode='linear', dtick=1))
    
    # Exibir o gráfico no Streamlit
    st.plotly_chart(hist_fig, use_container_width=True)

# Gera o gráfico principal
filtered_data['Data'] = filtered_data['Início da ligação'].dt.date
line_data = filtered_data.groupby('Data').size().reset_index(name='counts')
line_fig = px.line(line_data, x='Data', y='counts', markers=True, title='Número de Ligações ao Longo do Tempo')

# Adiciona as linhas de cada SDR com o nome simplificado na legenda
if selected_sdr_name == "Visão Geral":
    for sdr in col_to_filter:
        sdr_data = filtered_data[filtered_data['Usuário'] == sdr]
        sdr_line_data = sdr_data.groupby('Data').size().reset_index(name='counts')
        if not sdr_line_data.empty:  # Adiciona apenas se houver dados
            line_fig.add_scatter(
                x=sdr_line_data['Data'],
                y=sdr_line_data['counts'],
                mode='lines+markers',
                name=sdrs_dict[sdr]  # Usa apenas o nome do SDR
            )

# Renderiza o gráfico no Streamlit
st.plotly_chart(line_fig, use_container_width=True)

st.dataframe(filtered_data)