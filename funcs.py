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
import random
import re

def carregar_planilha(df_name, sheet_url: str, nome_aba: str = "Página1"):
    if df_name not in st.session_state:
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

def calcular_taxas(valores_dict):
    etapas = list(valores_dict.items())
    taxas = []
    for i in range(len(etapas)-1):
        atual = etapas[i][1]
        proximo = etapas[i+1][1]
        taxa = (proximo / atual * 100) if atual > 0 else 0
        taxas.append(f"{taxa:.2f}%")
    return taxas

def carregar_dataframes():

    planilhas_com_erro = []

    try:
        df_ligacoes = carregar_planilha("df_ligacoes", "https://docs.google.com/spreadsheets/d/17b9kaTH9TjSg2b32m0iHqxKF4XGWC9g6Cl2xl4VdivY/edit?usp=sharing", "LIGACOES")
        df_ligacoes = preparar_dataframe(df_ligacoes)
    except Exception as e:
        planilhas_com_erro.append(f"Histórico de chamadas: {e}")

    try:
        df_metas_individuais = carregar_planilha('df_metas_individuais','https://docs.google.com/spreadsheets/d/1244uV01S0_-64JI83kC7qv7ndzbL8CzZ6MvEu8c68nM/edit?usp=sharing', 'Metas_individuais')
    except Exception as e:
        planilhas_com_erro.append(f"Metas_individuais: {e}")

    try:
        df_rmarcadas = carregar_planilha('df_rmarcadas','https://docs.google.com/spreadsheets/d/1h7sQ7Q92ve5vA-MYxZF5srGYnlME8rfgkiKNNJQBbQk/edit?usp=sharing', 'R.MARCADAS')
        df_rmarcadas = adicionar_time('df_rmarcadas',df_rmarcadas, df_metas_individuais)
    except Exception as e:
        planilhas_com_erro.append(f"R.MARCADAS: {e}")
    
    try:
        df_rrealizadas = carregar_planilha('df_rrealizadas','https://docs.google.com/spreadsheets/d/1h7sQ7Q92ve5vA-MYxZF5srGYnlME8rfgkiKNNJQBbQk/edit?usp=sharing', 'R.REALIZADAS')
        df_rrealizadas = adicionar_time('df_rrealizadas',df_rrealizadas, df_metas_individuais)
    except Exception as e:
        planilhas_com_erro.append(f"R.REALIZADAS: {e}")
    
    try:
        df_cassinados = carregar_planilha('df_cassinados','https://docs.google.com/spreadsheets/d/1h7sQ7Q92ve5vA-MYxZF5srGYnlME8rfgkiKNNJQBbQk/edit?usp=sharing', 'C.ASSINADOS')
        df_cassinados = adicionar_time('df_cassinados',df_cassinados, df_metas_individuais)
    except Exception as e:
        planilhas_com_erro.append(f"C.ASSINADOS: {e}")

    try:
        df_captação = carregar_planilha('df_captação','https://docs.google.com/spreadsheets/d/1KmMdB6he5iqORaGa1QuBwaihSvR44LpUHWGGw_mfx_U/edit?usp=sharing', 'RANKING - DASH')
    except Exception as e:
        planilhas_com_erro.append(f"Captação: {e}")
    
    try:
        df_sdr = carregar_planilha('df_sdr', 'https://docs.google.com/spreadsheets/d/1Ex8pPnRyvN_A_5BBA7HgR26un1jyYs7DNYDt7NPqGus/edit?usp=sharing', 'DADOS')
    except Exception as e:
        planilhas_com_erro.append(f"Dados_SDR: {e}")

    try:
        df_discadora = carregar_planilha('df_discadora', 'https://docs.google.com/spreadsheets/d/1Ex8pPnRyvN_A_5BBA7HgR26un1jyYs7DNYDt7NPqGus/edit?usp=sharing', 'DADOS DISCADORA')
    except Exception as e:
        planilhas_com_erro.append(f"Dados_Discadora: {e}")
    
    if planilhas_com_erro:
        st.error("Erro ao carregar as seguintes planilhas:")
        for erro in planilhas_com_erro:
            st.error(erro)
    else:
        st.success("Planilhas carregadas com sucesso!")

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

    #########################################
        # def calcular_taxas(d):
        #     v = list(d.values())
        #     return [f"{(v[i+1]/v[i]*100):.1f}%" if v[i] else "0.0%" for i in range(len(v)-1)]

        # taxas_conversao = calcular_taxas(valores)
        # taxas_float = [float(t.replace('%', '')) for t in taxas_conversao]
        # norm = mcolors.Normalize(vmin=-100, vmax=100)
        # cmap = cm.get_cmap('Greens')

        # st.markdown("""
        # <div style="margin-bottom: 0px; font-size: 22px; font-weight: 600;">
        #     Conversão entre Etapas
        # </div>
        # <hr style="margin-top: 20px; margin-bottom: 10px;">
        # """, unsafe_allow_html=True)

        # for i in range(len(etapas) - 1):
        #     cor_rgb = cmap(norm(taxas_float[i]))[:3]
        #     cor_hex = mcolors.to_hex(cor_rgb)

        #     st.markdown(
        #         f"""
        #         <div style="font-size: 15px; margin-bottom: 20px;">
        #             <strong>{etapas[i]}</strong> ➡️ <strong>{etapas[i+1]}</strong>:
        #             <span style="color: {cor_hex}; font-weight: bold;">{taxas_conversao[i]}</span>
        #         </div>
        #         <hr style="margin-top: 20px; margin-bottom: 20px;">
        #         """,
        #         unsafe_allow_html=True
        #     )


        # conv_final = (quantidades[-1] / quantidades[0]) * 100 if quantidades[0] > 0 else 0
        # st.markdown(
        #     f"""
        #     <div style="margin-top: 1rem; background-color:#f0f0f0; border-radius:10px; 
        #                 padding:1rem; text-align:center; border: 1px solid #ccc;">
        #         <div style="font-size: 20px; font-weight: bold; color: #388e3c;">
        #             {conv_final:.2f}%
        #         </div>
        #         <div style="font-size: 14px;">
        #             dos leads chegaram até o final do funil
        #         </div>
        #     </div>
        #     """,
        #     unsafe_allow_html=True
        # )

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

    # Título do dashboard
    st.title("📊 Dashboard - Métricas SDR")
    st.info("""
    💡 Em desenvolvimento 🥶
    """)
    st.markdown("---")

    # Carregar dados
    df_sdr, df_discadora = preparar_dados()

    ##############################################################
    ##########             1ª Linha - FILTROS          ###########
    ##############################################################

    # FILTROS
    st.subheader("🔍 Filtros")

    # Criar colunas para os filtros
    col1, col2, col3, col4, col5 = st.columns(5)

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
        # Data mínima e máxima para o filtro
        min_date = df_sdr['IRÁ SER FEITA EM'].min()
        max_date = df_sdr['IRÁ SER FEITA EM'].max()
        
        data_ira_ser_feita = st.date_input(
            "IRÁ SER FEITA EM",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

    with col5:
        min_date_marcada = df_sdr['MARCADA EM'].min()
        max_date_marcada = df_sdr['MARCADA EM'].max()
        
        data_marcada = st.date_input(
            "MARCADA EM",
            value=(min_date_marcada, max_date_marcada),
            min_value=min_date_marcada,
            max_value=max_date_marcada
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

    # Filtro de datas
    if len(data_ira_ser_feita) == 2:
        start_date, end_date = data_ira_ser_feita
        df_sdr_filtered = df_sdr_filtered[
            (df_sdr_filtered['IRÁ SER FEITA EM'] >= pd.Timestamp(start_date)) &
            (df_sdr_filtered['IRÁ SER FEITA EM'] <= pd.Timestamp(end_date))
        ]
        df_discadora_filtered = df_discadora_filtered[
            (df_discadora_filtered['DATA'] >= pd.Timestamp(start_date)) &
            (df_discadora_filtered['DATA'] <= pd.Timestamp(end_date))
        ]

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
    col1, col2, col3, col4, col5 = st.columns(5)

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
        # Contar leads que possuem 'r.realizada' na coluna LOG
        reunioes_realizadas = df_sdr_filtered['LOG'].str.contains('r.realizada', na=False).sum()
        st.metric(
            label = "Reuniões Realizadas",
            value = reunioes_realizadas
        )

    with col4:
        # Contar leads que possuem 'no-show' na coluna LOG
        no_show = df_sdr_filtered['LOG'].str.contains('no-show', na=False).sum()
        st.metric(
            label = "No Show",
            value = no_show
        )
 
    with col5:
        # Contar leads que possuem 'c.assinado' na coluna LOG
        contratos_assinados = df_sdr_filtered['LOG'].str.contains('c.assinado', na=False).sum()
        st.metric(
            label = "Contratos Assinados",
            value = contratos_assinados
        )
    
    ##############################################################
    ##########                3ª Linha                 ###########
    ##############################################################
    
    col1, col2 = st.columns(2)

    with col1:
         # Etapas e valores coletados anteriormente
        etapas = [
            "Reuniões Marcadas",
            "Reuniões Realizadas",
            "Contratos Assinados"
        ]
        
        quantidades = [
            reunioes_marcadas,
            reunioes_realizadas,
            contratos_assinados
        ]

        # Taxas de conversão entre etapas
        taxas = []
        for i in range(len(quantidades) - 1):
            de = quantidades[i]
            para = quantidades[i + 1]
            taxa = (para / de) * 100 if de > 0 else 0
            taxas.append(f"{taxa:.1f}%")

        # Posição dos elementos (ajustável se necessário)
        posicoes_y_etapas = [0.91, 0.53, 0.18]
        posicoes_y_taxas = [0.69, 0.30]

        # Criação do DataFrame para o funil
        df_funnel = pd.DataFrame({
            "Etapa": etapas,
            "Quantidade": quantidades
        })

        # Criar gráfico do funil
        fig = px.funnel(
            df_funnel,
            y="Etapa",
            x="Quantidade",
            color_discrete_sequence=["#bfa94c"]
        )

        # Remover texto automático
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
                text=f"⬇️ {taxas[i]}",
                showarrow=False,
                font=dict(size=14, color="black")
            )

        # Layout final do gráfico
        fig.update_layout(
            title="Funil de Conversão",
            font=dict(size=18),
            margin=dict(t=20, b=0, l=0, r=0),
            height=480,
            showlegend=False,
            yaxis=dict(showticklabels=False, title=None)
        )

        # Exibir o gráfico no Streamlit
        st.plotly_chart(fig, use_container_width=True)

        # Conversão final (da 1ª para a última etapa)
        conv_final = round((quantidades[-1] / quantidades[0]) * 100, 1) if quantidades[0] != 0 else 0
        st.markdown(
            f"""
            <div style='text-align: center; font-size: 18px; font-weight: bold;'>
                Conv total: ⬇️ {conv_final:.2f}%
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.write()

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

    ##############################################################
    ##########                  5ª Linha               ###########
    ##############################################################

    col1, col2 = st.columns([1,4])

    with col1:
        st.subheader("Ranking Mensal")
        # Criar colunas de mês/ano
        df_discadora['MES_ANO'] = df_discadora['DATA'].dt.strftime('%m/%Y')
        df_sdr['MES_ANO'] = df_sdr['MARCADA EM'].dt.strftime('%m/%Y')

        # Obter meses/anos disponíveis em ambos os DataFrames
        meses_discadora = set(df_discadora['MES_ANO'].dropna())
        meses_sdr = set(df_sdr['MES_ANO'].dropna())
        meses_comuns = sorted(meses_discadora & meses_sdr, reverse=True)

        # Selectbox para o mês/ano
        mes_selecionado = st.selectbox("Selecione o mês/ano:", meses_comuns)

        # Aplicar filtro nos dois DataFrames
        df_discadora_filtrado = df_discadora[df_discadora['MES_ANO'] == mes_selecionado]
        df_sdr_filtrado = df_sdr[df_sdr['MES_ANO'] == mes_selecionado]

    # 1. Total de pessoas faladas por SDR
    try:
        # Verificar se as colunas existem antes de tentar removê-las
        colunas_para_remover = [col for col in ["DATA", "MES_ANO"] if col in df_discadora_filtrado.columns]
        df_pessoas_faladas = df_discadora_filtrado.drop(columns=colunas_para_remover).sum().reset_index()
        df_pessoas_faladas.columns = ['SDR', 'PESSOAS_FALADAS']
    except Exception as e:
        st.error(f"Erro ao calcular pessoas faladas: {e}")
        st.write("Colunas disponíveis:", df_discadora_filtrado.columns.tolist())

    # 2. Total de reuniões marcadas por SDR
    reunioes_marcadas = df_sdr_filtrado[df_sdr_filtrado['LOG'].str.contains('MARCADA', case=False, na=False)]
    df_reunioes_marcadas = reunioes_marcadas.groupby('SDR').size().reset_index(name='REUNIOES_MARCADAS')

    # 3. Pipeline por SDR (considerando reuniões com 'CONTRATO ASSINADO')
    df_sdr_filtrado['PATRIMÔNIO'] = pd.to_numeric(df_sdr_filtrado['PATRIMÔNIO'], errors='coerce').fillna(0)
    df_pipeline = df_sdr_filtrado.groupby('SDR')['PATRIMÔNIO'].sum().reset_index(name='PIPELINE')

    # 4. Unificar todos os dados
    df_ranking = df_pessoas_faladas.merge(df_reunioes_marcadas, on='SDR', how='left') \
                                    .merge(df_pipeline, on='SDR', how='left')

    # Preencher NaN com 0
    df_ranking.fillna(0, inplace=True)

    # 5. Eficiência
    df_ranking['EFICIENCIA'] = df_ranking['REUNIOES_MARCADAS'] / df_ranking['PESSOAS_FALADAS']
    df_ranking['EFICIENCIA'] = df_ranking['EFICIENCIA'].fillna(0)

    # Função de normalização
    def normalizar(coluna):
        max_val = coluna.max()
        return coluna / max_val if max_val > 0 else 0

    # Aplicar normalização
    df_ranking['NORM_PESSOAS'] = normalizar(df_ranking['PESSOAS_FALADAS'])
    df_ranking['NORM_REUNIOES'] = normalizar(df_ranking['REUNIOES_MARCADAS'])
    df_ranking['NORM_EFICIENCIA'] = normalizar(df_ranking['EFICIENCIA'])
    df_ranking['NORM_PIPELINE'] = normalizar(df_ranking['PIPELINE'])

    # Pesos (baseados na imagem)
    pesos = {
        'NORM_PESSOAS': 0.75,
        'NORM_REUNIOES': 0.5,
        'NORM_EFICIENCIA': 0.75,
        'NORM_PIPELINE': 0.25
    }

    # Cálculo da pontuação total
    df_ranking['TOTAL'] = (
        df_ranking['NORM_PESSOAS'] * pesos['NORM_PESSOAS'] +
        df_ranking['NORM_REUNIOES'] * pesos['NORM_REUNIOES'] +
        df_ranking['NORM_EFICIENCIA'] * pesos['NORM_EFICIENCIA'] +
        df_ranking['NORM_PIPELINE'] * pesos['NORM_PIPELINE']
    )

    # Organizar colunas para exibição final
    colunas_exibir = [
        'SDR', 'PESSOAS_FALADAS', 'NORM_PESSOAS',
        'REUNIOES_MARCADAS', 'NORM_REUNIOES',
        'EFICIENCIA', 'NORM_EFICIENCIA',
        'PIPELINE', 'NORM_PIPELINE',
        'TOTAL'
    ]

    df_resultado_final = df_ranking[colunas_exibir].sort_values(by='TOTAL', ascending=False)
    st.dataframe(df_resultado_final)





    # Tabela de dados filtrados
    st.markdown("---")
    st.subheader("📋 Dados Filtrados")
    st.dataframe(df_sdr_filtered, use_container_width=True)

    # Instruções para usar com dados reais
    st.markdown("---")
   
