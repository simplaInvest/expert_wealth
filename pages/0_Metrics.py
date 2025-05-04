##############################
##       Bibliotecas        ##
##############################

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

from funcs import calcular_taxas
from sidebar import setup_sidebar

##############################
##   Autenticação e cache   ##
##############################

st.set_page_config(page_title="Metrics", page_icon="🔧", layout = 'wide')

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

#######################################
##   Carregar dfs do session state   ##
#######################################

df_ligacoes = st.session_state.get("df_ligacoes")
df_rmarcadas = st.session_state.get("df_rmarcadas")
df_rrealizadas = st.session_state.get("df_rrealizadas")
df_cenviados = st.session_state.get("df_cenviados")
df_cassinados = st.session_state.get("df_cassinados")
df_metas_individuais = st.session_state.get("df_metas_individuais")
#df_metas_niveis = st.session_state.get("df_metas_niveis")

#########################################################
##                  Início do Layout                   ##
#########################################################

##############################
##      Filtros Globais     ##
##############################

# Layout horizontal
col_filtros = st.columns([2, 1, 2])  # [segmentação, período]

# Cópias filtradas dos DataFrames
df_rmarcadas_filtrado = df_rmarcadas.copy()
df_rrealizadas_filtrado = df_rrealizadas.copy()
df_cenviados_filtrado = df_cenviados.copy()
df_cassinados_filtrado = df_cassinados.copy()

# 1. Filtro de Período com fundo cinza claro
with col_filtros[0]:
    with st.container(border = True):
        st.write('Selecione o período')
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data inicial", date.today() - timedelta(days=30))
        with col2:
            data_fim = st.date_input("Data final", date.today())

        st.markdown("</div>", unsafe_allow_html=True)

# 1. Filtro de Segmentação
with col_filtros[1]:
    segmentacao = st.radio("Segmentar por:", ["Geral", "Time", "Consultor"], horizontal=False)

if segmentacao == "Time":
    with col_filtros[2]:
        time_selecionado = st.selectbox("Selecione o time:", ["TEAM BRAVO", "TEAM ANYWHERE", "TEAM FARMER"])
        
        df_rmarcadas_filtrado = df_rmarcadas[df_rmarcadas["TIME"] == time_selecionado]
        df_rrealizadas_filtrado = df_rrealizadas[df_rrealizadas["TIME"] == time_selecionado]
        df_cenviados_filtrado = df_cenviados[df_cenviados["TIME"] == time_selecionado]
        df_cassinados_filtrado = df_cassinados[df_cassinados["TIME"] == time_selecionado]

elif segmentacao == "Consultor":
    with col_filtros[2]:
        consultores = df_metas_individuais["CONSULTOR"].dropna().unique()
        consultor_selecionado = st.selectbox("Selecione o consultor:", sorted(consultores))

        df_rmarcadas_filtrado = df_rmarcadas[df_rmarcadas["CONSULTOR"] == consultor_selecionado]
        df_rrealizadas_filtrado = df_rrealizadas[df_rrealizadas["CONSULTOR"] == consultor_selecionado]
        df_cenviados_filtrado = df_cenviados[df_cenviados["CONSULTOR"] == consultor_selecionado]
        df_cassinados_filtrado = df_cassinados[df_cassinados["CONSULTOR"] == consultor_selecionado]

st.divider()

##############################
##      Velocimetros        ##
##############################

# Meta fixa
meta = 30

# Valores do funil
valores = {
    "Reuniões Marcadas": len(df_rmarcadas_filtrado),
    "Reuniões Realizadas": len(df_rrealizadas_filtrado),
    "Contratos Enviados": len(df_cenviados_filtrado),
    "Contratos Assinados": len(df_cassinados_filtrado)
}

# Layout com espaçamento: 4 colunas de gráficos + 3 colunas de espaço
cols = st.columns([1, 0.1, 1, 0.1, 1, 0.1, 1])  # Total de 7 colunas

for idx, (nome, valor) in enumerate(valores.items()):
    col_index = idx * 2  # 0, 2, 4, 6
    with cols[col_index]:
        with st.container():
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=valor,
                title={'text': nome},
                delta = {'reference': meta},
                gauge={
                    'axis': {'range': [0, meta]},
                    'bar': {'color': "lightgray"},
                    'steps' : [
                                {'range': [0, meta/3], 'color': "red"},
                                {'range': [meta/3, 2*(meta/3)], 'color': "yellow"},
                                {'range': [2*(meta/3), meta], 'color': "green"}],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': valor
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)

##############################
##          Funil           ##
##############################


cols_funnel = st.columns([12,6,1,3,1])

with cols_funnel[0]:
    # Converte para DataFrame
    df_funnel = pd.DataFrame({
        "Etapa": list(valores.keys()),
        "Quantidade": list(valores.values())
    })

    # Cria o gráfico de funil
    fig = px.funnel(
        df_funnel,
        y="Etapa",
        x="Quantidade",
        color_discrete_sequence=["#bfa94c"]
    )

    # Aumenta tamanho da fonte
    fig.update_layout(
        font=dict(size=22),  # Aumenta a fonte geral
        xaxis_title_font=dict(size=18),
        yaxis_title_font=dict(size=20),
    )

    # Exibe no Streamlit
    st.plotly_chart(fig, use_container_width=True)

with cols_funnel[1]:
    taxas_conversao = calcular_taxas(valores)
    etapas = list(valores.keys())
    quantidades = list(valores.values())

    # Converte taxas de string para float
    taxas_float = [float(t.replace('%', '')) for t in taxas_conversao]

    # Normaliza os valores entre 0 e 1
    norm = mcolors.Normalize(vmin=-100, vmax=100)
    cmap = cm.get_cmap('Greens')

    st.markdown("### Conversão entre Etapas")
    st.markdown("---")

    for i in range(len(etapas) - 1):
        cor_rgb = cmap(norm(taxas_float[i]))[:3]
        cor_hex = mcolors.to_hex(cor_rgb)

        st.markdown(
            f"""
            <div style="font-size: 18px;">
                <strong>{etapas[i]}</strong> ➡️ <strong>{etapas[i+1]}</strong>: 
                <span style="color: {cor_hex}; font-weight: bold;">{taxas_conversao[i]}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("---")

with cols_funnel[3]:
    conv_final = (quantidades[-1] / quantidades[0]) * 100 if quantidades[0] > 0 else 0

    st.markdown(
        f"""
        <div style="margin-top: 10rem; background-color:#f0f0f0; border-radius:10px; 
                    padding:1rem; text-align:center; border: 1px solid #ccc;">
            <div style="font-size: 30px; font-weight: bold; color: #388e3c;">
                {conv_final:.2f}%
            </div>
            <div style="font-size: 14px;">
                dos leads chegaram até o final do funil
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

##############################
##    ranking e linhas      ##
##############################

cols_grafs = st.columns([6,2,13])

with cols_grafs[0]:
    # 1. Lista de consultores
    consultores = df_metas_individuais["CONSULTOR"].dropna().unique()

    # 2. Gera valores fakes
    random.seed(42)
    valores_fake = {nome: random.randint(100_000, 3_000_000) for nome in consultores}

    # 3. Cria DataFrame e seleciona Top 10
    df_ranking = pd.DataFrame(list(valores_fake.items()), columns=["Consultor", "Valor"])
    df_ranking = df_ranking.sort_values(by="Valor", ascending=False).head(10)

    # 4. Formata valores para exibir em R$
    df_ranking["Label"] = df_ranking["Valor"].apply(lambda x: f"R$ {x:,.0f}".replace(",", "."))

    # 5. Gráfico de barras horizontais
    fig = go.Figure(go.Bar(
        x=df_ranking["Valor"],
        y=df_ranking["Consultor"],
        orientation='h',
        text=df_ranking["Label"],
        textposition='outside',
        marker_color="#bfa94c"
    ))

    fig.update_layout(
        title="Top 10 Consultores por Captação (Fake Data)",
        xaxis_title="Valor Captado (R$)",
        yaxis_title="Consultor",
        yaxis=dict(autorange="reversed"),  # maior no topo
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

with cols_grafs[2]:
    # 1. Gerar dados fakes diários por consultor
    hoje = date.today() + timedelta(days=20)
    inicio_mes = hoje.replace(day=1)
    dias = pd.date_range(start=inicio_mes, end=hoje)

    consultores = df_metas_individuais["CONSULTOR"].dropna().unique()
    metricas = {
        "RM": "Reuniões Marcadas",
        "RR": "Reuniões Realizadas",
        "CE": "Contratos Enviados",
        "CA": "Contratos Assinados"
    }

    random.seed(42)
    registros = []
    for consultor in consultores:
        for dia in dias:
            for m_code, m_nome in metricas.items():
                registros.append({
                    "CONSULTOR": consultor,
                    "DATA": dia,
                    "MÉTRICA": m_code,
                    "REALIZADO": random.randint(1, 10),
                    "META": 10
                })

    df_fake_kpis = pd.DataFrame(registros)

    # 2. Aplicar filtro por segmentação
    df_segmentado = df_fake_kpis.copy()
    if segmentacao == "Time":
        consultores_filtrados = df_metas_individuais[df_metas_individuais["TIME"] == time_selecionado]["CONSULTOR"]
        df_segmentado = df_segmentado[df_segmentado["CONSULTOR"].isin(consultores_filtrados)]
    elif segmentacao == "Consultor":
        df_segmentado = df_segmentado[df_segmentado["CONSULTOR"] == consultor_selecionado]

    # 3. Criar gráfico com botões e linhas preenchidas
    fig = go.Figure()
    for i, (m_code, m_nome) in enumerate(metricas.items()):
        df_m = df_segmentado[df_segmentado["MÉTRICA"] == m_code]
        df_m = df_m.groupby("DATA").agg({"REALIZADO": "sum", "META": "sum"}).cumsum().reset_index()

        # Linha Realizado (azul com preenchimento)
        fig.add_trace(go.Scatter(
            x=df_m["DATA"],
            y=df_m["REALIZADO"],
            mode="lines+markers+text",
            name=f"{m_nome} - Realizado",
            text=df_m["REALIZADO"],
            textposition="top center",
            fill="tozeroy",
            line=dict(color="#1c64f2"),
            visible=(i == 0)
        ))

        # Linha Meta (verde)
        fig.add_trace(go.Scatter(
            x=df_m["DATA"],
            y=df_m["META"],
            mode="lines+markers+text",
            name=f"{m_nome} - Meta",
            text=df_m["META"],
            textposition="top center",
            fill="tozeroy",
            line=dict(color="#2e7d32", dash="dot"),
            visible=(i == 0)
        ))

    # 4. Botões com nomes completos
    buttons = []
    for i, (_, m_nome) in enumerate(metricas.items()):
        vis = [False] * (len(metricas) * 2)
        vis[i*2] = True      # Realizado
        vis[i*2 + 1] = True  # Meta
        buttons.append(dict(
            label=m_nome,
            method="update",
            args=[{"visible": vis},
                {"title": f"Realizado x Meta - {m_nome}"}]
        ))

    # 5. Layout final
    fig.update_layout(
        title="Realizado x Meta - Reuniões Marcadas",
        xaxis_title="Data",
        yaxis_title="Quantidade",
        height=500,
        hovermode="x unified",
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.7,
                y=1.15,
                buttons=buttons,
                showactive=True,
                bgcolor="white",
                bordercolor="#ccc"
            )
        ]
    )

    st.plotly_chart(fig, use_container_width=True)

##############################
##          Tabelas         ##
##############################

cols_tabelas = st.columns([2,4])
with cols_tabelas[0]:
    with st.container(border=True):
        st.markdown(f"### Origem dos leads")
        cols_1 = st.columns([1,2])
        with cols_1[0]:
            # 1. Radio para seleção da métrica
            metrica_origem = st.radio("Selecione a etapa do funil:", [
                "Reuniões Marcadas",
                "Reuniões Realizadas",
                "Contratos Enviados",
                "Contratos Assinados"
            ])

            # 2. Mapeia a seleção para o dataframe correspondente
            df_map = {
                "Reuniões Marcadas": df_rmarcadas_filtrado,
                "Reuniões Realizadas": df_rrealizadas_filtrado,
                "Contratos Enviados": df_cenviados_filtrado,
                "Contratos Assinados": df_cassinados_filtrado
            }

            df_origem = df_map[metrica_origem]

            # 3. Conta os leads por origem e ordena
            tabela_origens = (
            df_origem["ORIGEM"]
            .value_counts()
            .rename_axis("Origem")
            .to_frame(name="Quantidade")
            )

        with cols_1[1]:
            # 4. Exibe a tabela
            st.dataframe(tabela_origens, use_container_width=True)

