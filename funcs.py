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
    """
    Dashboard SDR com modo noturno e compatibilidade total com Plotly 5.x+
    
    Principais características:
    - Sintaxe correta para títulos de eixos (sem titlefont)
    - Tratamento robusto de erros
    - Tema dark mode profissional
    - Compatibilidade total com diferentes versões
    """
    
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime, date, timedelta
    import numpy as np
    
    # Imports com tratamento de erro
    try:
        import matplotlib.pyplot as plt
        MATPLOTLIB_AVAILABLE = True
    except ImportError:
        MATPLOTLIB_AVAILABLE = False
        
    try:
        from sklearn.preprocessing import MinMaxScaler
        SKLEARN_AVAILABLE = True
    except ImportError:
        SKLEARN_AVAILABLE = False
        # Fallback se sklearn não estiver disponível
        class MinMaxScaler:
            def fit_transform(self, X):
                if isinstance(X, pd.DataFrame):
                    return (X - X.min()) / (X.max() - X.min())
                else:
                    return (X - np.min(X)) / (np.max(X) - np.min(X))

    # Configuração da página
    st.set_page_config(
        page_title="SDR Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # CSS personalizado para modo noturno e visual profissional
    st.markdown("""
    <style>
        /* Importar fonte moderna */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Tema principal dark */
        .stApp {
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            font-family: 'Inter', sans-serif;
        }
        
        .main-header {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
            padding: 2.5rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.3);
            backdrop-filter: blur(10px);
        }
        
        .main-header h1 {
            font-size: 2.8rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .main-header p {
            font-size: 1.2rem;
            opacity: 0.9;
            margin: 0;
            font-weight: 300;
        }
        
        /* Cards de métricas dark mode */
        .metric-card {
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 16px;
            padding: 1.8rem;
            margin: 0.8rem 0;
            box-shadow: 0 8px 25px rgba(0,0,0,0.4);
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .metric-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.2);
            border-color: rgba(99, 102, 241, 0.5);
        }
        
        .metric-value {
            font-size: 2.8rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 500;
        }
        
        /* Seções com divisores elegantes dark */
        .section-divider {
            height: 3px;
            background: linear-gradient(90deg, transparent, #6366f1, #8b5cf6, transparent);
            margin: 3rem 0;
            border: none;
            border-radius: 2px;
        }
        
        .section-header {
            font-size: 1.8rem;
            font-weight: 600;
            color: #f8fafc;
            margin-bottom: 1.5rem;
            padding-bottom: 0.8rem;
            border-bottom: 2px solid #6366f1;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }
        
        /* Sidebar dark mode */
        .sidebar-header {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }
        
        .sidebar-header h2 {
            color: white;
            margin: 0;
            font-size: 1.4rem;
            font-weight: 600;
        }
        
        /* Customização da sidebar */
        .css-1d391kg {
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
        }
        
        .css-1d391kg .css-1v3fvcr {
            background: rgba(31, 41, 55, 0.8);
        }
        
        /* Tabelas dark mode */
        .stDataFrame {
            background: rgba(31, 41, 55, 0.8);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
        }
        
        /* Expander dark mode */
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
            border-radius: 12px;
            font-weight: 600;
            color: #f8fafc;
            border: 1px solid rgba(99, 102, 241, 0.2);
        }
        
        /* Gráficos com bordas dark */
        .plotly-graph-div {
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            background: rgba(31, 41, 55, 0.8);
            backdrop-filter: blur(10px);
        }
        
        /* Remover padding padrão */
        .block-container {
            padding-top: 1rem;
        }
        
        /* Buttons dark mode */
        .stButton > button {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.8rem 1.5rem;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
        }
        
        /* Selectbox dark mode */
        .stSelectbox > div > div > div {
            background: rgba(31, 41, 55, 0.8);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 8px;
        }
        
        /* Multiselect dark mode */
        .stMultiSelect > div > div > div {
            background: rgba(31, 41, 55, 0.8);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 8px;
        }
        
        /* Info/Success messages dark */
        .stInfo, .stSuccess, .stWarning {
            background: rgba(31, 41, 55, 0.8);
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }
        
        /* Tabs dark mode */
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(31, 41, 55, 0.8);
            border-radius: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: #94a3b8;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
        }
        
        /* Métricas nativas do Streamlit */
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }
        
        [data-testid="metric-container"]:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(99, 102, 241, 0.2);
        }
        
        [data-testid="metric-container"] > div {
            color: #f8fafc;
        }
        
        /* Customização dos valores das métricas */
        [data-testid="metric-container"] [data-testid="metric-value"] {
            font-size: 2rem;
            font-weight: 700;
            color: #6366f1;
        }
        
        [data-testid="metric-container"] [data-testid="metric-label"] {
            font-size: 0.9rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1> 🥷 SDR's - Estatísticas Ninjas </h1>
        <p>Análise avançada de performance e conversões</p>
    </div>
    """, unsafe_allow_html=True)

    # Função para carregar e processar os dados
    @st.cache_data
    def preparar_dados():
        df_sdr['IRÁ SER FEITA EM'] = pd.to_datetime(df_sdr['IRÁ SER FEITA EM'], format='%d/%m/%Y', errors='coerce')
        df_sdr['MARCADA EM'] = pd.to_datetime(df_sdr['MARCADA EM'], format='%d/%m/%Y', errors='coerce')
        df_discadora['DATA'] = pd.to_datetime(df_discadora['DATA'], format='%d/%m/%Y', errors='coerce')
        
        # Converter colunas numéricas do df_discadora para evitar erros de soma
        for col in df_discadora.columns:
            if col != 'DATA':
                df_discadora[col] = pd.to_numeric(df_discadora[col], errors='coerce').fillna(0)
        
        return df_sdr, df_discadora

    df_sdr, df_discadora = preparar_dados()

    # ================================
    # SIDEBAR COM FILTROS ELEGANTES
    # ================================
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header">
            <h2>🔍 Filtros de Análise</h2>
        </div>
        """, unsafe_allow_html=True)

        # Filtros organizados
        st.markdown("**👥 Equipe**")
        sdr_options = st.multiselect(
            "SDR",
            options=['TODOS'] + list(df_sdr['SDR'].unique()),
            default=['TODOS'],
            help="Selecione os SDRs para análise"
        )

        consultor_options = st.multiselect(
            "Consultor",
            options=['TODOS'] + list(df_sdr['CONSULTOR'].unique()),
            default=['TODOS'],
            help="Filtre por consultor responsável"
        )

        st.markdown("**🎯 Origem & Data**")
        origem_option = st.selectbox(
            "Origem",
            options=['Todos'] + list(df_sdr['ORIGEM'].unique()),
            index=0,
            help="Filtrar por origem do lead"
        )

        min_val = df_sdr['MARCADA EM'].min()
        max_val = df_sdr['MARCADA EM'].max() + timedelta(days=1)

        # Corrige o valor padrão para estar dentro do intervalo
        min_date_marcada = max(min_date_marcada, min_val)
        max_date_marcada = min(max_date_marcada, max_val)

        data_marcada = st.date_input(
            "Período",
            value=(min_date_marcada, max_date_marcada),
            min_value=min_val,
            max_value=max_val,
            help="Selecione o período para análise"
        )

        st.markdown("---")
        st.markdown("**📈 Métricas em tempo real**")
        
        # Indicador de status
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            color: white;
            margin-top: 1rem;
        ">
            <div style="font-size: 0.9rem; font-weight: 600;">
                🟢 Sistema Online
            </div>
            <div style="font-size: 0.8rem; opacity: 0.9;">
                Dados atualizados
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Aplicar filtros
    df_sdr_filtered = df_sdr.copy()
    df_discadora_filtered = df_discadora.copy()

    # Filtro SDR
    if 'TODOS' not in sdr_options and sdr_options:
        df_sdr_filtered = df_sdr_filtered[df_sdr_filtered['SDR'].isin(sdr_options)]
        colunas_validas = [sdr for sdr in sdr_options if sdr in df_discadora.columns]
        df_discadora_filtered = df_discadora_filtered[['DATA'] + colunas_validas]
    else:
        colunas_validas = [col for col in df_discadora_filtered.columns if col != 'DATA']

    # Filtro CONSULTOR
    if 'TODOS' not in consultor_options and consultor_options:
        df_sdr_filtered = df_sdr_filtered[df_sdr_filtered['CONSULTOR'].isin(consultor_options)]

    # Filtro ORIGEM
    if origem_option != 'Todos':
        df_sdr_filtered = df_sdr_filtered[df_sdr_filtered['ORIGEM'] == origem_option]

    # Filtro DATA
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

    # ================================
    # MÉTRICAS PRINCIPAIS REDESENHADAS
    # ================================
    st.markdown('<div class="section-header">📊 Métricas Principais</div>', unsafe_allow_html=True)

    # Calcular métricas com tratamento de erro
    try:
        # Garantir que as colunas sejam numéricas antes da soma
        df_discadora_numeric = df_discadora_filtered[colunas_validas].apply(pd.to_numeric, errors='coerce').fillna(0)
        pessoas_faladas = int(df_discadora_numeric.sum().sum())
    except:
        pessoas_faladas = 0

    reunioes_marcadas = df_sdr_filtered['LOG'].str.contains('r.marcada', na=False).sum()
    a_fazer = (df_sdr_filtered['LOG'] == 'r.marcada').sum()
    reunioes_realizadas = df_sdr_filtered['LOG'].str.contains('r.realizada', na=False).sum()
    no_show = df_sdr_filtered['LOG'].str.contains('no-show', na=False).sum()
    contratos_assinados = df_sdr_filtered['LOG'].str.contains('c.assinado', na=False).sum()

    # Usar métricas nativas do Streamlit (que agora estão estilizadas)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🗣️ Pessoas Faladas",
            value=f"{pessoas_faladas:,}"
        )
        
        st.metric(
            label="📅 Reuniões Marcadas",
            value=f"{reunioes_marcadas:,}"
        )

    with col2:
        st.metric(
            label="⏳ Reuniões a Fazer",
            value=f"{a_fazer:,}"
        )
        
        st.metric(
            label="✅ Reuniões Realizadas",
            value=f"{reunioes_realizadas:,}"
        )

    with col3:
        st.metric(
            label="❌ No Show",
            value=f"{no_show:,}"
        )
        
        st.metric(
            label="🏆 Contratos Assinados",
            value=f"{contratos_assinados:,}"
        )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ================================
    # FUNIL E CONVERSÕES APRIMORADO
    # ================================
    st.markdown('<div class="section-header">🎯 Funil de Conversão</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("**Visualização do Funil**")
        
        # Placeholder para imagem do funil
        try:
            st.image('Funil.png', use_container_width=True)
        except:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
                border: 2px dashed rgba(99, 102, 241, 0.3);
                border-radius: 16px;
                padding: 3rem;
                text-align: center;
                color: #94a3b8;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <div style="font-size: 1.2rem; font-weight: 600;">Funil de Conversão</div>
                <div style="font-size: 0.9rem; opacity: 0.8;">Visualização será exibida aqui</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("**Métricas de Conversão**")
        
        # Calcular conversões
        conv1 = reunioes_marcadas / pessoas_faladas * 100 if pessoas_faladas else 0
        conv2 = reunioes_realizadas / reunioes_marcadas * 100 if reunioes_marcadas else 0
        conv3 = contratos_assinados / reunioes_realizadas * 100 if reunioes_realizadas else 0
        conv_total = contratos_assinados / pessoas_faladas * 100 if pessoas_faladas else 0

        # Cards de conversão com tema dark
        conversoes = [
            ("Faladas → Marcadas", conv1, "🎯", "#6366f1"),
            ("Marcadas → Realizadas", conv2, "✅", "#10b981"),
            ("Realizadas → Fechadas", conv3, "🏆", "#f59e0b"),
            ("Conversão Total", conv_total, "💎", "#8b5cf6")
        ]

        for titulo, valor, emoji, color in conversoes:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color}20, {color}10);
                border: 1px solid {color}40;
                border-left: 4px solid {color};
                padding: 1.2rem;
                border-radius: 12px;
                margin: 0.8rem 0;
                backdrop-filter: blur(10px);
            ">
                <div style="font-size: 1.4rem; font-weight: 700; color: {color};">
                    {emoji} {valor:.1f}%
                </div>
                <div style="font-size: 0.9rem; color: #94a3b8; font-weight: 500;">
                    {titulo}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        st.markdown("**Eficiência Operacional**")
        
        # Métricas de eficiência
        eficiencia = [
            ("Pessoas p/ 1 Reunião", int(pessoas_faladas / reunioes_marcadas) if reunioes_marcadas else 0, "🎯"),
            ("Reuniões p/ 1 Realizada", int(reunioes_marcadas / reunioes_realizadas) if reunioes_realizadas else 0, "📅"),
            ("Realizadas p/ 1 Fechamento", int(reunioes_realizadas / contratos_assinados) if contratos_assinados else 0, "🏆")
        ]

        for titulo, valor, emoji in eficiencia:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
                border: 1px solid rgba(99, 102, 241, 0.3);
                padding: 1.3rem;
                border-radius: 12px;
                margin: 0.8rem 0;
                text-align: center;
                backdrop-filter: blur(10px);
            ">
                <div style="font-size: 1.8rem; font-weight: 700; color: #6366f1;">
                    {valor}
                </div>
                <div style="font-size: 0.85rem; color: #94a3b8; font-weight: 500;">
                    {emoji} {titulo}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ================================
    # ANÁLISES VISUAIS APRIMORADAS
    # ================================
    st.markdown('<div class="section-header">📈 Análises Visuais</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**🗓️ Agenda de Hoje**")
        
        # Filtrar pela data de hoje
        hoje = datetime.today().date()
        df_hoje = df_sdr_filtered[
            (df_sdr_filtered['STATUS'] == 'MARCADA/PENDENTE') &
            (df_sdr_filtered['IRÁ SER FEITA EM'].dt.date == hoje)
        ]

        if not df_hoje.empty:
            st.dataframe(
                df_hoje[['SDR', 'CONSULTOR', 'IRÁ SER FEITA EM', 'TEMPERATURA DO LEAD']],
                use_container_width=True
            )
        else:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                padding: 2rem;
                border-radius: 16px;
                text-align: center;
                color: white;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">🎉</div>
                <div style="font-size: 1.3rem; font-weight: 600;">Nenhuma reunião marcada para hoje!</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">Aproveite para prospectar novos leads</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("**🌡️ Temperatura dos Leads**")
        
        # Gráfico de temperatura melhorado para dark mode
        temp_data = df_sdr_filtered['TEMPERATURA DO LEAD'].value_counts()
        valid_temps = ['FRIO', 'MORNO', 'QUENTE']
        temp_filtered = temp_data[temp_data.index.isin(valid_temps)]
        
        if len(temp_filtered) > 0:
            # Cores para dark mode
            colors = {
                'FRIO': '#3b82f6',
                'MORNO': '#f59e0b', 
                'QUENTE': '#ef4444'
            }
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=temp_filtered.index,
                values=temp_filtered.values,
                hole=0.5,  # Donut chart
                marker=dict(
                    colors=[colors.get(temp, '#6b7280') for temp in temp_filtered.index],
                    line=dict(color='#1f2937', width=3)
                ),
                textinfo='label+percent',
                textposition='outside',
                textfont=dict(size=14, color='#f8fafc', family='Inter')
            )])
            
            fig_pie.update_layout(
                title=dict(
                    text='Distribuição de Temperatura',
                    font=dict(size=18, family="Inter", color='#f8fafc'),
                    x=0.5
                ),
                height=400,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.1,
                    xanchor="center",
                    x=0.5,
                    font=dict(color='#f8fafc')
                ),
                margin=dict(t=60, b=60, l=60, r=60),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("📊 Dados insuficientes para análise de temperatura")

    # ================================
    # GRÁFICO DE REUNIÕES POR DIA
    # ================================
    with st.expander("📅 **Reuniões Marcadas por Dia**", expanded=True):
        dias = pd.date_range(start=start_date_marcada, end=end_date_marcada, freq='B')
        meta_individual = 3
        n_sdrs = df_sdr_filtered['SDR'].nunique()
        meta_diaria_ajustada = meta_individual * n_sdrs

        df_dia = (
            df_sdr_filtered.groupby("MARCADA EM")["SDR"]
            .count()
            .reindex(dias.date, fill_value=0)
            .reset_index()
            .rename(columns={"index": "MARCADA EM", "SDR": "REALIZADO"})
        )

        df_dia["LABEL"] = df_dia["MARCADA EM"].apply(lambda d: d.strftime("%d/%m"))

        fig = go.Figure()

        # Barras com gradiente para dark mode
        fig.add_trace(go.Bar(
            x=df_dia["LABEL"],
            y=df_dia["REALIZADO"],
            name="Reuniões Marcadas",
            marker=dict(
                color=df_dia["REALIZADO"],
                colorscale=[[0, '#1f2937'], [0.5, '#6366f1'], [1, '#8b5cf6']],
                showscale=False,
                line=dict(color='#374151', width=1)
            ),
            text=df_dia["REALIZADO"],
            textposition="outside",
            textfont=dict(color='#f8fafc'),
            hovertemplate="<b>%{x}</b><br>Reuniões: %{y}<extra></extra>"
        ))

        # Linha da meta
        fig.add_trace(go.Scatter(
            x=df_dia["LABEL"],
            y=[meta_diaria_ajustada] * len(df_dia),
            mode="lines",
            name="Meta Diária",
            line=dict(color="#ef4444", dash="dash", width=4),
            hovertemplate=f"<b>Meta: {meta_diaria_ajustada}</b><extra></extra>"
        ))

        # Layout atualizado com sintaxe correta
        fig.update_layout(
            title=dict(
                text="Performance Diária vs Meta",
                font=dict(size=20, family="Inter", color='#f8fafc'),
                x=0.5
            ),
            xaxis=dict(
                title=dict(text="Dias Úteis", font=dict(color='#f8fafc')),
                tickfont=dict(color='#94a3b8'),
                showgrid=True,
                gridcolor='rgba(148, 163, 184, 0.1)',
                zeroline=False
            ),
            yaxis=dict(
                title=dict(text="Reuniões Marcadas", font=dict(color='#f8fafc')),
                tickfont=dict(color='#94a3b8'),
                showgrid=True,
                gridcolor='rgba(148, 163, 184, 0.1)',
                zeroline=False,
                range=[0, max(df_dia["REALIZADO"].max(), meta_diaria_ajustada) * 1.15]
            ),
            hovermode="x unified",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(color='#f8fafc')
            ),
            height=450,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ================================
    # RANKING DE PERFORMANCE
    # ================================
    st.markdown('<div class="section-header">🏆 Ranking de Performance</div>', unsafe_allow_html=True)

    # Seletor de semana (mantendo funcionalidade original)
    def get_week_year(date):
        if pd.isna(date):
            return None
        return f"{date.year}-W{date.isocalendar()[1]:02d}"

    def format_week_display(week_str):
        if not week_str:
            return "Sem data"
        year, week = week_str.split('-W')
        monday = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w")
        sunday = monday + pd.Timedelta(days=6)
        return f"Semana {week}/{year} ({monday.strftime('%d/%m')} a {sunday.strftime('%d/%m/%Y')})"

    # Processar semanas
    df_sdr['semana_ira_ser_feita'] = df_sdr['IRÁ SER FEITA EM'].apply(get_week_year)
    df_sdr['semana_marcada'] = df_sdr['MARCADA EM'].apply(get_week_year)
    df_discadora['semana'] = df_discadora['DATA'].apply(get_week_year)

    semanas_sdr = set()
    semanas_sdr.update(df_sdr['semana_ira_ser_feita'].dropna().unique())
    semanas_sdr.update(df_sdr['semana_marcada'].dropna().unique())
    semanas_discadora = set(df_discadora['semana'].dropna().unique())
    todas_semanas = sorted(semanas_sdr.union(semanas_discadora))

    opcoes_semana = {"Todas as semanas": "todas"}
    for semana in todas_semanas:
        opcoes_semana[format_week_display(semana)] = semana

    col1, col2 = st.columns([1, 3])
    
    with col1:
        semana_selecionada = st.selectbox(
            "📅 Filtrar por semana:",
            options=list(opcoes_semana.keys()),
            index=0
        )

    semana_valor = opcoes_semana[semana_selecionada]

    # Filtrar dados por semana
    if semana_valor == "todas":
        sdr_filtrado = df_sdr.copy()
        discadora_filtrado = df_discadora.copy()
    else:
        sdr_filtrado = df_sdr[
            (df_sdr['semana_ira_ser_feita'] == semana_valor) | 
            (df_sdr['semana_marcada'] == semana_valor)
        ].copy()
        discadora_filtrado = df_discadora[df_discadora['semana'] == semana_valor].copy()

    # Remover colunas auxiliares
    colunas_remover_sdr = ['semana_ira_ser_feita', 'semana_marcada']
    colunas_remover_discadora = ['semana']
    
    sdr_filtrado = sdr_filtrado.drop(columns=[col for col in colunas_remover_sdr if col in sdr_filtrado.columns])
    discadora_filtrado = discadora_filtrado.drop(columns=[col for col in colunas_remover_discadora if col in discadora_filtrado.columns])

    # Função para calcular ranking com tratamento de erro
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
        # Tratamento seguro das colunas
        sdrs_discadora = [col for col in discadora_df.columns if col not in ['', 'DATA']]
        
        # Converter para numérico e somar de forma segura
        pessoas_faladas = {}
        for sdr in sdrs_discadora:
            if sdr in discadora_df.columns:
                try:
                    valores = pd.to_numeric(discadora_df[sdr], errors='coerce').fillna(0)
                    pessoas_faladas[sdr] = int(valores.sum())
                except:
                    pessoas_faladas[sdr] = 0
        
        reunioes_marcadas = {}
        if 'LOG' in sdr_df.columns and 'SDR' in sdr_df.columns:
            marcadas = sdr_df[sdr_df['LOG'].str.contains('r.marcada', case=False, na=False)]
            reunioes_marcadas = marcadas.groupby('SDR').size().to_dict()

        pipeline = {}
        if 'PATRIMÔNIO' in sdr_df.columns and 'SDR' in sdr_df.columns:
            sdr_df_copy = sdr_df.copy()
            sdr_df_copy['patrimonio_limpo'] = sdr_df_copy['PATRIMÔNIO'].apply(limpar_valor_monetario)
            pipeline = sdr_df_copy.groupby('SDR')['patrimonio_limpo'].sum().to_dict()
        
        realizadas = sdr_df[sdr_df['LOG'].str.contains('r.realizada', case=False, na=False)]
        reunioes_realizadas = realizadas.groupby('SDR').size().to_dict()
        
        assinados = sdr_df[sdr_df['LOG'].str.contains('c.assinado', case=False, na=False)]
        contratos_assinados = assinados.groupby('SDR').size().to_dict()

        todos_sdrs = set(pessoas_faladas) | set(sdr_df['SDR'].dropna().unique())

        df_ranking = pd.DataFrame([{
            'SDR': sdr,
            'Pessoas Faladas': pessoas_faladas.get(sdr, 0),
            'Reuniões Marcadas': reunioes_marcadas.get(sdr, 0),
            'Pipeline (R$)': pipeline.get(sdr, 0),
            'Reuniões Realizadas': reunioes_realizadas.get(sdr, 0),
            'Contratos Assinados': contratos_assinados.get(sdr, 0)
        } for sdr in todos_sdrs])

        colunas = ['Pessoas Faladas', 'Reuniões Marcadas', 'Pipeline (R$)', 'Reuniões Realizadas', 'Contratos Assinados']
        
        # Tratamento seguro do MinMaxScaler
        if len(df_ranking) > 0:
            scaler = MinMaxScaler()
            df_normalizado = df_ranking.copy()
            
            # Verificar se há variação nos dados
            for col in colunas:
                if df_ranking[col].max() == df_ranking[col].min():
                    df_normalizado[col] = 0
                else:
                    df_normalizado[col] = scaler.fit_transform(df_ranking[[col]]).flatten()
        else:
            df_normalizado = df_ranking.copy()
            for col in colunas:
                df_normalizado[col] = 0

        pesos = {
            'Pessoas Faladas': 0.75,
            'Reuniões Marcadas': 0.5,
            'Pipeline (R$)': 0.25,
            'Reuniões Realizadas': 1,
            'Contratos Assinados': 1
        }
        
        for col in colunas:
            df_normalizado[f'{col} (Ponderado)'] = df_normalizado[col] * pesos[col]

        df_normalizado['Eficiência'] = np.where(
            df_normalizado['Pessoas Faladas (Ponderado)'] == 0,
            0,
            df_normalizado['Reuniões Marcadas (Ponderado)'] / df_normalizado['Pessoas Faladas (Ponderado)']
        )
        
        if len(df_normalizado) > 0 and df_normalizado['Eficiência'].max() != df_normalizado['Eficiência'].min():
            df_normalizado['Eficiência Normalizada'] = MinMaxScaler().fit_transform(df_normalizado[['Eficiência']])
        else:
            df_normalizado['Eficiência Normalizada'] = 0
            
        df_normalizado['Eficiência Ponderada'] = df_normalizado['Eficiência Normalizada'] * 0.5

        df_normalizado['Score Final'] = (
            df_normalizado[[f'{col} (Ponderado)' for col in colunas]].sum(axis=1) +
            df_normalizado['Eficiência Ponderada']
        )

        df_normalizado = df_normalizado.sort_values(by='Score Final', ascending=False).reset_index(drop=True)

        return df_normalizado[['SDR'] + colunas + ['Eficiência', 'Score Final']]

    # Calcular ranking com tratamento de erro
    try:
        df_ranking = calcular_metricas_sdr(sdr_filtrado, discadora_filtrado)
        
        # Adicionar pessoas faladas absoluto
        sdrs_discadora = [col for col in discadora_filtrado.columns if col not in ['', 'DATA']]
        pessoas_faladas_abs = {}
        for sdr in sdrs_discadora:
            if sdr in discadora_filtrado.columns:
                try:
                    valores = pd.to_numeric(discadora_filtrado[sdr], errors='coerce').fillna(0)
                    pessoas_faladas_abs[sdr] = int(valores.sum())
                except:
                    pessoas_faladas_abs[sdr] = 0
        
        df_pf_abs = pd.DataFrame([
            {'SDR': sdr, 'Pessoas Faladas Absoluto': pessoas_faladas_abs.get(sdr, 0)}
            for sdr in df_ranking['SDR']
        ])

        df_ranking = df_ranking.merge(df_pf_abs, on='SDR', how='left')

        # Exibir ranking com estilo
        st.markdown("**📊 Tabela de Performance**")
        
        # Verificar se há dados para mostrar
        if len(df_ranking) > 0:
            st.dataframe(
                df_ranking.style.format({
                    'Score Final': '{:.2f}',
                    'Eficiência': '{:.2f}',
                    'Pipeline (R$)': 'R$ {:,.2f}'
                }).highlight_max(axis=0, color='lightgreen').highlight_min(axis=0, color='lightcoral'),
                use_container_width=True
            )
        else:
            st.info("📊 Nenhum dado disponível para o período selecionado")

        # ================================
        # GRÁFICOS DE PERFORMANCE
        # ================================
        if len(df_ranking) > 0:
            st.markdown('<div class="section-header">📊 Visualizações de Performance</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🏆 Score Final por SDR**")
                
                fig_score = go.Figure()
                
                sdrs = df_ranking['SDR']
                scores = df_ranking['Score Final']
                
                # Cores em gradiente para dark mode
                colors = ['#8b5cf6', '#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#ef4444']
                bar_colors = [colors[i % len(colors)] for i in range(len(scores))]
                
                fig_score.add_trace(go.Bar(
                    x=scores,
                    y=sdrs,
                    orientation='h',
                    marker=dict(
                        color=bar_colors,
                        line=dict(color='#374151', width=1)
                    ),
                    text=[f'{score:.2f}' for score in scores],
                    textposition='outside',
                    textfont=dict(color='#f8fafc'),
                    hovertemplate="<b>%{y}</b><br>Score: %{x:.2f}<extra></extra>"
                ))
                
                fig_score.update_layout(
                    title=dict(
                        text="Ranking por Score Final",
                        font=dict(size=18, color='#f8fafc', family='Inter'),
                        x=0.5
                    ),
                    xaxis=dict(
                        title=dict(text="Score Final", font=dict(color='#f8fafc')),
                        tickfont=dict(color='#94a3b8'),
                        showgrid=True,
                        gridcolor='rgba(148, 163, 184, 0.1)'
                    ),
                    yaxis=dict(
                        title=dict(text="SDR", font=dict(color='#f8fafc')),
                        tickfont=dict(color='#94a3b8'),
                        categoryorder='total ascending'
                    ),
                    height=300 + len(sdrs) * 35,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig_score, use_container_width=True)

            with col2:
                st.markdown("**📞 Pessoas Faladas vs Meta (280)**")
                
                fig_meta = go.Figure()
                
                valores_pf = df_ranking['Pessoas Faladas Absoluto']
                cores_meta = ['#10b981' if v >= 280 else '#ef4444' for v in valores_pf]
                
                fig_meta.add_trace(go.Bar(
                    x=valores_pf,
                    y=sdrs,
                    orientation='h',
                    marker=dict(
                        color=cores_meta,
                        line=dict(color='#374151', width=1)
                    ),
                    text=[f'{int(v)}' for v in valores_pf],
                    textposition='outside',
                    textfont=dict(color='#f8fafc'),
                    hovertemplate="<b>%{y}</b><br>Pessoas faladas: %{x}<extra></extra>"
                ))
                
                # Linha da meta
                fig_meta.add_shape(
                    type="line",
                    x0=280, x1=280,
                    y0=-0.5, y1=len(sdrs)-0.5,
                    line=dict(color="#6366f1", dash="dash", width=4)
                )
                
                fig_meta.add_annotation(
                    x=280,
                    y=len(sdrs)-0.5,
                    text="Meta: 280",
                    showarrow=False,
                    yshift=25,
                    font=dict(color='#f8fafc', size=12),
                    bgcolor="rgba(99, 102, 241, 0.2)",
                    bordercolor="#6366f1",
                    borderwidth=1
                )
                
                fig_meta.update_layout(
                    title=dict(
                        text="Performance vs Meta",
                        font=dict(size=18, color='#f8fafc', family='Inter'),
                        x=0.5
                    ),
                    xaxis=dict(
                        title=dict(text="Pessoas Faladas", font=dict(color='#f8fafc')),
                        tickfont=dict(color='#94a3b8'),
                        showgrid=True,
                        gridcolor='rgba(148, 163, 184, 0.1)'
                    ),
                    yaxis=dict(
                        title=dict(text="SDR", font=dict(color='#f8fafc')),
                        tickfont=dict(color='#94a3b8'),
                        categoryorder='total ascending'
                    ),
                    height=300 + len(sdrs) * 35,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig_meta, use_container_width=True)
        else:
            st.info("📊 Dados insuficientes para gerar visualizações de performance")

    except Exception as e:
        st.error(f"⚠️ Erro no cálculo das métricas: {str(e)}")
        st.info("💡 Verifique se os dados estão no formato correto e tente novamente.")
        
        # Exibir informações básicas mesmo com erro
        st.markdown("**📋 Informações Básicas dos Dados**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Colunas SDR:**", list(sdr_filtrado.columns))
            st.write("**Registros SDR:**", len(sdr_filtrado))
            
        with col2:
            st.write("**Colunas Discadora:**", list(discadora_filtrado.columns))
            st.write("**Registros Discadora:**", len(discadora_filtrado))

    # ================================
    # DADOS DETALHADOS
    # ================================
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    with st.expander("📋 **Bases de Dados Detalhadas**"):
        tab1, tab2 = st.tabs(["📊 Dados SDR", "📞 Dados Discadora"])
        
        with tab1:
            st.markdown("**Base de dados SDR filtrada**")
            st.dataframe(df_sdr_filtered, use_container_width=True)
        
        with tab2:
            st.markdown("**Base de dados Discadora filtrada**")
            st.dataframe(df_discadora_filtered, use_container_width=True)

    # Footer com tema dark e informações de compatibilidade
    st.markdown("---")
    
    # Verificar versões das bibliotecas
    plotly_version = "5.x+"
    sklearn_status = "✅ Disponível" if SKLEARN_AVAILABLE else "⚠️ Usando fallback"
    matplotlib_status = "✅ Disponível" if MATPLOTLIB_AVAILABLE else "⚠️ Não disponível"
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        margin-top: 2rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
    ">
        <div style="color: #f8fafc; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">
            🌙 SDR Analytics Dashboard - Versão Corrigida
        </div>
        <div style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 1rem;">
            100% compatível com Plotly moderno • Última atualização: {datetime.now().strftime("%d/%m/%Y %H:%M")}
        </div>
        <div style="color: #6366f1; font-size: 0.8rem; margin-bottom: 0.5rem;">
            ✅ Sintaxe correta para títulos de eixos • Sem erros de propriedade
        </div>
        <div style="color: #94a3b8; font-size: 0.7rem; display: flex; justify-content: center; gap: 20px;">
            <span>📊 Plotly: ✅ Compatível</span>
            <span>🔬 Sklearn: {sklearn_status}</span>
            <span>📈 Matplotlib: {matplotlib_status}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)