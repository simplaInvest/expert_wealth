import json 
import requests # type: ignore
import os
import datetime
from datetime import date, timedelta, datetime
import pandas as pd # type: ignore
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import time  # Para controle de atualização automática
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import time
import random
import re
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from streamlit_extras.metric_cards import style_metric_cards

def carregar_planilha(df_name, sheet_url: str, nome_aba: str = "Página1", forcar=False):
    if df_name not in st.session_state or forcar:
        # Autenticação
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        client = gspread.authorize(creds)

        # Acesso à aba
        sheet = client.open_by_url(sheet_url)
        aba = sheet.worksheet(nome_aba)

        # DataFrame
        data = aba.get_all_records()
        df = pd.DataFrame(data)

        # Armazenamento correto usando colchetes
        st.session_state[df_name] = df

    return st.session_state[df_name]

def preparar_dataframe(df):
    # Convertendo colunas de data e hora com vírgula
    df["Início da ligação"] = pd.to_datetime(df["Início da ligação"], format="%d/%m/%Y, %H:%M:%S", errors="coerce")
    df["Fim da ligação"] = pd.to_datetime(df["Fim da ligação"], format="%d/%m/%Y, %H:%M:%S", errors="coerce")
    df["Atualizado em"] = pd.to_datetime(df["Atualizado em"], format="%d/%m/%Y, %H:%M:%S", errors="coerce")

    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce").dt.date
    df["Hora"] = pd.to_datetime(df["Hora"], format="%H:%M:%S", errors="coerce").dt.time

    # Convertendo duração da planilha para timedelta (opcional)
    df["Tempo da ligação"] = pd.to_timedelta(df["Tempo da ligação"], errors="coerce")

    # Calculando a duração real com base nas datas
    df["call_time"] = df["Fim da ligação"] - df["Início da ligação"]

    # Extraindo nome do operador de "Usuário"
    df["Operador"] = df["Usuário"].str.extract(r"-\s*(.+?)\)$")

    return df

def adicionar_time(df_name, df_evento, df_metas):
    # Faz merge com base no nome
    df_times = df_metas[["CONSULTOR", "TIME"]].drop_duplicates()
    df_merged = df_evento.merge(df_times, on="CONSULTOR", how="left")

    # Remove linhas sem TIME
    df_merged = df_merged.dropna(subset=["TIME"])

    # Atualiza o session_state
    st.session_state[df_name] = df_merged

    return df_merged

def carregar_dataframes():

    planilhas_com_erro = []

    try:
        df_ligacoes = carregar_planilha("df_ligacoes", "https://docs.google.com/spreadsheets/d/17b9kaTH9TjSg2b32m0iHqxKF4XGWC9g6Cl2xl4VdivY/edit?usp=sharing", "LIGACOES", forcar=True)
        df_ligacoes = preparar_dataframe(df_ligacoes)
    except Exception as e:
        planilhas_com_erro.append(f"Histórico de chamadas: {e}")

    try:
        df_metas_individuais = carregar_planilha('df_metas_individuais','https://docs.google.com/spreadsheets/d/1244uV01S0_-64JI83kC7qv7ndzbL8CzZ6MvEu8c68nM/edit?usp=sharing', 'Metas_individuais', forcar=True)
    except Exception as e:
        planilhas_com_erro.append(f"Metas_individuais: {e}")

    try:
        df_rmarcadas = carregar_planilha('df_rmarcadas','https://docs.google.com/spreadsheets/d/1h7sQ7Q92ve5vA-MYxZF5srGYnlME8rfgkiKNNJQBbQk/edit?usp=sharing', 'R.MARCADAS', forcar=True)
        df_rmarcadas = adicionar_time('df_rmarcadas',df_rmarcadas, df_metas_individuais)
    except Exception as e:
        planilhas_com_erro.append(f"R.MARCADAS: {e}")
    
    try:
        df_rrealizadas = carregar_planilha('df_rrealizadas','https://docs.google.com/spreadsheets/d/1h7sQ7Q92ve5vA-MYxZF5srGYnlME8rfgkiKNNJQBbQk/edit?usp=sharing', 'R.REALIZADAS', forcar=True)
        df_rrealizadas = adicionar_time('df_rrealizadas',df_rrealizadas, df_metas_individuais)
    except Exception as e:
        planilhas_com_erro.append(f"R.REALIZADAS: {e}")
    
    try:
        df_cassinados = carregar_planilha('df_cassinados','https://docs.google.com/spreadsheets/d/1h7sQ7Q92ve5vA-MYxZF5srGYnlME8rfgkiKNNJQBbQk/edit?usp=sharing', 'C.ASSINADOS', forcar=True)
        df_cassinados = adicionar_time('df_cassinados',df_cassinados, df_metas_individuais)
    except Exception as e:
        planilhas_com_erro.append(f"C.ASSINADOS: {e}")

    try:
        df_captação = carregar_planilha('df_captação','https://docs.google.com/spreadsheets/d/1KmMdB6he5iqORaGa1QuBwaihSvR44LpUHWGGw_mfx_U/edit?usp=sharing', 'RANKING - DASH', forcar=True)
    except Exception as e:
        planilhas_com_erro.append(f"Captação: {e}")
    
    try:
        df_sdr = carregar_planilha('df_sdr', 'https://docs.google.com/spreadsheets/d/1Ex8pPnRyvN_A_5BBA7HgR26un1jyYs7DNYDt7NPqGus/edit?usp=sharing', 'DADOS REUNIOES', forcar=True)
    except Exception as e:
        planilhas_com_erro.append(f"Dados_SDR: {e}")

    try:
        df_discadora = carregar_planilha('df_discadora', 'https://docs.google.com/spreadsheets/d/1Ex8pPnRyvN_A_5BBA7HgR26un1jyYs7DNYDt7NPqGus/edit?usp=sharing', 'DADOS DISCADORA', forcar=True)
    except Exception as e:
        planilhas_com_erro.append(f"Dados_Discadora: {e}")
    
    if planilhas_com_erro:
        st.error("Erro ao carregar as seguintes planilhas:")
        for erro in planilhas_com_erro:
            st.error(erro)
    else:
        st.success("Planilhas carregadas com sucesso!")

def precisa_atualizar():
    agora = time.time()
    ultima = st.session_state.get("ultima_atualizacao", 0)
    return (agora - ultima) > 900  # 15 minutos

def projetar_dados(
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
):
    # Layout reorganizado com duas colunas principais
    col_1, col_2, col_funil, col_leg = st.columns([1, 1, 3, 3])

    # Coluna 1: Ligações + Reuniões Marcadas
    with col_1:
        for nome, valor, meta in [
            ("Ligações", df_ligacoes_filtered.shape[0], multiplicador_mes * 5 * 100 * n_consultores),
            ("Reuniões Realizadas", valores["Reuniões Realizadas"], metas_acumuladas["Reuniões Realizadas"])
        ]:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=valor,
                number={'valueformat': ',.0f'},
                title={'text': nome, 'font': {'size': 18}},
                delta={'reference': meta},
                gauge={
                    'axis': {'range': [0, meta], 'tickwidth': 1, 'tickcolor': "gray"},
                    'bar': {'color': "rgba(0,0,0,0)"},
                    'steps': [
                        {'range': [0, 0.5 * meta], 'color': "#ff4d4d"},
                        {'range': [0.5 * meta, 0.8 * meta], 'color': "#ffd633"},
                        {'range': [0.8 * meta, meta], 'color': "#5cd65c"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 6},
                        'thickness': 1,
                        'value': valor
                    }
                }
            ))

            fig.update_layout(
                margin=dict(t=10, b=10, l=0, r=0),
                height=180
                )

            st.plotly_chart(fig, use_container_width=True)

    # Coluna 2: Reuniões Realizadas + Contratos Assinados
    with col_2:
        for nome in ["Reuniões Marcadas", "Contratos Assinados"]:
            valor = valores[nome]
            meta = metas_acumuladas[nome]
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=valor,
                title={'text': nome, 'font': {'size': 18}},
                delta={'reference': meta},
                gauge={
                    'axis': {'range': [0, meta], 'tickwidth': 1, 'tickcolor': "gray"},
                    'bar': {'color': "rgba(0,0,0,0)"},
                    'steps': [
                        {'range': [0, 0.5 * meta], 'color': "#ff4d4d"},
                        {'range': [0.5 * meta, 0.8 * meta], 'color': "#ffd633"},
                        {'range': [0.8 * meta, meta], 'color': "#5cd65c"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 6},
                        'thickness': 1,
                        'value': valor
                    }
                }
            ))
            fig.update_layout(
                margin=dict(t=10, b=10, l=0, r=0),
                height=180
                )
            
            st.plotly_chart(fig, use_container_width=True)

    # Coluna 3: Funil
    with col_funil:
        etapas = list(valores.keys())
        quantidades = list(valores.values())

        # Taxas de conversão entre etapas
        taxas = []
        for i in range(len(quantidades) - 1):
            de = quantidades[i]
            para = quantidades[i + 1]
            taxa = (para / de) * 100 if de > 0 else 0
            taxas.append(f"{taxa:.1f}%")

        # 🔧 AJUSTÁVEIS MANUALMENTE
        posicoes_y_etapas = [0.92, 0.55, 0.19]
        posicoes_y_taxas = [0.305, 0.687]

        # Criação do DataFrame base
        df_funnel = pd.DataFrame({
            "Etapa": etapas,
            "Quantidade": quantidades
        })

        # Gráfico base
        fig = px.funnel(
            df_funnel,
            y="Etapa",
            x="Quantidade",
            color_discrete_sequence=["#bfa94c"]
        )

        # Remove texto automático
        fig.update_traces(text=None)

        # Anotações: Etapas
        for etapa, y in zip(etapas, posicoes_y_etapas):
            fig.add_annotation(
                xref="paper", yref="paper",
                x=0.5, y=y,
                text=f"<b>{etapa}:</b>",
                showarrow=False,
                font=dict(size=18, color="#444444")
            )

        # Anotações: Taxas de conversão
        for i, y in enumerate(posicoes_y_taxas):
            fig.add_annotation(
                xref="paper", yref="paper",
                x=0.5, y=y,
                text=f"⬇️ {taxas[i-1]}",
                showarrow=False,
                font=dict(size=14, color="black")
            )

        # Layout final
        fig.update_layout(
            title="Funil de Conversão",
            font=dict(size=18),
            margin=dict(t=20, b=0, l=0, r=0),
            height=420,
            showlegend=False,
            yaxis=dict(showticklabels=False, title=None)
        )
        # Exibe no Streamlit
        st.plotly_chart(fig, use_container_width=True)

        conv_final = round((quantidades[-1]/quantidades[0])*100, 1) if quantidades[0] != 0 else 0
        st.markdown(
            f"""
            <div style='text-align: center; font-size: 18px; font-weight: bold;'>
                Conv total: ⬇️ {conv_final:.2f}%
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_leg:
        # Geração apenas dos dias úteis
        dias = pd.date_range(start=data_inicio, end=data_fim, freq='B')
        meta_individual = 2
        meta_diaria_ajustada = meta_individual * n_consultores

        # Conta quantas reuniões marcadas por dia útil
        df_dia = (
            df_rmarcadas_filtrado.groupby("DATA")["CONSULTOR"]
            .count()
            .reindex(dias.date, fill_value=0)
            .reset_index()
            .rename(columns={"index": "DATA", "CONSULTOR": "REALIZADO"})
        )

        # Converte datas para string (categorias no eixo X)
        df_dia["LABEL"] = df_dia["DATA"].apply(lambda d: d.strftime("%d/%m"))

        # Criação do gráfico
        fig = go.Figure()

        # Barras de reuniões marcadas
        fig.add_trace(go.Bar(
            x=df_dia["LABEL"],
            y=df_dia["REALIZADO"],
            name="Reuniões Marcadas",
            marker_color="#1c64f2",
            text=df_dia["REALIZADO"],
            textposition="outside",
        ))

        # Linha da meta diária ajustada
        fig.add_trace(go.Scatter(
            x=df_dia["LABEL"],
            y=[meta_diaria_ajustada] * len(df_dia),
            mode="lines",
            name="Meta Diária",
            line=dict(color="green", dash="dash")
        ))

        # Layout
        fig.update_layout(
            title="Reuniões Marcadas por Dia vs Meta",
            xaxis_title="Data (dias úteis)",
            yaxis=dict(
                title="Reuniões marcadas",
                range=[0, max(df_dia["REALIZADO"].max(), meta_diaria_ajustada) * 1.15]
            ),
            barmode='group',
            hovermode="x unified",
            showlegend=False,
            margin=dict(t=20, b=0, l=0, r=0),
            height=220
        )

        # Anotação da meta
        fig.add_annotation(
            xref="paper", yref="y",
            x=0.99, y=meta_diaria_ajustada,
            text=f"Meta diária: {meta_diaria_ajustada}",
            showarrow=False,
            font=dict(size=14, color="green"),
            bgcolor="white",
            bordercolor="green",
            borderwidth=1
        )

        # Exibe no Streamlit
        st.plotly_chart(fig, use_container_width=True)


        ###################################

        # 1. Geração das datas do período filtrado
        dias = pd.date_range(start=data_inicio, end=data_fim)

        # 2. DataFrames reais por métrica
        dados_real = {
            "Reuniões Marcadas": df_rmarcadas_filtrado,
            "Reuniões Realizadas": df_rrealizadas_filtrado,
            "Contratos Assinados": df_cassinados_filtrado
        }

        # 3. gráfico
        fig = go.Figure()

        for i, (nome_metrica, df) in enumerate(dados_real.items()):
            # Conta diários
            df_dia = (
                df.groupby("DATA")["CONSULTOR"]
                .count()
                .reindex(dias.date, fill_value=0)
                .rename("REALIZADO")
                .reset_index()
                .rename(columns={"index": "DATA"})
            )

            # Linha Realizado
            fig.add_trace(go.Scatter(
                x=df_dia["DATA"],
                y=df_dia["REALIZADO"].cumsum(),
                mode="lines+markers+text",
                name=f"{nome_metrica}",
                text=df_dia["REALIZADO"].cumsum(),
                textposition="top center",
                fill="tozeroy",
                line=dict(color="#1c64f2"),
                visible=(i == 0)
            ))

            # ===== NOVA LINHA DE META ACUMULADA =====
            meta_mensal = metas_acumuladas[nome_metrica]
            meta_diaria = meta_mensal / 30
            df_dia["META"] = [meta_diaria * (j + 1) for j in range(len(df_dia))]

            fig.add_trace(go.Scatter(
                x=df_dia["DATA"],
                y=df_dia["META"],
                mode="lines+markers+text",
                name=f"{nome_metrica} - Meta",
                text=df_dia["META"].astype(int),
                textposition="top center",
                line=dict(color="green", dash="dot"),
                visible=(i == 0)
            ))


        # 4. Botões interativos por métrica
        buttons = []
        for i, nome_metrica in enumerate(dados_real.keys()):
            vis = [False] * (len(dados_real) * 2)
            vis[i*2] = True       # Realizado
            vis[i*2 + 1] = True   # Meta
            buttons.append(dict(
                label=nome_metrica,
                method="update",
                args=[{"visible": vis},
                    {"title": f"{nome_metrica}"}]
            ))


        # 5. Layout final
        fig.update_layout(
            title="Reuniões Marcadas",
            xaxis_title="Data",
            yaxis_title="Quantidade acumulada",
            height=500,
            hovermode="x unified",
            xaxis=dict(range=[data_inicio, data_fim]),
            showlegend = False,
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    x=1,
                    y=0,
                    showactive=True,
                    bgcolor="#333333",         # fundo do botão (escuro)
                    bordercolor="#999999",     # borda cinza clara
                    font=dict(
                        color="white",         # texto branco
                        size=12
                    ),
                    buttons=buttons
                )
            ]
        )


        fig.update_layout(
            margin=dict(t=20, b=0, l=0, r=0),
            height=250,
            )

        st.plotly_chart(fig, use_container_width=True)

    ##############################################################################
    ##                                   rankings                               ##
    ##############################################################################

    cols_rankings = st.columns(3)

    with cols_rankings[0]:
        mapa_linha_consultor = df_linhas_validas.set_index("LINHA")["CONSULTOR"].to_dict()
        df_ligacoes_filtered["Linha"] = df_ligacoes_filtered["Usuário"].str.extract(r"\((\d{10,})\s*-")
        df_ligacoes_filtered["Consultor"] = df_ligacoes_filtered["Linha"].map(mapa_linha_consultor)

        # Agrupar e ordenar por número de ligações
        df_agrupado = df_ligacoes_filtered["Consultor"].value_counts().reset_index()
        df_agrupado.columns = ["Consultor", "Número de Ligações"]
        df_agrupado = df_agrupado.sort_values(by="Número de Ligações", ascending=False)

        # Criar gráfico de barras horizontais com Plotly
        fig = px.bar(
            df_agrupado,
            x="Número de Ligações",
            y="Consultor",
            orientation='h',
            text="Número de Ligações",
            title="Número de ligações por consultor",
        )

        fig.update_layout(yaxis=dict(autorange="reversed"),
                        margin=dict(t=21, b=10, l=0, r=0),
                        height=350
                        )
        fig.update_traces(textposition="outside")

        st.plotly_chart(fig, use_container_width=True)

    # Lista de métricas com seus respectivos DataFrames
    rankings = [
        ("Reuniões Marcadas", df_rmarcadas_filtrado),
        ("Contratos Assinados", df_cassinados_filtrado)
    ]
    
    # Loop com index para usar cols_rankings corretamente
    for idx, (titulo, df) in enumerate(rankings):
        # Conta por consultor
        df_ranking = (
            df["CONSULTOR"]
            .value_counts()
            .rename_axis("Consultor")
            .reset_index(name="Quantidade")
            .sort_values(by="Quantidade", ascending=True)
        )

        # Gráfico de barras horizontais
        fig = go.Figure(go.Bar(
            x=df_ranking["Quantidade"],
            y=df_ranking["Consultor"],
            orientation="h",
            text=df_ranking["Quantidade"],
            textposition="outside",
            marker_color="#bfa94c"
        ))

        fig.update_layout(
            title=titulo,
            xaxis_title="Quantidade",
            yaxis_title="Consultor",
            yaxis=dict(automargin=True),
            margin=dict(t=20, b=10, l=0, r=0),
            height=350
        )

        # Exibe o gráfico na coluna correspondente (1 para o primeiro, 2 para o segundo)
        with cols_rankings[idx + 1]:
            st.plotly_chart(fig, use_container_width=True)

    ##############################################################################
    ##                              ranking captação                            ##
    ##############################################################################

    df_cap = df_captação_mes.copy()
    df_metas = df_metas_individuais.copy()

    # Padronização dos nomes para merge
    df_cap["NOME"] = (
        df_cap["NOME"]
        .astype(str)
        .apply(lambda x: re.sub(r'\d+', '', x))  # remove números
        .str.replace("#", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.upper()
    )

    df_metas["CONSULTOR"] = (
        df_metas["CONSULTOR"]
        .astype(str)
        .str.replace(" ", "", regex=False)
        .str.upper()
    )

    # Tratamento dos valores de captação
    df_cap["CAPTACAO"] = (
        df_cap["CAPTACAO"]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace("- ", "-", regex=False)
        .replace("", "0")
        .astype(float)
    )

    # Merge com metas
    df = pd.merge(df_cap, df_metas, left_on="NOME", right_on="CONSULTOR", how="left")
    for col in ["BOM", "OTIMO", "EXCEPCIONAL"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .replace("", "0")
            .astype(float)
        )


    # Ordenação
    df = df.sort_values(by="CAPTACAO", ascending=False)
    # Gráfico base
    fig = go.Figure()

    # Barras de captação
    fig.add_trace(go.Bar(
        x=df["CAPTACAO"],
        y=df["NOME"],
        orientation="h",
        text=df["CAPTACAO"].apply(lambda x: f"R$ {x:,.0f}".replace(",", ".")),
        textposition="outside",
        marker_color="#bfa94c",
        name="Captação"
    ))

    # Adiciona marcadores de metas por linha
    for idx, row in df.iterrows():
        y_pos = row["NOME"]
        for tipo, cor in zip(["BOM", "OTIMO", "EXCEPCIONAL"], ["red", "green", "blue"]):
            valor_meta = row.get(tipo)
            if pd.notnull(valor_meta):
                fig.add_shape(
                    type="line",
                    x0=valor_meta,
                    x1=valor_meta,
                    y0=idx - 0.4,
                    y1=idx + 0.4,
                        line=dict(
                            color=cor,
                            width=1
                        ),
                    xref="x",
                    yref="y"
                )


    # Configuração do layout
    limite_x = df["CAPTACAO"].max() * 1.15
    limite_min = df["CAPTACAO"].min() * 2.8 if df["CAPTACAO"].min() < 0 else 0

    fig.update_layout(
        title="Ranking de Captação por Consultor (com Metas)",
        xaxis_title="Valor Captado (R$)",
        yaxis_title="Consultor",
        font=dict(size=16),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(range=[limite_min, limite_x]),
        height=800,
        margin=dict(t=40, b=20, l=20, r=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    ##############################################################################
    ##                                Tabelas                                   ##
    ##############################################################################

    cols_tabelas = st.columns(2)
    with cols_tabelas[0]:
        with st.container(border=True):
            st.markdown(f"### Origem dos leads")
            cols_1 = st.columns([1,2])

            with cols_1[0]:
                # 1. Radio para seleção da métrica
                metrica_origem = st.radio("Selecione a etapa do funil:", [
                    "Reuniões Marcadas",
                    "Reuniões Realizadas",
                    "Contratos Assinados"
                ])

                # 2. Mapeia seleção para dataframe correspondente
                df_map = {
                    "Reuniões Marcadas": df_rmarcadas_filtrado,
                    "Reuniões Realizadas": df_rrealizadas_filtrado,
                    "Contratos Assinados": df_cassinados_filtrado
                }

                df_origem = df_map[metrica_origem]

                # 3. Conta leads por origem da etapa selecionada
                tabela_origens = (
                    df_origem["ORIGEM"]
                    .value_counts()
                    .rename_axis("Origem")
                    .to_frame(name="Quantidade")
                )

                # 4. Se a métrica for anterior a Contratos Assinados, calcula conversão
                if metrica_origem != "Contratos Assinados":
                    # Base de contratos assinados por origem
                    assinados_por_origem = (
                        df_cassinados_filtrado["ORIGEM"]
                        .value_counts()
                        .rename_axis("Origem")
                        .to_frame(name="Assinados")
                    )

                    # Junta com a tabela de leads e calcula conversão
                    tabela_origens = tabela_origens.join(assinados_por_origem, how="left")
                    tabela_origens["Assinados"] = tabela_origens["Assinados"].fillna(0)
                    tabela_origens["Conversão"] = (
                        tabela_origens["Assinados"] / tabela_origens["Quantidade"]
                    ).apply(lambda x: f"{x:.1%}" if x > 0 else "0%")

                    # Remove coluna auxiliar
                    tabela_origens = tabela_origens.drop(columns=["Assinados"])

            with cols_1[1]:
                # 4. Exibe a tabela
                st.dataframe(tabela_origens, use_container_width=True)
    ##############################################################################
    ##                              Histograma                                  ##
    ##############################################################################
    with cols_tabelas[1]:
        # Garante que a coluna 'Início da ligação' está em datetime
        df_ligacoes_filtered = df_ligacoes_filtered.copy()
        df_ligacoes_filtered = df_ligacoes_filtered[df_ligacoes_filtered["Início da ligação"].notna()]

        # Converter o tempo para horas decimais
        df_ligacoes_filtered['HoraDecimal'] = (
            df_ligacoes_filtered['Início da ligação'].dt.hour +
            df_ligacoes_filtered['Início da ligação'].dt.minute / 60
        )

        # Criar o histograma
        hist_fig = px.histogram(
            df_ligacoes_filtered, 
            x='HoraDecimal', 
            nbins=14, 
            title='Distribuição de Ligações por Hora do Dia',
            labels={'HoraDecimal': 'Hora do Dia'}, 
            range_x=[7, 25],
            text_auto=True
        )

        # Estética do gráfico
        hist_fig.update_traces(marker_line_width=2, marker_line_color='black')
        hist_fig.update_traces(textposition='outside')
        hist_fig.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            bargap=0.05
        )

        # Exibir no Streamlit
        st.plotly_chart(hist_fig, use_container_width=True)

def pag_sdr(df_sdr, df_discadora):
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime
    import numpy as np

    # Função para carregar e processar os dados
    @st.cache_data
    def preparar_dados():

        # Processamento dos dados
        # Converter PATRIMÔNIO para numérico
        #df_sdr['PATRIMÔNIO'] = df_sdr['PATRIMÔNIO'].str.replace('R$ ', '').str.replace('.', '').str.replace(',', '.').astype(float)
        # Converter datas
        df_sdr['IRÁ SER FEITA EM'] = pd.to_datetime(df_sdr['IRÁ SER FEITA EM'], format='%d/%m/%Y', errors='coerce')
        df_sdr['MARCADA EM'] = pd.to_datetime(df_sdr['MARCADA EM'], format='%d/%m/%Y', errors='coerce')
        df_discadora['DATA'] = pd.to_datetime(df_discadora['DATA'], format='%d/%m/%Y', errors='coerce')
        
        return df_sdr, df_discadora

    # Carregar dados
    df_sdr, df_discadora = preparar_dados()

    ##############################################################
    ##########             1ª Linha - FILTROS          ###########
    ##############################################################

    # FILTROS
    st.subheader("🔍 Filtros")

    # Criar colunas para os filtros
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        sdr_options = st.multiselect(
            "SDR",
            options=['TODOS'] + list(df_sdr['SDR'].unique()),
            default=['TODOS']
        )

    with col2:
        consultor_options = st.multiselect(
            "CONSULTOR",
            options=['TODOS'] + list(df_sdr['CONSULTOR'].unique()),
            default=['TODOS']
        )

    with col3:
        origem_option = st.selectbox(
            "ORIGEM",
            options=['Todos'] + list(df_sdr['ORIGEM'].unique()),
            index=0
        )

    with col4:
        min_date_marcada = date.today() - timedelta(days=1)
        max_date_marcada = date.today()
        
        data_marcada = st.date_input(
            "MARCADA EM",
            value=(min_date_marcada, max_date_marcada),
            min_value= df_sdr['MARCADA EM'].min(),
            max_value=df_sdr['MARCADA EM'].max() + timedelta(days=1)
        )

    # Aplicar filtros
    df_sdr_filtered = df_sdr.copy()
    df_discadora_filtered = df_discadora.copy()

    # Filtro SDR
    if 'TODOS' not in sdr_options and sdr_options:
        # Filtra df_sdr_filtered pelas SDRs selecionadas
        df_sdr_filtered = df_sdr_filtered[df_sdr_filtered['SDR'].isin(sdr_options)]
        
        # Seleciona colunas correspondentes às SDRs em df_discadora
        colunas_validas = [sdr for sdr in sdr_options if sdr in df_discadora.columns]
        df_discadora_filtered = df_discadora_filtered[['DATA'] + colunas_validas]
    else:
        # Seleciona todas as colunas exceto 'DATA'
        colunas_validas = [col for col in df_discadora_filtered.columns if col != 'DATA']

    # Filtro CONSULTOR
    if 'TODOS' not in consultor_options and consultor_options:
        df_sdr_filtered = df_sdr_filtered[df_sdr_filtered['CONSULTOR'].isin(consultor_options)]

    # Filtro ORIGEM
    if origem_option != 'Todos':
        df_sdr_filtered = df_sdr_filtered[df_sdr_filtered['ORIGEM'] == origem_option]

    if len(data_marcada) == 2:
        start_date_marcada, end_date_marcada = data_marcada
        df_sdr_filtered = df_sdr_filtered[
            (df_sdr_filtered['MARCADA EM'] >= pd.Timestamp(start_date_marcada)) &
            (df_sdr_filtered['MARCADA EM'] <= pd.Timestamp(end_date_marcada))
        ]
        df_discadora_filtered = df_discadora_filtered[
            (df_discadora_filtered['DATA'] >= pd.Timestamp(start_date_marcada)) &
            (df_discadora_filtered['DATA'] <= pd.Timestamp(end_date_marcada))
        ]

    st.markdown("---")

    ##############################################################
    ##########                  2ª Linha               ###########
    ##############################################################

    # MÉTRICAS E GRÁFICOS
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        pessoas_faladas = df_discadora_filtered[colunas_validas].sum().sum()
        st.metric(
            label="Pessoas Faladas",
            value=pessoas_faladas
        )

    with col2: 
        # Contar leads que possuem 'r.marcada' na coluna LOG
        reunioes_marcadas = df_sdr_filtered['LOG'].str.contains('r.marcada', na=False).sum()
        st.metric(
            label="Reuniões Marcadas",
            value=reunioes_marcadas
        )

    with col3:
        # Contar leads que possuem exatamente 'r.marcada' na coluna LOG
        a_fazer = (df_sdr_filtered['LOG'] == 'r.marcada').sum()
        st.metric(
            label = "Reuniões a Fazer",
            value = a_fazer
        )

    with col4:
        # Contar leads que possuem 'r.realizada' na coluna LOG
        reunioes_realizadas = df_sdr_filtered['LOG'].str.contains('r.realizada', na=False).sum()
        st.metric(
            label = "Reuniões Realizadas",
            value = reunioes_realizadas
        )

    with col5:
        # Contar leads que possuem 'no-show' na coluna LOG
        no_show = df_sdr_filtered['LOG'].str.contains('no-show', na=False).sum()
        st.metric(
            label = "No Show",
            value = no_show
        )
 
    with col6:
        # Contar leads que possuem 'c.assinado' na coluna LOG
        contratos_assinados = df_sdr_filtered['LOG'].str.contains('c.assinado', na=False).sum()
        st.metric(
            label = "Contratos Assinados",
            value = contratos_assinados
        )

    style_metric_cards(background_color="#292D34", border_size_px=2, 
                        border_color="#292D34", border_radius_px=20, 
                        border_left_color="#bfa94c", box_shadow='True')
    ##############################################################
    ##########                3ª Linha                 ###########
    ##############################################################
    col1, col2, col3 = st.columns([2,2,2])
    
    with col1:
        st.subheader("Funil SDR's")
        st.image('Funil.png', output_format = 'PNG', use_container_width = True)

    with col2:
        # Função para renderizar cards de métricas principais
        def render_metric_card(titulo, valor, emoji="📊", cor_primaria="#4CAF50"):
            html = f"""
            <div style="background: linear-gradient(135deg, #1e1e1e, #2d2d2d); padding: 12px; border-radius: 8px; border-left: 3px solid {cor_primaria}; box-shadow: 0 2px 4px rgba(0,0,0,0.3); margin-bottom: 6px;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <div style="font-size: 11px; color: #b0b0b0; margin-bottom: 4px;">{titulo}</div>
                        <div style="font-size: 24px; color: #fff; font-weight: bold;">{valor}</div>
                    </div>
                    <div style="font-size: 24px; opacity: 0.7;">{emoji}</div>
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

        # Função para renderizar cards de conversão
        def render_conversion_card(conversao_texto, cor="#90CAF9", icone="↗"):
            html = f"""
            <div style="background: rgba(40, 40, 40, 0.8); padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; border-left: 2px solid {cor};">
                <div style="font-size: 11px; color: {cor}; text-align: center;">
                    {icone} {conversao_texto}
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

        # Função para renderizar cards de conversão total (destacada)
        def render_total_conversion_card(conversao_texto):
            html = f"""
            <div style="background: rgba(76, 175, 80, 0.15); padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; border-left: 2px solid #4CAF50;">
                <div style="font-size: 11px; color: #A5D6A7; text-align: center; font-weight: bold;">
                    🎯 {conversao_texto}
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

        # Calcular conversões
        conv1 = reunioes_marcadas / pessoas_faladas * 100 if pessoas_faladas else 0
        conv2 = reunioes_realizadas / reunioes_marcadas * 100 if reunioes_marcadas else 0
        conv3 = contratos_assinados / reunioes_realizadas * 100 if reunioes_realizadas else 0
        conv_total = contratos_assinados / pessoas_faladas * 100 if pessoas_faladas else 0

        # Render cards principais
        render_metric_card(
            titulo="Pessoas Faladas",
            valor=f"{pessoas_faladas:,}",
            emoji="🗣",
            cor_primaria="#3498db"
        )

        render_metric_card(
            titulo="Reuniões Marcadas",
            valor=f"{reunioes_marcadas:,}",
            emoji="📅",
            cor_primaria="#f39c12"
        )
        render_conversion_card(f"Conversão: {conv1:.1f}%", "#FFA726")

        render_metric_card(
            titulo="Reuniões Realizadas",
            valor=f"{reunioes_realizadas:,}",
            emoji="✅",
            cor_primaria="#27ae60"
        )
        render_conversion_card(f"Conversão: {conv2:.1f}%", "#66BB6A")

        render_metric_card(
            titulo="Contratos Assinados",
            valor=f"{contratos_assinados:,}",
            emoji="📝",
            cor_primaria="#e74c3c"
        )
        render_conversion_card(f"Conversão: {conv3:.1f}%", "#EF5350")
        render_total_conversion_card(f"Conversão Total: {conv_total:.1f}%")

    with col3:
        def render_card(texto_descricao, valor_formatado, emoji="📊"):
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #2b2e3b, #1f222d);
                    padding: 25px 20px;
                    border-radius: 16px;
                    border: 1px solid #3a3d4a;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    margin-bottom: 25px;
                    text-align: center;
                    font-family: 'Segoe UI', 'Roboto', sans-serif;
                ">
                    <div style="font-size: 16px; color: #bbbbbb; margin-bottom: 12px;">
                        {emoji} {texto_descricao}
                    </div>
                    <div style="font-size: 28px; color: #ffffff; font-weight: 600;">
                        {valor_formatado}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        render_card(
            texto_descricao="Pessoas necessárias para marcar 1 reunião",
            valor_formatado=(
                f"{int(pessoas_faladas / reunioes_marcadas)} pessoas"
                if reunioes_marcadas != 0 else "N/A"
            ),
            emoji="🗣️"
        )

        render_card(
            texto_descricao="Reuniões marcadas para realizar 1",
            valor_formatado=(
                f"{int(reunioes_marcadas / reunioes_realizadas)} reuniões"
                if reunioes_realizadas != 0 else "N/A"
            ),
            emoji="📅"
        )

        render_card(
            texto_descricao="Reuniões realizadas para fechar 1 contrato",
            valor_formatado=(
                f"{int(reunioes_realizadas / contratos_assinados)} reuniões"
                if contratos_assinados != 0 else "N/A"
            ),
            emoji="🤝"
        )


    ##############################################################
    ##########                  4ª Linha               ###########
    ##############################################################

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Marcadas para hoje')
        # Filtrar pela data de hoje e status
        hoje = datetime.today().date()
        df_hoje = df_sdr_filtered[
            (df_sdr_filtered['STATUS'] == 'MARCADA/PENDENTE') &
            (df_sdr_filtered['IRÁ SER FEITA EM'].dt.date == hoje)
        ]

        st.dataframe(df_hoje)
    
    with col2:
        # Gráfico de pizza - Temperatura do Lead
        temp_data = df_sdr_filtered['TEMPERATURA DO LEAD'].value_counts()
        
        # Filtrar apenas FRIO, MORNO, QUENTE
        valid_temps = ['FRIO', 'MORNO', 'QUENTE']
        temp_filtered = temp_data[temp_data.index.isin(valid_temps)]
        
        if len(temp_filtered) > 0:
            colors = {'FRIO': '#1f77b4', 'MORNO': '#ffbb33', 'QUENTE': '#ff4444'}
            
            # Calcular percentuais
            total = temp_filtered.sum()
            percentuais = (temp_filtered / total * 100).round(1)
            
            # Criar labels com valores absolutos e relativos
            labels = [f"{temp}<br>{temp_filtered[temp]} ({percentuais[temp]}%)" 
                    for temp in temp_filtered.index]
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=temp_filtered.index,
                values=temp_filtered.values,
                marker_colors=[colors.get(temp, '#gray') for temp in temp_filtered.index],
                textinfo='label+value+percent',
                texttemplate='%{label}<br>%{value} (%{percent})'
            )])
            
            fig_pie.update_layout(
                title='🌡️ Temperatura do Lead',
                height=400
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Não há dados de temperatura válidos para exibir")
    
        # Geração apenas dos dias úteis
        with st.expander(label= "Reuniões Marcadas por dia"):
            dias = pd.date_range(start= start_date_marcada, end=end_date_marcada, freq='B')
            meta_individual = 10
            n_sdrs = df_sdr_filtered['SDR'].nunique()
            meta_diaria_ajustada = meta_individual * n_sdrs

            # Conta quantas reuniões marcadas por dia útil
            df_dia = (
                df_sdr_filtered.groupby("MARCADA EM")["SDR"]
                .count()
                .reindex(dias.date, fill_value=0)
                .reset_index()
                .rename(columns={"index": "MARCADA EM", "SDR": "REALIZADO"})
            )

            # Converte datas para string (categorias no eixo X)
            df_dia["LABEL"] = df_dia["MARCADA EM"].apply(lambda d: d.strftime("%d/%m"))

            # Criação do gráfico
            fig = go.Figure()

            # Barras de reuniões marcadas
            fig.add_trace(go.Bar(
                x=df_dia["LABEL"],
                y=df_dia["REALIZADO"],
                name="Reuniões Marcadas",
                marker_color="#1c64f2",
                text=df_dia["REALIZADO"],
                textposition="outside",
            ))

            # Linha da meta diária ajustada
            fig.add_trace(go.Scatter(
                x=df_dia["LABEL"],
                y=[meta_diaria_ajustada] * len(df_dia),
                mode="lines",
                name="Meta Diária",
                line=dict(color="green", dash="dash")
            ))

            # Layout
            fig.update_layout(
                title="Reuniões Marcadas por Dia vs Meta",
                xaxis_title="Data (dias úteis)",
                yaxis=dict(
                    title="Reuniões marcadas",
                    range=[0, max(df_dia["REALIZADO"].max(), meta_diaria_ajustada) * 1.15]
                ),
                barmode='group',
                hovermode="x unified",
                showlegend=False,
                margin=dict(t=20, b=0, l=0, r=0),
                height=220
            )

            # Anotação da meta
            fig.add_annotation(
                xref="paper", yref="y",
                x=0.99, y=meta_diaria_ajustada,
                text=f"Meta diária: {meta_diaria_ajustada}",
                showarrow=False,
                font=dict(size=14, color="green"),
                bgcolor="white",
                bordercolor="green",
                borderwidth=1
            )

            # Exibe no Streamlit
            st.plotly_chart(fig, use_container_width=True)

    ##############################################################
    ##########                  5ª Linha               ###########
    ##############################################################
    # Função para extrair semana e ano de uma data
    def get_week_year(date):
        if pd.isna(date):
            return None
        return f"{date.year}-W{date.isocalendar()[1]:02d}"

    # Função para formatar a semana para exibição
    def format_week_display(week_str):
        if not week_str:
            return "Sem data"
        year, week = week_str.split('-W')
        # Encontrar a segunda-feira daquela semana
        monday = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w")
        sunday = monday + pd.Timedelta(days=6)
        return f"Semana {week}/{year} ({monday.strftime('%d/%m')} a {sunday.strftime('%d/%m/%Y')})"

    # Adicionar colunas de semana aos dataframes
    df_sdr['semana_ira_ser_feita'] = df_sdr['IRÁ SER FEITA EM'].apply(get_week_year)
    df_sdr['semana_marcada'] = df_sdr['MARCADA EM'].apply(get_week_year)
    df_discadora['semana'] = df_discadora['DATA'].apply(get_week_year)

    # Obter todas as semanas únicas
    semanas_sdr = set()
    semanas_sdr.update(df_sdr['semana_ira_ser_feita'].dropna().unique())
    semanas_sdr.update(df_sdr['semana_marcada'].dropna().unique())
    semanas_discadora = set(df_discadora['semana'].dropna().unique())
    todas_semanas = sorted(semanas_sdr.union(semanas_discadora))

    # Criar um dicionário para o selectbox (formato amigável -> formato técnico)
    opcoes_semana = {"Todas as semanas": "todas"}
    for semana in todas_semanas:
        opcoes_semana[format_week_display(semana)] = semana

    # Selectbox para escolher a semana
    semana_selecionada = st.selectbox(
        "Selecione a semana:",
        options=list(opcoes_semana.keys()),
        index=0
    )

    # Obter o valor técnico da semana selecionada
    semana_valor = opcoes_semana[semana_selecionada]

    # Filtrar os dataframes
    if semana_valor == "todas":
        sdr_filtrado = df_sdr.copy()
        discadora_filtrado = df_discadora.copy()
        st.info("Mostrando dados de todas as semanas")
    else:
        # Filtrar SDR - considera registros onde qualquer uma das datas está na semana selecionada
        sdr_filtrado = df_sdr[
            (df_sdr['semana_ira_ser_feita'] == semana_valor) | 
            (df_sdr['semana_marcada'] == semana_valor)
        ].copy()
        
        # Filtrar Discadora
        discadora_filtrado = df_discadora[df_discadora['semana'] == semana_valor].copy()
        
        st.success(f"Filtrado para: {semana_selecionada}")

    # Remover colunas auxiliares de semana antes de exibir
    colunas_remover_sdr = ['semana_ira_ser_feita', 'semana_marcada']
    colunas_remover_discadora = ['semana']

    sdr_filtrado = sdr_filtrado.drop(columns=[col for col in colunas_remover_sdr if col in sdr_filtrado.columns])
    discadora_filtrado = discadora_filtrado.drop(columns=[col for col in colunas_remover_discadora if col in discadora_filtrado.columns])

    def limpar_valor_monetario(valor):
        if pd.isna(valor) or valor == '':
            return 0
        if isinstance(valor, str):
            try:
                return float(valor.replace('R$', '').replace('.', '').replace(',', '.').strip())
            except ValueError:
                return 0
        return valor

    def calcular_metricas_sdr(sdr_df, discadora_df):
        # 1. Pessoas Faladas
        sdrs_discadora = [col for col in discadora_df.columns if col not in ['', 'DATA']]
        pessoas_faladas = {sdr: discadora_df[sdr].sum() for sdr in sdrs_discadora if sdr in discadora_df.columns}
        
        # 2. Reuniões Marcadas
        reunioes_marcadas = {}
        if 'LOG' in sdr_df.columns and 'SDR' in sdr_df.columns:
            marcadas = sdr_df[sdr_df['LOG'].str.contains('r.marcada', case=False, na=False)]
            reunioes_marcadas = marcadas.groupby('SDR').size().to_dict()

        # 3. Pipeline
        pipeline = {}
        if 'PATRIMÔNIO' in sdr_df.columns and 'SDR' in sdr_df.columns:
            sdr_df_copy = sdr_df.copy()
            sdr_df_copy['patrimonio_limpo'] = sdr_df_copy['PATRIMÔNIO'].apply(limpar_valor_monetario)
            pipeline = sdr_df_copy.groupby('SDR')['patrimonio_limpo'].sum().to_dict()
        
        # 4. Reuniões Realizadas
        realizadas = sdr_df[sdr_df['LOG'].str.contains('r.realizada', case=False, na=False)]
        reunioes_realizadas = realizadas.groupby('SDR').size().to_dict()
        
        # 5. Contratos Assinados
        assinados = sdr_df[sdr_df['LOG'].str.contains('c.assinado', case=False, na=False)]
        contratos_assinados = assinados.groupby('SDR').size().to_dict()

        # SDRs únicos
        todos_sdrs = set(pessoas_faladas) | set(sdr_df['SDR'].dropna().unique())

        # Montar DataFrame inicial
        df_ranking = pd.DataFrame([{
            'SDR': sdr,
            'Pessoas Faladas': pessoas_faladas.get(sdr, 0),
            'Reuniões Marcadas': reunioes_marcadas.get(sdr, 0),
            'Pipeline (R$)': pipeline.get(sdr, 0),
            'Reuniões Realizadas': reunioes_realizadas.get(sdr, 0),
            'Contratos Assinados': contratos_assinados.get(sdr, 0)
        } for sdr in todos_sdrs])

        # Normalizar colunas
        colunas = ['Pessoas Faladas', 'Reuniões Marcadas', 'Pipeline (R$)', 'Reuniões Realizadas', 'Contratos Assinados']
        scaler = MinMaxScaler()
        df_normalizado = df_ranking.copy()
        df_normalizado[colunas] = scaler.fit_transform(df_ranking[colunas])

        # Aplicar pesos
        pesos = {
            'Pessoas Faladas': 0.75,
            'Reuniões Marcadas': 0.5,
            'Pipeline (R$)': 0.25,
            'Reuniões Realizadas': 1,
            'Contratos Assinados': 1
        }
        for col in colunas:
            df_normalizado[f'{col} (Ponderado)'] = df_normalizado[col] * pesos[col]

        # Calcular eficiência
        df_normalizado['Eficiência'] = np.where(
            df_normalizado['Pessoas Faladas (Ponderado)'] == 0,
            0,
            df_normalizado['Reuniões Marcadas (Ponderado)'] / df_normalizado['Pessoas Faladas (Ponderado)']
        )
                
        # Normalizar eficiência
        df_normalizado['Eficiência Normalizada'] = MinMaxScaler().fit_transform(df_normalizado[['Eficiência']])
        df_normalizado['Eficiência Ponderada'] = df_normalizado['Eficiência Normalizada'] * 0.5

        # Calcular Score Final
        df_normalizado['Score Final'] = (
            df_normalizado[[f'{col} (Ponderado)' for col in colunas]].sum(axis=1) +
            df_normalizado['Eficiência Ponderada']
        )

        # Ordenar por Score Final
        df_normalizado = df_normalizado.sort_values(by='Score Final', ascending=False).reset_index(drop=True)

        return df_normalizado[['SDR'] + colunas + ['Eficiência', 'Score Final']]

    # Calcular métricas
    df_ranking = calcular_metricas_sdr(sdr_filtrado, discadora_filtrado)

    # Captura separada do valor absoluto de Pessoas Faladas (do raw DataFrame)
    sdrs_discadora = [col for col in discadora_filtrado.columns if col not in ['', 'DATA']]
    pessoas_faladas_abs = {sdr: discadora_filtrado[sdr].sum() for sdr in sdrs_discadora}

    # Criar DataFrame com SDR e PF absoluto
    df_pf_abs = pd.DataFrame([
        {'SDR': sdr, 'Pessoas Faladas Absoluto': pessoas_faladas_abs.get(sdr, 0)}
        for sdr in df_ranking['SDR']
    ])

    # Mesclar ao ranking (mantém a ordem)
    df_ranking = df_ranking.merge(df_pf_abs, on='SDR', how='left')

    st.dataframe(df_ranking)

    ##############################################################
    ##########                  6ª Linha               ###########
    ##############################################################

    col1, col2 = st.columns(2)

    with col1:
        # GRÁFICO 1 — Score Final por SDR
        st.subheader("Score Final por SDR")

        fig1, ax1 = plt.subplots(figsize=(10, 0.5 * len(df_ranking)))
        sdrs = df_ranking['SDR']
        scores = df_ranking['Score Final']

        # Cores: degradê do verde ao vermelho com base no rank
        n = len(scores)
        colors = plt.cm.RdYlGn(np.linspace(1, 0, n))  # verde (top) → vermelho (último)

        bars = ax1.barh(sdrs, scores, color=colors)

        # Anotar valores sobre as barras
        for i, bar in enumerate(bars):
            ax1.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                    f"{scores.iloc[i]:.2f}", va='center')

        ax1.set_xlabel("Score Final")
        ax1.invert_yaxis()  # SDRs com maior score no topo
        st.pyplot(fig1)

    with col2:
        st.subheader("Pessoas Faladas Absoluto por SDR (Meta = 280)")

        fig2, ax2 = plt.subplots(figsize=(10, 0.5 * len(df_ranking)))

        sdrs_pf = df_ranking['SDR']
        valores_pf = df_ranking['Pessoas Faladas Absoluto']
        colors_pf = ['green' if v >= 280 else 'red' for v in valores_pf]

        bars_pf = ax2.barh(sdrs_pf, valores_pf, color=colors_pf)

        for i, bar in enumerate(bars_pf):
            ax2.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
                    f"{valores_pf.iloc[i]:.0f}", va='center')

        # Linha da meta
        ax2.axvline(x=280, linestyle='--', color='black', label='Meta: 280 pessoas')
        ax2.set_xlabel("Pessoas Faladas Absoluto")
        ax2.invert_yaxis()
        ax2.legend()
        st.pyplot(fig2)



    ##############################################################
    ##########                  7ª Linha               ###########
    ##############################################################

    # Tabela de dados filtrados
    st.markdown("---")
    with st.expander(label="Bases de dados"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Sdr_df")
            st.dataframe(df_sdr_filtered, use_container_width=True)
        
        with col2:
            st.subheader("Discadora_df")
            st.dataframe(df_discadora_filtered, use_container_width=True)

    # Instruções para usar com dados reais
    st.markdown("---")

   
# ===============================

def pag_sdr_teste(df_sdr, df_discadora):
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    import numpy as np
    from plotly.subplots import make_subplots
    
    # Configuração da página
    st.set_page_config(
        page_title="SDR Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personalizado para modo escuro profissional
    st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border: 1px solid #404040;
        border-radius: 16px;
        padding: 25px;
        margin: 10px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(191, 169, 76, 0.2);
        border-color: #bfa94c;
    }
    
    .metric-title {
        font-size: 14px;
        color: #a0a0a0;
        font-weight: 500;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 8px;
    }
    
    .metric-delta {
        font-size: 14px;
        font-weight: 600;
    }
    
    .metric-delta.positive {
        color: #00d4aa;
    }
    
    .metric-delta.negative {
        color: #ff6b6b;
    }
    
    .kpi-container {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        margin: 20px 0;
    }
    
    .status-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-alta { background: #ff6b6b; color: white; }
    .status-media { background: #ffd93d; color: #333; }
    .status-baixa { background: #6bcf7f; color: white; }
    
    .sidebar-metric {
        background: #1e1e2e;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #bfa94c;
    }
    
    .highlight-text {
        color: #bfa94c;
        font-weight: 600;
    }
    
    .section-header {
        color: #ffffff;
        font-size: 24px;
        font-weight: 700;
        margin: 30px 0 20px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid #bfa94c;
    }
    
    .insight-box {
        background: linear-gradient(135deg, #2d2d44 0%, #1e1e2e 100%);
        border: 1px solid #404040;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        border-left: 4px solid #bfa94c;
    }
    
    .insight-title {
        color: #bfa94c;
        font-weight: 600;
        font-size: 16px;
        margin-bottom: 8px;
    }
    
    .insight-text {
        color: #e0e0e0;
        font-size: 14px;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

    # Função para carregar e processar os dados
    @st.cache_data
    def preparar_dados():
        # Processamento dos dados
        df_sdr['IRÁ SER FEITA EM'] = pd.to_datetime(df_sdr['IRÁ SER FEITA EM'], format='%d/%m/%Y', errors='coerce')
        df_sdr['MARCADA EM'] = pd.to_datetime(df_sdr['MARCADA EM'], format='%d/%m/%Y', errors='coerce')
        df_discadora['DATA'] = pd.to_datetime(df_discadora['DATA'], format='%d/%m/%Y', errors='coerce')
        
        # Converter patrimônio para numérico
        if 'PATRIMÔNIO' in df_sdr.columns:
            df_sdr['PATRIMÔNIO'] = pd.to_numeric(df_sdr['PATRIMÔNIO'], errors='coerce').fillna(0)
        
        return df_sdr, df_discadora

    # Função para criar métricas avançadas
    def criar_metricas_avancadas(df_sdr_filtered, df_discadora_filtered, colunas_validas):
        # Métricas base
        pessoas_faladas = pd.to_numeric(df_discadora_filtered[colunas_validas].stack(), errors='coerce').sum()
        reunioes_marcadas = df_sdr_filtered['LOG'].str.contains('r.marcada', na=False).sum()
        reunioes_realizadas = df_sdr_filtered['LOG'].str.contains('r.realizada', na=False).sum()
        no_show = df_sdr_filtered['LOG'].str.contains('no-show', na=False).sum()
        contratos_assinados = df_sdr_filtered['LOG'].str.contains('c.assinado', na=False).sum()
        
        # Métricas avançadas
        taxa_conversao_marcacao = (reunioes_marcadas / pessoas_faladas * 100) if pessoas_faladas > 0 else 0
        taxa_conversao_realizacao = (reunioes_realizadas / reunioes_marcadas * 100) if reunioes_marcadas > 0 else 0
        taxa_no_show = (no_show / reunioes_marcadas * 100) if reunioes_marcadas > 0 else 0
        taxa_fechamento = (contratos_assinados / reunioes_realizadas * 100) if reunioes_realizadas > 0 else 0
        
        # Pipeline value
        pipeline_value = df_sdr_filtered['PATRIMÔNIO'].sum() if 'PATRIMÔNIO' in df_sdr_filtered.columns else 0
        
        return {
            'pessoas_faladas': pessoas_faladas,
            'reunioes_marcadas': reunioes_marcadas,
            'reunioes_realizadas': reunioes_realizadas,
            'no_show': no_show,
            'contratos_assinados': contratos_assinados,
            'taxa_conversao_marcacao': taxa_conversao_marcacao,
            'taxa_conversao_realizacao': taxa_conversao_realizacao,
            'taxa_no_show': taxa_no_show,
            'taxa_fechamento': taxa_fechamento,
            'pipeline_value': pipeline_value
        }

    # Função para criar gráficos profissionais
    def criar_grafico_tendencia(df_sdr_filtered, df_discadora_filtered):
        # Agregar dados por data
        df_sdr_daily = df_sdr_filtered.groupby(df_sdr_filtered['MARCADA EM'].dt.date).size().reset_index()
        df_sdr_daily.columns = ['Data', 'Reuniões Marcadas']
        
        # Criar gráfico de tendência
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_sdr_daily['Data'],
            y=df_sdr_daily['Reuniões Marcadas'],
            mode='lines+markers',
            name='Reuniões Marcadas',
            line=dict(color='#bfa94c', width=3),
            marker=dict(color='#bfa94c', size=8),
            fill='tonexty',
            fillcolor='rgba(191, 169, 76, 0.1)'
        ))
        
        fig.update_layout(
            title='Tendência de Reuniões Marcadas',
            xaxis_title='Data',
            yaxis_title='Quantidade',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=350
        )
        
        return fig

    # Header principal
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #ffffff; font-size: 48px; font-weight: 800; margin-bottom: 10px;">
            📊 SDR Analytics Dashboard
        </h1>
        <p style="color: #a0a0a0; font-size: 18px; margin-bottom: 0;">
            Inteligência de Vendas & Performance Analytics
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Carregar dados
    df_sdr, df_discadora = preparar_dados()

    # Sidebar com filtros elegantes
    with st.sidebar:
        st.markdown("### 🎯 Filtros Avançados")
        
        # Filtros existentes (mantendo a mesma lógica)
        sdr_options = st.multiselect(
            "👥 SDR",
            options=['TODOS'] + list(df_sdr['SDR'].unique()),
            default=['TODOS']
        )

        consultor_options = st.multiselect(
            "🎯 CONSULTOR",
            options=['TODOS'] + list(df_sdr['CONSULTOR'].unique()),
            default=['TODOS']
        )

        origem_option = st.selectbox(
            "📍 ORIGEM",
            options=['Todos'] + list(df_sdr['ORIGEM'].unique()),
            index=0
        )

        # Filtros de data
        st.markdown("#### 📅 Período de Análise")
        
        min_date = df_sdr['IRÁ SER FEITA EM'].min()
        max_date = df_sdr['IRÁ SER FEITA EM'].max()
        
        data_range = st.date_input(
            "Data das Reuniões",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

    # Aplicar filtros (mantendo a mesma lógica do código original)
    df_sdr_filtered = df_sdr.copy()
    df_discadora_filtered = df_discadora.copy()

    # Aplicar filtros...
    if 'TODOS' not in sdr_options and sdr_options:
        df_sdr_filtered = df_sdr_filtered[df_sdr_filtered['SDR'].isin(sdr_options)]
        colunas_validas = [sdr for sdr in sdr_options if sdr in df_discadora.columns]
        df_discadora_filtered = df_discadora_filtered[['DATA'] + colunas_validas]
    else:
        colunas_validas = [col for col in df_discadora_filtered.columns if col != 'DATA']

    if 'TODOS' not in consultor_options and consultor_options:
        df_sdr_filtered = df_sdr_filtered[df_sdr_filtered['CONSULTOR'].isin(consultor_options)]

    if origem_option != 'Todos':
        df_sdr_filtered = df_sdr_filtered[df_sdr_filtered['ORIGEM'] == origem_option]

    # Obter métricas
    metricas = criar_metricas_avancadas(df_sdr_filtered, df_discadora_filtered, colunas_validas)

    # KPIs Principais
    st.markdown('<div class="section-header">🎯 Key Performance Indicators</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">👥 Pessoas Contatadas</div>
            <div class="metric-value">{metricas['pessoas_faladas']:,}</div>
            <div class="metric-delta positive">Volume Total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📅 Reuniões Marcadas</div>
            <div class="metric-value">{metricas['reunioes_marcadas']:,}</div>
            <div class="metric-delta positive">{metricas['taxa_conversao_marcacao']:.1f}% conversão</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">✅ Reuniões Realizadas</div>
            <div class="metric-value">{metricas['reunioes_realizadas']:,}</div>
            <div class="metric-delta positive">{metricas['taxa_conversao_realizacao']:.1f}% efetivação</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        delta_class = "negative" if metricas['taxa_no_show'] > 20 else "positive"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">❌ No-Show</div>
            <div class="metric-value">{metricas['no_show']:,}</div>
            <div class="metric-delta {delta_class}">{metricas['taxa_no_show']:.1f}% taxa</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">💼 Contratos Fechados</div>
            <div class="metric-value">{metricas['contratos_assinados']:,}</div>
            <div class="metric-delta positive">{metricas['taxa_fechamento']:.1f}% conversão</div>
        </div>
        """, unsafe_allow_html=True)

    # Insights e Análises
    st.markdown('<div class="section-header">🧠 Insights & Análises</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Funil de conversão melhorado
        etapas = ["Pessoas Contatadas", "Reuniões Marcadas", "Reuniões Realizadas", "Contratos Fechados"]
        quantidades = [metricas['pessoas_faladas'], metricas['reunioes_marcadas'], 
                      metricas['reunioes_realizadas'], metricas['contratos_assinados']]
        
        fig_funil = go.Figure()
        
        # Cores gradientes
        colors = ['#4a90e2', '#bfa94c', '#6bcf7f', '#ff6b6b']
        
        for i, (etapa, quantidade) in enumerate(zip(etapas, quantidades)):
            fig_funil.add_trace(go.Funnel(
                y=[etapa],
                x=[quantidade],
                textinfo="value+percent initial",
                marker=dict(color=colors[i]),
                name=etapa
            ))
        
        fig_funil.update_layout(
            title="🎯 Funil de Conversão de Vendas",
            font=dict(color='white'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=450,
            showlegend=False
        )
        
        st.plotly_chart(fig_funil, use_container_width=True)
    
    with col2:
        # Insights automáticos
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">🎯 Insight de Performance</div>
            <div class="insight-text">
                Para cada reunião marcada, você precisa contactar 
                <span class="highlight-text">{:.0f} pessoas</span> em média.
            </div>
        </div>
        """.format(metricas['pessoas_faladas'] / metricas['reunioes_marcadas'] if metricas['reunioes_marcadas'] > 0 else 0), 
        unsafe_allow_html=True)
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">📊 Eficiência de Fechamento</div>
            <div class="insight-text">
                A cada <span class="highlight-text">{:.0f} reuniões realizadas</span>, 
                você fecha aproximadamente 1 contrato.
            </div>
        </div>
        """.format(metricas['reunioes_realizadas'] / metricas['contratos_assinados'] if metricas['contratos_assinados'] > 0 else 0), 
        unsafe_allow_html=True)
        
        # Gauge de performance geral
        performance_score = (metricas['taxa_conversao_marcacao'] + metricas['taxa_conversao_realizacao'] + metricas['taxa_fechamento']) / 3
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = performance_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Performance Score"},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#bfa94c"},
                'steps': [
                    {'range': [0, 25], 'color': "#ff6b6b"},
                    {'range': [25, 50], 'color': "#ffd93d"},
                    {'range': [50, 75], 'color': "#6bcf7f"},
                    {'range': [75, 100], 'color': "#00d4aa"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig_gauge.update_layout(
            font=dict(color='white'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        
        st.plotly_chart(fig_gauge, use_container_width=True)

    # Análise de Temperatura de Leads
    st.markdown('<div class="section-header">🌡️ Análise de Temperatura de Leads</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Distribuição de temperatura
        temp_data = df_sdr_filtered['TEMPERATURA DO LEAD'].value_counts()
        valid_temps = ['FRIO', 'MORNO', 'QUENTE']
        temp_filtered = temp_data[temp_data.index.isin(valid_temps)]
        
        if len(temp_filtered) > 0:
            fig_temp = go.Figure(data=[go.Pie(
                labels=temp_filtered.index,
                values=temp_filtered.values,
                hole=0.6,
                marker=dict(
                    colors=['#4a90e2', '#ffd93d', '#ff6b6b'],
                    line=dict(color='#ffffff', width=2)
                )
            )])
            
            fig_temp.update_layout(
                title="Distribuição de Temperatura dos Leads",
                font=dict(color='white'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=350,
                showlegend=True
            )
            
            st.plotly_chart(fig_temp, use_container_width=True)
    
    with col2:
        # Análise de conversão por temperatura
        conversion_by_temp = []
        for temp in valid_temps:
            temp_leads = df_sdr_filtered[df_sdr_filtered['TEMPERATURA DO LEAD'] == temp]
            if len(temp_leads) > 0:
                conv_rate = temp_leads['LOG'].str.contains('c.assinado', na=False).sum() / len(temp_leads) * 100
                conversion_by_temp.append({'Temperatura': temp, 'Conversão': conv_rate})
        
        if conversion_by_temp:
            df_conv = pd.DataFrame(conversion_by_temp)
            
            fig_conv = px.bar(
                df_conv, 
                x='Temperatura', 
                y='Conversão',
                color='Conversão',
                color_continuous_scale='RdYlGn',
                title="Taxa de Conversão por Temperatura"
            )
            
            fig_conv.update_layout(
                font=dict(color='white'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=350
            )
            
            st.plotly_chart(fig_conv, use_container_width=True)

    # Ranking e Performance Individual
    st.markdown('<div class="section-header">🏆 Ranking de Performance</div>', unsafe_allow_html=True)
    
    # Criar ranking (mantendo a lógica original mas com apresentação melhorada)
    if len(df_sdr_filtered) > 0:
        performance_by_sdr = df_sdr_filtered.groupby('SDR').agg({
            'LOG': lambda x: x.str.contains('r.marcada', na=False).sum(),
            'PATRIMÔNIO': 'sum' if 'PATRIMÔNIO' in df_sdr_filtered.columns else lambda x: 0
        }).reset_index()
        
        performance_by_sdr.columns = ['SDR', 'Reuniões Marcadas', 'Pipeline Value']
        performance_by_sdr = performance_by_sdr.sort_values('Reuniões Marcadas', ascending=False)
        
        # Exibir ranking com estilo
        st.dataframe(
            performance_by_sdr.head(10),
            use_container_width=True,
            hide_index=True
        )

    # Agenda do Dia
    st.markdown('<div class="section-header">📅 Agenda de Hoje</div>', unsafe_allow_html=True)
    
    hoje = datetime.today().date()
    df_hoje = df_sdr_filtered[
        (df_sdr_filtered['STATUS'] == 'MARCADA/PENDENTE') &
        (df_sdr_filtered['IRÁ SER FEITA EM'].dt.date == hoje)
    ]
    
    if len(df_hoje) > 0:
        st.dataframe(
            df_hoje[['SDR', 'CONSULTOR', 'ORIGEM', 'IRÁ SER FEITA EM', 'TEMPERATURA DO LEAD']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("📅 Nenhuma reunião agendada para hoje.")

    # Dados detalhados em expander
    with st.expander("📊 Dados Detalhados"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("SDR Data")
            st.dataframe(df_sdr_filtered.head(100), use_container_width=True)
        
        with col2:
            st.subheader("Discadora Data")
            st.dataframe(df_discadora_filtered.head(100), use_container_width=True)

    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 40px 0; border-top: 1px solid #404040; margin-top: 40px;">
        <p style="color: #a0a0a0; font-size: 14px;">
            📊 Dashboard desenvolvido com Streamlit & Plotly | Última atualização: {current_time}
        </p>
    </div>
    """.format(current_time=datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)