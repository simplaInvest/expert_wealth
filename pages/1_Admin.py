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

from funcs import load_calls, format_data, preparar_dataframe, carregar_planilha
from sidebar import setup_sidebar

##############################
##      Início do Layout    ##
##############################

st.set_page_config(page_title="Admin", page_icon="🔧", layout = 'wide')

# Verifica autenticação
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Acesso negado. Faça login para acessar esta página.")
    st.switch_page("main.py")

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
    

# Continuação do código para filtros e gráficos
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
        '1023 (3231420382 - Douglas)',
        '1025 (3231420383 - Tiago)'
    ]
    consultores = [
        '2016 (3231420318 - Victor Corrêa)',
        '2018 (3231420386 - Débora Bordonal)',
        '2014 (3231420112 - Douglas Santos)',
        '2020 (3231420387 - Victor Hugo)',
        '2015 (3231420113 - Marlon Mendes)',
        '1021 (3231420381 - Felipe Altmann)',
        '1023 (3231420382 - Rafael Sanchez)',
        '2017 (3231420384 - Paula Leitão)',
        '2021 (3231420388 - Bruno Veiga)'
    ]
    trainees = [
        '2024 (3231420114 - Gabriel Soares)',
        '2025 (3231420311 - Alexander Neto)',
        '2026 (3231420160 - Leonnardo Gomes)',
        '2027 (3231420161 - Mateus Lage)',
        '2028 (3231420162 - Gustavo Nogueira)',
        '2029 (3231420163 - Emily Rocha)'
    ]

    type_of_operator = st.radio("Escolha quem quer analisar:", ['SDRs', 'Consultores'], horizontal = True)
    if type_of_operator == 'SDRs':
        selected_sdr = st.selectbox("Escolha um SDR", ["Visão Geral"] + sdrs, help="Escolha o SDR que quer analisar")
    elif type_of_operator == 'Consultores':
        selected_sdr = st.selectbox("Escolha um Consultor", ["Visão Geral"] + consultores, help="Escolha o Consultor que quer analisar")
    else:
        selected_sdr = st.selectbox("Escolha uma opção acima", ["Visão Geral"], help="Escolha uma das opções acima")
    
    if selected_sdr != "Visão Geral":
        filtered_data = filtered_data[filtered_data['Usuário'] == selected_sdr]
    

with cols_filters[2]:
    duration_options = ["Todos", "Zero", "Menos de 1 min", "Mais de 1 min", "Mais de 2 min"]
    selected_durations = st.multiselect("Escolha a duração das chamadas", duration_options, help="")
    
    if selected_durations:
        duration_filters = []
        if "Zero" in selected_durations:
            duration_filters.append(filtered_data['Tempo da ligação'] == timedelta(seconds=0))
        if "Menos de 1 min" in selected_durations:
            duration_filters.append((filtered_data['Tempo da ligação'] > timedelta(seconds=0)) & 
                                    (filtered_data['Tempo da ligação'] < timedelta(minutes=1)))
        if "Mais de 1 min" in selected_durations:
            duration_filters.append(filtered_data['Tempo da ligação'] >= timedelta(minutes=1))
        if "Mais de 2 min" in selected_durations:
            duration_filters.append(filtered_data['Tempo da ligação'] >= timedelta(minutes=2))
        if "Todos" in selected_durations:
            duration_filters.append(filtered_data['Tempo da ligação'] >= timedelta(minutes=0))
        filtered_data = filtered_data[pd.concat(duration_filters, axis=1).any(axis=1)]
    
st.divider()

tab1, tab2, tab3 = st.tabs(['SDRs', 'Consultores', 'Trainees'])

with tab1:
    filtered_data_sdrs = filtered_data.loc[filtered_data['Usuário'].isin(sdrs)]
    cols_grafs = st.columns(2)

    with cols_grafs[0].container():
        # Obter contagem de valores e ordenar em ordem decrescente
        sdr_counts = filtered_data_sdrs['Usuário'].value_counts().sort_values(ascending=True)
        
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
        filtered_data_sdrs['Hora'] = filtered_data_sdrs['Início da ligação'].dt.hour + filtered_data_sdrs['Início da ligação'].dt.minute / 60
        
        # Criar o histograma com os valores exibidos em cada barra
        hist_fig = px.histogram(
            filtered_data_sdrs, 
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

    sdr_names = {
        '1002 (3231420312 - Daniel)': 'Daniel',
        '1004 (3231420313 - Toledo)': 'Toledo',
        '1006 (3231420314 - Pedro Vieira)': 'Pedro Vieira',
        '1008 (3231420315 - Saint Clair)': 'Saint Clair',
        '1010 (3231420316 - Rúbio)': 'Rúbio',
        '1012 (3231420310 - Marioti)': 'Marioti',
        '1014 (3231420317 - Gustavo B)': 'Gustavo B',
        '1015 (3231420319 - Gabriel)': 'Gabriel',
        '1018 (3231420380 - Micaelli)': 'Micaelli',
        '1021 (3231420381 - Felipe Altmann)': 'Felipe Altmann',
        '1023 (3231420382 - Douglas)': 'Douglas',
        '1025 (3231420383 - Tiago)': 'Tiago'
    }

    # Gera o gráfico principal
    filtered_data_sdrs['Data'] = filtered_data_sdrs['Início da ligação'].dt.date
    line_data = filtered_data_sdrs.groupby('Data').size().reset_index(name='counts')
    line_fig = px.line(line_data, x='Data', y='counts', markers=True, title='Número de Ligações ao Longo do Tempo')

    # Adiciona as linhas de cada SDR com o nome simplificado na legenda
    if selected_sdr == "Visão Geral":
        for sdr in sdrs:
            sdr_data = filtered_data_sdrs[filtered_data_sdrs['Usuário'] == sdr]
            sdr_line_data = sdr_data.groupby('Data').size().reset_index(name='counts')
            if not sdr_line_data.empty:  # Adiciona apenas se houver dados
                line_fig.add_scatter(
                    x=sdr_line_data['Data'],
                    y=sdr_line_data['counts'],
                    mode='lines+markers',
                    name=sdr_names[sdr]  # Usa apenas o nome do SDR
                )

    # Renderiza o gráfico no Streamlit
    st.plotly_chart(line_fig, use_container_width=True)

    st.dataframe(filtered_data_sdrs)

with tab2:
    filtered_data_consultores = filtered_data.loc[filtered_data['Usuário'].isin(consultores)]
    cols_grafs = st.columns(2)

    with cols_grafs[0].container():
        # Obter contagem de valores e ordenar em ordem decrescente
        consultor_counts = filtered_data_consultores['Usuário'].value_counts().sort_values(ascending=True)
        
        df_consultor = consultor_counts.reset_index()
        df_consultor.columns = ['Consultor', 'Número de Ligações']
        bar_fig = px.bar(
            df_consultor, 
            x='Número de Ligações', 
            y='Consultor', 
            orientation='h',
            title='Número de Ligações por Consultor', 
            text='Número de Ligações'
        )
        
        # Calcular a média das ligações por consultor
        avg_calls = consultor_counts.mean()
        
        # Adicionar linha vertical pontilhada vermelha para a média
        bar_fig.add_shape(
            type='line',
            x0=avg_calls, y0=-0.5, x1=avg_calls, y1=len(consultor_counts) - 0.5,
            line=dict(color='red', width=2, dash='dot')
        )
        
        # Adicionar anotação para o valor da média no eixo x
        bar_fig.add_annotation(
            x=avg_calls, y=len(consultor_counts) - 0.5, text=f'Média: {avg_calls:.2f}',
            showarrow=True, arrowhead=2, ax=0, ay=-40,
            bgcolor='red'
        )
        
        # Ajustar o formato do texto nas barras
        bar_fig.update_traces(textposition='outside')  # Posição do texto fora das barras
        
        # Exibir o gráfico
        st.plotly_chart(bar_fig, use_container_width=True)


    with cols_grafs[1].container():
        # Converter o tempo para horas decimais
        filtered_data_consultores['Hora'] = filtered_data_consultores['Início da ligação'].dt.hour + filtered_data_consultores['Início da ligação'].dt.minute / 60
        
        # Criar o histograma com os valores exibidos em cada barra
        hist_fig = px.histogram(
            filtered_data_consultores, 
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
        st.plotly_chart(hist_fig, use_container_width=True, key="hist_duracao")

    consultores_names = {
        '2016 (3231420318 - Victor Corrêa)' : 'Victor C',
        '2018 (3231420386 - Débora Bordonal)': 'Débora',
        '2014 (3231420112 - Douglas Santos)': 'Douglas',
        '2020 (3231420387 - Victor Hugo)': 'Victor H',
        '2015 (3231420113 - Marlon Mendes)': 'Marlon',
        '1021 (3231420381 - Felipe Altmann)': 'Felipe Altmann',
        '1023 (3231420382 - Rafael Sanchez)': 'Rafael Sanchez',
        '2017 (3231420384 - Paula Leitão)': 'Paula Leitão',
        '2021 (3231420388 - Bruno Veiga)': 'Bruno Veiga'
    }

    # Gera o gráfico principal
    filtered_data_consultores['Data'] = filtered_data_consultores['Início da ligação'].dt.date
    line_data = filtered_data_consultores.groupby('Data').size().reset_index(name='counts')
    line_fig = px.line(line_data, x='Data', y='counts', markers=True, title='Número de Ligações ao Longo do Tempo')

    # Adiciona as linhas de cada consultor com o nome simplificado na legenda
    if selected_sdr == "Visão Geral":
        for consultor in consultores:
            consultor_data = filtered_data_consultores[filtered_data_consultores['Usuário'] == consultor]
            consultor_line_data = consultor_data.groupby('Data').size().reset_index(name='counts')
            if not consultor_line_data.empty:  # Adiciona apenas se houver dados
                line_fig.add_scatter(
                    x=consultor_line_data['Data'],
                    y=consultor_line_data['counts'],
                    mode='lines+markers',
                    name=consultores_names[consultor]  # Usa apenas o nome do consultor
                )

    # Renderiza o gráfico no Streamlit
    st.plotly_chart(line_fig, use_container_width=True, key="line_fig")

    st.dataframe(filtered_data_consultores)

with tab3:
    filtered_data_trainees = filtered_data.loc[filtered_data['Usuário'].isin(trainees)]
    cols_grafs = st.columns(2)

    with cols_grafs[0].container():
        # Obter contagem de valores e ordenar em ordem decrescente
        trainee_counts = filtered_data_trainees['Usuário'].value_counts().sort_values(ascending=True)
        
        df_trainee = trainee_counts.reset_index()
        df_trainee.columns = ['trainee', 'Número de Ligações']
        bar_fig = px.bar(
            df_trainee, 
            x='Número de Ligações', 
            y='trainee', 
            orientation='h',
            title='Número de Ligações por trainee', 
            text='Número de Ligações'
        )
        
        # Calcular a média das ligações por trainee
        avg_calls = trainee_counts.mean()
        
        # Adicionar linha vertical pontilhada vermelha para a média
        bar_fig.add_shape(
            type='line',
            x0=avg_calls, y0=-0.5, x1=avg_calls, y1=len(trainee_counts) - 0.5,
            line=dict(color='red', width=2, dash='dot')
        )
        
        # Adicionar anotação para o valor da média no eixo x
        bar_fig.add_annotation(
            x=avg_calls, y=len(trainee_counts) - 0.5, text=f'Média: {avg_calls:.2f}',
            showarrow=True, arrowhead=2, ax=0, ay=-40,
            bgcolor='red'
        )
        
        # Ajustar o formato do texto nas barras
        bar_fig.update_traces(textposition='outside')  # Posição do texto fora das barras
        
        # Exibir o gráfico
        st.plotly_chart(bar_fig, use_container_width=True)


    with cols_grafs[1].container():
        # Converter o tempo para horas decimais
        filtered_data_trainees['Hora'] = filtered_data_trainees['Início da ligação'].dt.hour + filtered_data_trainees['Início da ligação'].dt.minute / 60
        
        # Criar o histograma com os valores exibidos em cada barra
        hist_fig = px.histogram(
            filtered_data_trainees, 
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
        st.plotly_chart(hist_fig, use_container_width=True, key="hist_duração2")

    trainees_names = {
        '2024 (3231420114 - Gabriel Soares)': 'Gabriel Soares',
        '2025 (3231420311 - Alexander Neto)': 'Alexander Neto',
        '2026 (3231420160 - Leonnardo Gomes)': 'Leo Gomes',
        '2027 (3231420161 - Mateus Lage)': 'Mateus Lage',
        '2028 (3231420162 - Gustavo Nogueira)': 'Gustavo N.',
        '2029 (3231420163 - Emily Rocha)': 'Emily Rocha'
    }

    # Gera o gráfico principal
    filtered_data_trainees['Data'] = filtered_data_trainees['Início da ligação'].dt.date
    line_data = filtered_data_trainees.groupby('Data').size().reset_index(name='counts')
    line_fig = px.line(line_data, x='Data', y='counts', markers=True, title='Número de Ligações ao Longo do Tempo')

    # Adiciona as linhas de cada trainee com o nome simplificado na legenda
    if selected_sdr == "Visão Geral":
        for trainee in trainees:
            trainee_data = filtered_data_trainees[filtered_data_trainees['Usuário'] == trainee]
            trainee_line_data = trainee_data.groupby('Data').size().reset_index(name='counts')
            if not trainee_line_data.empty:  # Adiciona apenas se houver dados
                line_fig.add_scatter(
                    x=trainee_line_data['Data'],
                    y=trainee_line_data['counts'],
                    mode='lines+markers',
                    name=trainees_names[trainee]  # Usa apenas o nome do trainee
                )

    # Renderiza o gráfico no Streamlit
    st.plotly_chart(line_fig, use_container_width=True, key="line_fig2")

    st.dataframe(filtered_data_trainees)