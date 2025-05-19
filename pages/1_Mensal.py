##############################################################################
##                                Bibliotecas                               ##
##############################################################################

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
import re

from funcs import calcular_taxas
from sidebar import setup_sidebar

##############################################################################
##                           Autenticação e cache                           ##
##############################################################################

st.set_page_config(page_title="Mensal", page_icon="📅", layout = 'wide')

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

    st.switch_page("main.py")

#######################################################################################
##                           Carregar dfs do session state                           ##
#######################################################################################

df_ligacoes = st.session_state.get("df_ligacoes")
df_rmarcadas = st.session_state.get("df_rmarcadas")
df_rrealizadas = st.session_state.get("df_rrealizadas")
#df_cenviados = st.session_state.get("df_cenviados")
df_cassinados = st.session_state.get("df_cassinados")
df_metas_individuais = st.session_state.get("df_metas_individuais")
#df_metas_niveis = st.session_state.get("df_metas_niveis")
df_captação_mes = st.session_state.get("df_captação")

#########################################################################################################
##                                         Início do Layout                                            ##
#########################################################################################################

##############################################################################
##                           Filtros Globais                                ##
##############################################################################

# Layout horizontal
col_filtros = st.columns([2, 1, 1, 2])  # [segmentação, período]

# Cópias filtradas dos DataFrames
df_rmarcadas_filtrado = df_rmarcadas.copy()
df_rrealizadas_filtrado = df_rrealizadas.copy()
df_cassinados_filtrado = df_cassinados.copy()
df_ligacoes_filtered =df_ligacoes.copy()

# 1. Filtro de Período com fundo cinza claro
with col_filtros[0]:
    with st.container(border = True):
        st.write('Selecione o período')
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data inicial", date.today().replace(day=1))
        with col2:
            data_fim = st.date_input("Data final", date.today())

        st.markdown("</div>", unsafe_allow_html=True)

    dias_selecionados = (data_fim - data_inicio).days + 1  # Inclui a data final

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

    mes_inicio = int(data_inicio.strftime("%m"))  # mês de data_inicio como int
    mes_fim = int(data_fim.strftime("%m"))        # mês de data_fim como int

# 1. Filtro de Segmentação

# --- Pré-processamento para df_ligacoes_filtered ---
# Extrair número da linha do campo "Usuário"
df_ligacoes_filtered["Linha"] = df_ligacoes_filtered["Usuário"].str.extract(r"\((\d{10,})\s*-")

df_linhas_validas = df_metas_individuais.copy()
df_linhas_validas["LINHA"] = df_linhas_validas["LINHA"].astype(str).str.strip()
df_linhas_validas = df_linhas_validas[df_linhas_validas["LINHA"].str.match(r"^\d+$")]

# Agora o mapa é criado só com LINHAS válidas
mapa_linha_consultor = df_linhas_validas.set_index("LINHA")["CONSULTOR"].to_dict()
mapa_linha_time = df_linhas_validas.set_index("LINHA")["TIME"].to_dict()


# Preenche o df_ligacoes_filtered com base nos mapas
df_ligacoes_filtered["Consultor"] = df_ligacoes_filtered["Linha"].map(mapa_linha_consultor)
df_ligacoes_filtered["Time"] = df_ligacoes_filtered["Linha"].map(mapa_linha_time)

with col_filtros[1]:
    segmentacao = st.radio("Segmentar por:", ["Geral", "Time", "Consultor"], horizontal=False)

    if segmentacao == "Time":
        with col_filtros[1]:
            time_selecionado = st.selectbox("Selecione o time:", ["TEAM BRAVO", "TEAM FARMER", "TEAM POWER", "SDR"])
            
            df_rmarcadas_filtrado = df_rmarcadas_filtrado[df_rmarcadas_filtrado["TIME"] == time_selecionado]
            df_rrealizadas_filtrado = df_rrealizadas_filtrado[df_rrealizadas_filtrado["TIME"] == time_selecionado]
            df_cassinados_filtrado = df_cassinados_filtrado[df_cassinados_filtrado["TIME"] == time_selecionado]
            df_ligacoes_filtered = df_ligacoes_filtered[df_ligacoes_filtered["Time"] == time_selecionado]

    elif segmentacao == "Consultor":
        with col_filtros[1]:
            consultores = df_metas_individuais["CONSULTOR"].dropna().unique()
            consultor_selecionado = st.selectbox("Selecione o consultor:", sorted(consultores))

            df_rmarcadas_filtrado = df_rmarcadas_filtrado[df_rmarcadas_filtrado["CONSULTOR"] == consultor_selecionado]
            df_rrealizadas_filtrado = df_rrealizadas_filtrado[df_rrealizadas_filtrado["CONSULTOR"] == consultor_selecionado]
            df_cassinados_filtrado = df_cassinados_filtrado[df_cassinados_filtrado["CONSULTOR"] == consultor_selecionado]
            df_ligacoes_filtered = df_ligacoes_filtered[df_ligacoes_filtered["Consultor"] == consultor_selecionado]

    # 2. Determina os consultores filtrados
    if segmentacao == "Geral":
        consultores_filtrados = df_metas_individuais["CONSULTOR"].dropna().unique()
    elif segmentacao == "Time":
        consultores_filtrados = df_metas_individuais[df_metas_individuais["TIME"] == time_selecionado]["CONSULTOR"].dropna().unique()
    elif segmentacao == "Consultor":
        consultores_filtrados = [consultor_selecionado]
    
    n_consultores = max(1, len(consultores_filtrados)-3)

with col_filtros[2]:
    st.write(f'Número de consultores selecionados: {n_consultores}')

# Define o número de ligações atendidas para o funil
ligações_atendidas = df_ligacoes_filtered[df_ligacoes_filtered['Tempo da ligação'] >= timedelta(minutes=1)].shape[0]

with col_filtros[3]:
    duration_options = ["Todos", "Zero", "Menos de 1 min", "Mais de 1 min", "Mais de 2 min"]
    selected_durations = st.multiselect("Escolha a duração mínima das chamadas (Apenas para Linha Virtual)", duration_options, help="")
    
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

st.divider()

#########################################################################################################
##                                                 Funil                                               ##
#########################################################################################################

##############################################################################
##                              Velocimetros                                ##
##############################################################################

# Valores do funil
valores = {
    "Reuniões Marcadas": len(df_rmarcadas_filtrado),
    "Reuniões Realizadas": len(df_rrealizadas_filtrado),
    "Contratos Assinados": len(df_cassinados_filtrado)
}

# Metas por dia por consultor
metas_mensais = {
    "Reuniões Marcadas": 40,
    "Reuniões Realizadas": 28,
    "Contratos Assinados": 7
}

multiplicador_mes = mes_fim - mes_inicio + 1

# Meta acumulada = dias * meta_diária * número de consultores
metas_acumuladas = {
    etapa: multiplicador_mes * valor_mensal * n_consultores
    for etapa, valor_mensal in metas_mensais.items()
}

# Layout com espaçamento: 4 colunas de gráficos + 3 colunas de espaço
cols = st.columns([1, 0.1, 1, 0.1, 1, 0.1, 1])  


with cols[0]:
    valor = df_ligacoes_filtered.shape[0]

    # Meta: dias úteis * 100 ligações por consultor * número de consultores
    meta_atual = multiplicador_mes * 22 * 100 * n_consultores 

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        number={'valueformat': ',.0f'},
        title={'text': "Ligações", 'font': {'size': 22}},
        delta={'reference': meta_atual},
        gauge={
            'axis': {'range': [0, meta_atual], 'tickwidth': 1, 'tickcolor': "gray"},
            'bar': {'color': "rgba(0,0,0,0)"},
            'steps': [
                {'range': [0, 0.5 * meta_atual], 'color': "#ff4d4d"},
                {'range': [0.5 * meta_atual, 0.8 * meta_atual], 'color': "#ffd633"},
                {'range': [0.8 * meta_atual, meta_atual], 'color': "#5cd65c"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 6},
                'thickness': 1,
                'value': valor
            }
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# Renderiza cada velocímetro
for idx, (nome, valor) in enumerate(valores.items()):
    col_index = 2 + idx * 2  # 2, 4, 6
    meta_atual = metas_acumuladas[nome]

    with cols[col_index]:
        with st.container():
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=valor,
                title={'text': nome, 'font': {'size': 22}},
                delta={'reference': meta_atual},
                gauge={
                    'axis': {'range': [0, meta_atual], 'tickwidth': 1, 'tickcolor': "gray"},
                    'bar': {'color': "rgba(0,0,0,0)"},
                    'steps': [
                        {'range': [0, 0.5 * meta_atual], 'color': "#ff4d4d"},
                        {'range': [0.5 * meta_atual, 0.8 * meta_atual], 'color': "#ffd633"},
                        {'range': [0.8 * meta_atual, meta_atual], 'color': "#5cd65c"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 6},
                        'thickness': 1,
                        'value': valor
                    }
                }
            ))

            st.plotly_chart(fig, use_container_width=True)

##############################################################################
##                                   Funil                                  ##
##############################################################################


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
    # Insere "Ligações Atendidas" no início
    etapas = list(valores.keys())
    quantidades = list(valores.values())

    # Recalcula taxas
    taxas_conversao = calcular_taxas(dict(zip(etapas, quantidades)))
    taxas_float = [float(t.replace('%', '')) for t in taxas_conversao]

    # Normalização para cores
    norm = mcolors.Normalize(vmin=-100, vmax=100)
    cmap = cm.get_cmap('Greens')

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

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
        <div style="margin-top: 9rem; background-color:#f0f0f0; border-radius:10px; 
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

    fig.update_layout(yaxis=dict(autorange="reversed"))
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
        height=400
    )

    # Exibe o gráfico na coluna correspondente (1 para o primeiro, 2 para o segundo)
    with cols_rankings[idx + 1]:
        st.plotly_chart(fig, use_container_width=True)

##############################################################################
##                                   Graf de linha                          ##
##############################################################################

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

##############################################################################
##     ranking captação     ##
##############################################################################

df_cap_simples = df_captação_mes.copy()

# Tratamento completo da coluna de valores
df_cap_simples["CAPTACAO"] = (
    df_cap_simples["CAPTACAO"]
    .astype(str)
    .str.replace("R$", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.replace("- ", "-", regex=False)  # Corrige valores negativos com espaço
    .replace("", "0")
    .astype(float)
)

df_cap_simples["NOME"] = (
    df_cap_simples["NOME"]
    .astype(str)
    .apply(lambda x: re.sub(r'\d+', '', x))  # remove números
    .str.replace("#", "", regex=False)
    .str.replace(" ", "", regex=False)
)


# Cria label formatado
df_cap_simples["LABEL"] = df_cap_simples["CAPTACAO"].apply(lambda x: f"R$ {x:,.0f}".replace(",", "."))

# Ordena
df_cap_simples = df_cap_simples.sort_values(by="CAPTACAO", ascending=False)

# Gráfico
fig = go.Figure(go.Bar(
    x=df_cap_simples["CAPTACAO"],
    y=df_cap_simples["NOME"],
    orientation="h",
    text=df_cap_simples["LABEL"],
    textposition="outside",
    marker_color="#bfa94c"
))

fig.update_layout(
    title="Ranking de Captação por Consultor mês atual",
    xaxis_title="Valor Captado (R$)",
    yaxis_title="Consultor",
    yaxis=dict(autorange="reversed"),
    height=600
)

# Exibe no Streamlit
st.plotly_chart(fig, use_container_width=True)

##############################################################################
##          Tabelas         ##
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
##         Histograma       ##
##############################################################################

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

