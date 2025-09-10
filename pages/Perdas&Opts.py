##############################################################################
##                                Bibliotecas                               ##
##############################################################################

from __future__ import annotations
import numpy as np
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

from funcs import carregar_dataframes, precisa_atualizar
from utils import formatar_data_base, vspace
from sidebar import setup_sidebar

##############################################################################
##                           Autenticação e cache                           ##
##############################################################################

# =========================
# ---------- TEMA ---------
# =========================
GOLD      = "#D4AF37"
GOLD_DIM  = "#b9972f"
WHITE     = "#FFFFFF"
BLACK     = "#0B0B0C"
GRAPH_BG  = "#0f1117"
GRAPH_GRID= "#2a2d37"
TEXT_DIM  = "#C9CCD6"
TEXT_SOFT = "#A3A7B3"
BORDER    = "rgba(212,175,55,0.25)"

def apply_plotly_theme(fig, *, with_legend=True):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=GRAPH_BG,
        plot_bgcolor=GRAPH_BG,
        font=dict(
            family="Inter, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, sans-serif",
            color=WHITE, size=13
        ),
        legend=dict(
            title=None, orientation="h",
            yanchor="bottom", y=1.02, xanchor="left", x=0
        ) if with_legend else dict(orientation="h", y=-0.2),
        hoverlabel=dict(bgcolor="#161922", bordercolor=GOLD, font=dict(color=WHITE)),
        margin=dict(l=16, r=16, t=40, b=16),
        xaxis=dict(gridcolor=GRAPH_GRID, zeroline=False, showspikes=True, spikethickness=1, spikecolor=GOLD, spikemode="across"),
        yaxis=dict(gridcolor=GRAPH_GRID, zeroline=False, showspikes=True, spikethickness=1, spikecolor=GOLD, spikemode="across")
    )
    return fig

# =========================
# ------ PAGE CONFIG ------
# =========================
st.set_page_config(page_title="Nova Pag", layout="wide")
st.logo(image='z_logo_light.png', size = 'large')
st.write(""); st.write(""); st.write("")

# =========================
# ---------- CSS ----------
# =========================
st.markdown(f"""
<style>
:root {{
  --gold: {GOLD};
  --gold-dim: {GOLD_DIM};
  --bg: {BLACK};
  --text: {WHITE};
  --text-dim: {TEXT_DIM};
  --text-soft: {TEXT_SOFT};
  --graph-bg: {GRAPH_BG};
  --graph-grid: {GRAPH_GRID};
  --gold-border: {BORDER};
}}
html, body, [data-testid="stAppViewContainer"] {{
  background: radial-gradient(1200px 800px at 20% -10%, rgba(212,175,55,0.06), transparent 60%),
              radial-gradient(900px 600px at 120% 10%, rgba(212,175,55,0.05), transparent 60%),
              var(--bg) !important;
}}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #0d0e12 0%, #0b0c10 100%);
  border-right: 1px solid rgba(255,255,255,0.03);
}}
[data-testid="stSidebar"] * {{ color: var(--text-dim) !important; }}

/* Títulos e textos */
h1, h2, h3, h4 {{ color: var(--text); letter-spacing: .2px; }}
.small {{ font-size: .85rem; color: #8e94a3; }}

/* Inputs e seletores */
.stSelectbox, .stMultiSelect, .stDateInput, .stRadio, .stSlider, .stTextInput, .stNumberInput {{
  padding: 6px 10px; border-radius: 12px;
  background: #10131a30; border: 1px solid rgba(255,255,255,0.07);
}}

/* Botões */
.stButton>button {{
  background: linear-gradient(180deg, #12141c 0%, #0e1118 100%);
  border: 1px solid var(--gold-border); color: var(--text);
  border-radius: 12px; padding: 0.55rem 0.9rem;
  transition: transform .08s ease, box-shadow .08s ease, border-color .2s;
}}
.stButton>button:hover {{
  transform: translateY(-1px);
  border-color: rgba(212,175,55,0.6);
  box-shadow: 0 10px 30px rgba(212,175,55,0.08);
}}

/* Métricas */
[data-testid="stMetric"] {{
  background: #0e1016;
  border: 1px solid rgba(212,175,55,0.18);
  border-radius: 14px; padding: 10px 12px;
}}
[data-testid="stMetricValue"], [data-testid="stMetricDelta"] {{ color: var(--text) !important; }}

/* DataFrames */
[data-testid="stDataFrame"] {{
  background: #0f1117; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
}}

/* Sections e badges */
.section {{
  background: linear-gradient(180deg, rgba(16,19,26,.55) 0%, rgba(11,12,16,.55) 100%);
  border: 1px solid rgba(255,255,255,.05);
  border-radius: 14px; padding: 14px 14px 8px 14px;
  margin-bottom: 10px;
}}
.section-title {{
  display:flex; align-items:center; gap:.5rem;
  font-weight: 700; font-size: 1.05rem; color: var(--text);
}}
.badge {{
  display:inline-block; padding:4px 10px; border-radius:999px;
  background:#131722; color:{TEXT_DIM}; border:1px solid rgba(255,255,255,.06);
}}

/* Tabs */
[data-baseweb="tab-list"] {{ gap: .25rem; border-bottom: 1px solid rgba(255,255,255,.07); }}
[data-baseweb="tab"] {{
  background: #0f1218; color: var(--text-soft);
  border: 1px solid rgba(255,255,255,.06); border-bottom: none;
  border-top-left-radius: 10px; border-top-right-radius: 10px;
}}
[data-baseweb="tab"][aria-selected="true"] {{
  color: var(--text);
  background: linear-gradient(180deg, #12141c 0%, #0f1218 100%);
  border-color: rgba(212,175,55,0.35);
  box-shadow: inset 0 -2px 0 0 var(--gold);
}}
</style>
""", unsafe_allow_html=True)

# Chama a sidebar
setup_sidebar()
with st.sidebar:
    if precisa_atualizar():
        carregar_dataframes()
        st.session_state["ultima_atualizacao"] = time.time()
    if st.button(label = '🔄 Recarregar Planilhas'):
        carregar_dataframes()
        st.session_state["ultima_atualizacao"] = time.time()
    if "ultima_atualizacao" in st.session_state:
        st.markdown(
            f"<span class='small'>🕒 Dados atualizados pela última vez em: "
            f"{time.strftime('%H:%M:%S', time.localtime(st.session_state['ultima_atualizacao']))}</span>",
            unsafe_allow_html=True
        )

#######################################################################################
##                           Carregar dfs do session state                           ##
#######################################################################################
if not all(k in st.session_state for k in ["df_nova_base"]):
    carregar_dataframes()
df_nova_base = st.session_state.get("df_nova_base")

#########################################################################################################
##                                         Início do Layout                                            ##
#########################################################################################################
if 'deals_master' not in st.session_state or 'stage_events' not in st.session_state:
    deals_master, stage_events = formatar_data_base(df_nova_base)
else:
    stage_events = st.session_state['stage_events']
    deals_master = st.session_state['deals_master']

# ------------------------------- Helpers -------------------------------

def _fmt_brl(x: float | int | None) -> str:
    if x is None or pd.isna(x):
        return "—"
    try:
        return (f"R$ {x:,.0f}").replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(x)

@st.cache_data(show_spinner=False)
def _coerce_dates(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_datetime(out[c], errors="coerce")
    return out

@st.cache_data(show_spinner=False)
def _find_loss_reason_col_name(df: pd.DataFrame) -> pd.Series:
    candidates = [
        "motivo_perda", "motivo", "motivo_loss", "lost_reason",
        "reason_loss", "motivo_closed_lost", "closed_lost_reason"
    ]
    found = None
    for c in candidates:
        if c in df.columns:
            found = c
            break
    return pd.Series([found])

@st.cache_data(show_spinner=False)
def _prepare(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    date_cols = [
        "criado_em", "ganhou_em", "perdeu_em", "assinado_em",
        "reuniao_realizada_em", "reuniao_marcada_em", "primeiro_contato_em",
        "movimentado_em"
    ]
    df = _coerce_dates(df, date_cols)

    if "status" not in df.columns:
        df["status"] = np.where(~df["ganhou_em"].isna(), "won",
                          np.where(~df["perdeu_em"].isna(), "lost", "open"))
    if "estagio_atual_canonical" not in df.columns and "etapa_atual" in df.columns:
        df["estagio_atual_canonical"] = df["etapa_atual"].fillna("Criado")

    if "valor" in df.columns:
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
    else:
        df["valor"] = 0.0

    for c in ("proprietario", "origem"):
        if c not in df.columns:
            df[c] = None

    today = pd.Timestamp(pd.Timestamp.today().date())
    if "idade_dias" not in df.columns:
        df["idade_dias"] = (today - df["criado_em"]).dt.days

    df["_loss_reason_col"] = _find_loss_reason_col_name(df)
    col = df["_loss_reason_col"].iloc[0] if len(df) else None
    if col is None:
        df["motivo_perda_norm"] = "(não informado)"
    else:
        df["motivo_perda_norm"] = (
            df[col].astype(str).str.strip()
            .str.replace("\\s+", " ", regex=True).str.capitalize()
        )
        df.loc[df[col].isna() | (df[col].astype(str).str.strip()==""), "motivo_perda_norm"] = "(não informado)"

    if "origem" in df.columns:
        df["origem_norm"] = (
            df["origem"].astype(str).str.lower().str.strip()
            .str.replace(r"lançamento ei.*", "lançamento ei", regex=True)
            .str.replace(r"\s+", " ", regex=True)
        )
        df.loc[df["origem"].isna() | (df["origem"].astype(str).str.strip()==""), "origem_norm"] = "(sem origem)"
    else:
        df["origem_norm"] = "(sem origem)"

    if "email" in df.columns:
        df["email_norm"] = df["email"].astype(str).str.strip().str.lower()
        df.loc[df["email"].astype(str).str.strip().eq(""), "email_norm"] = np.nan
    else:
        df["email_norm"] = np.nan

    if "telefone" in df.columns:
        df["telefone_norm"] = df["telefone"].astype(str).str.replace(r"\D", "", regex=True)
        df.loc[df["telefone_norm"].eq("") | df["telefone_norm"].isna(), "telefone_norm"] = np.nan
    else:
        df["telefone_norm"] = np.nan

    return df

# ------------------------------- Filtros (top bar) -------------------------------

def filter_controls_top(df: pd.DataFrame):
    st.markdown("<div class='section'><div class='section-title'>🎛️ Filtros — Perdas & Qualidade</div>", unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([1.1, 1.4, 1.2, 1.2, 2.1])

    with c1:
        status_default = ["lost"] if "lost" in df["status"].unique() else list(df["status"].unique())
        status = st.multiselect("Status",
            options=sorted(df["status"].dropna().unique()),
            default=status_default, placeholder="Selecione status…", key="pq_status")

    stages_all = list(pd.Series(df["estagio_atual_canonical"].dropna().unique()).sort_values())
    default_stages = stages_all
    with c2:
        stages = st.multiselect("Estágios",
            options=stages_all, default=default_stages,
            placeholder="Selecione estágios…", key="pq_stages")

    with c3:
        owners = st.multiselect("Proprietários",
            options=sorted([o for o in df["proprietario"].dropna().unique()]),
            default=None, placeholder="Selecione owners…", key="pq_owners")

    with c4:
        origens = st.multiselect("Origem",
            options=sorted([o for o in df["origem_norm"].dropna().unique()]),
            default=None, placeholder="Selecione origens…", key="pq_origens")

    vmin, vmax = float(df["valor"].min()), float(df["valor"].max())
    vmax = max(1.0, vmax)
    with c5:
        val_range = st.slider("Faixa de valor (BRL)",
            min_value=0.0, max_value=float(vmax),
            value=(0.0, float(vmax)), key="pq_val_range")

    c6, c7 = st.columns(2)
    with c6:
        if df["criado_em"].notna().any():
            dmin, dmax = df["criado_em"].min(), df["criado_em"].max()
            dt_criacao = st.date_input("Janela de criação (opcional)",
                value=(dmin.date(), dmax.date()), key="pq_dt_criacao")
        else:
            dt_criacao = None
    with c7:
        if df["perdeu_em"].notna().any():
            lmin, lmax = df["perdeu_em"].min(), df["perdeu_em"].max()
            dt_perda = st.date_input("Janela de perda (opcional)",
                value=(lmin.date(), lmax.date()), key="pq_dt_perda")
        else:
            dt_perda = None

    st.markdown("</div>", unsafe_allow_html=True)

    return dict(
        status=status, stages=stages, owners=owners, origens=origens,
        val_range=val_range, dt_criacao=dt_criacao, dt_perda=dt_perda
    )

@st.cache_data(show_spinner=False)
def _apply_filters(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    f = df.copy()
    if params.get("status"):
        f = f[f["status"].isin(params["status"])]
    if params.get("stages"):
        f = f[f["estagio_atual_canonical"].isin(params["stages"])]
    if params.get("owners"):
        f = f[f["proprietario"].isin(params["owners"])]
    if params.get("origens"):
        f = f[f["origem_norm"].isin(params["origens"])]
    lo, hi = params.get("val_range", (0.0, float(f["valor"].max() if len(f) else 1.0)))
    f = f[(f["valor"] >= lo) & (f["valor"] <= hi)]

    if params.get("dt_criacao") and isinstance(params["dt_criacao"], tuple):
        a, b = params["dt_criacao"]
        try:
            a = pd.Timestamp(a); b = pd.Timestamp(b) + pd.Timedelta(days=1)
            f = f[(f["criado_em"] >= a) & (f["criado_em"] < b)]
        except Exception:
            pass

    if params.get("dt_perda") and isinstance(params["dt_perda"], tuple) and ("perdeu_em" in f.columns):
        a, b = params["dt_perda"]
        try:
            a = pd.Timestamp(a); b = pd.Timestamp(b) + pd.Timedelta(days=1)
            f = f[(f["perdeu_em"] >= a) & (f["perdeu_em"] < b)]
        except Exception:
            pass
    return f

# ------------------------------- Seção PERDAS -------------------------------

def perdas_kpis(df: pd.DataFrame):
    st.markdown("<div class='section'><div class='section-title'>📌 KPIs de Perdas</div>", unsafe_allow_html=True)
    df_lost = df[df["status"] == "lost"] if "lost" in df["status"].unique() else df.iloc[0:0]
    c1, c2, c3, c4 = st.columns(4)
    total = int(len(df_lost))
    val = float(df_lost["valor"].sum()) if total else 0.0
    dias = (df_lost["perdeu_em"] - df_lost["criado_em"]).dt.days if {"perdeu_em","criado_em"}.issubset(df_lost.columns) else pd.Series(dtype=float)
    mediana_dias = float(np.nanmedian(dias)) if len(dias) else 0.0
    top_motivo = (df_lost["motivo_perda_norm"].value_counts().index[0]
                  if "motivo_perda_norm" in df_lost.columns and not df_lost.empty else "—")
    c1.metric("Perdas (qtde)", f"{total:,}".replace(",","."))  # sem mudança de dado
    c2.metric("Valor Perdido", _fmt_brl(val))
    c3.metric("Mediana dias até perder", f"{mediana_dias:.0f} d")
    c4.metric("Motivo mais comum", top_motivo)
    st.markdown("</div>", unsafe_allow_html=True)

def pareto_perdas(df: pd.DataFrame):
    st.markdown("<div class='section'><div class='section-title'>🧩 Pareto de motivos de perda</div>", unsafe_allow_html=True)
    df_lost = df[df["status"] == "lost"]
    if df_lost.empty:
        st.info("Sem dados de perdas nos filtros atuais.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    mode = st.radio("Métrica", ["Contagem", "Valor"], horizontal=True, key="pq_pareto_mode")

    if mode == "Contagem":
        ser = df_lost.groupby("motivo_perda_norm")["deal_key" if "deal_key" in df_lost.columns else df_lost.columns[0]].count().sort_values(ascending=False)
        df_plot = ser.reset_index(name="Contagem")
        y = "Contagem"
    else:
        ser = df_lost.groupby("motivo_perda_norm")["valor"].sum().sort_values(ascending=False)
        df_plot = ser.reset_index(name="Valor")
        y = "Valor"

    # cores: dourado (valor) x cinza (contagem)
    color = GOLD if y == "Valor" else "#9aa0a6"
    fig = px.bar(df_plot, x="motivo_perda_norm", y=y,
                 labels={"motivo_perda_norm": "Motivo de perda"},
                 color_discrete_sequence=[color])
    fig.update_traces(marker_line_width=0,
                      hovertemplate="<b>%{x}</b><br>%{y:,}<extra></extra>" if y=="Contagem"
                                    else "<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>")
    if y == "Valor":
        fig.update_yaxes(tickprefix="R$ ", separatethousands=True)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_tickangle=-25)
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

def tempo_ate_perder(df: pd.DataFrame):
    st.markdown("<div class='section'><div class='section-title'>⏱️ Tempo até perder (dias) por motivo</div>", unsafe_allow_html=True)
    df_lost = df[(df["status"] == "lost") & df["perdeu_em"].notna() & df["criado_em"].notna()].copy()
    if df_lost.empty:
        st.info("Sem dados suficientes para calcular tempo até perda.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    df_lost["dias_ate_perder"] = (df_lost["perdeu_em"] - df_lost["criado_em"]).dt.days
    fig = px.box(df_lost, x="motivo_perda_norm", y="dias_ate_perder",
                 points="outliers",
                 labels={"motivo_perda_norm":"Motivo de perda", "dias_ate_perder":"Dias"},
                 color_discrete_sequence=[GOLD])
    fig.update_traces(marker=dict(opacity=0.85))
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_tickangle=-25)
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

def matriz_origem_motivo(df: pd.DataFrame):
    st.markdown("<div class='section'><div class='section-title'>🧭 Origem × Motivo de Perda (contagem)</div>", unsafe_allow_html=True)
    df_lost = df[df["status"] == "lost"].copy()
    if df_lost.empty:
        st.info("Sem perdas para cruzar origem × motivo.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    pvt = pd.pivot_table(df_lost, index="origem_norm", columns="motivo_perda_norm",
                         values="valor", aggfunc="size", fill_value=0)
    # escala preta → dourado para chamar atenção a maiores contagens
    colorscale = [
        [0.00, "#0f1117"],
        [0.10, "#1a1f2b"],
        [0.40, "#3b3f4a"],
        [0.70, "#6f5e1f"],
        [1.00, GOLD],
    ]
    fig = px.imshow(pvt, text_auto=True, aspect="auto",
                    labels=dict(color="Contagem"),
                    color_continuous_scale=colorscale)
    fig.update_traces(texttemplate="%{z}")
    fig.update_coloraxes(colorbar_title="Contagem")
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------- Seção QUALIDADE / HIGIENE -------------------------------

def qualidade_kpis(df: pd.DataFrame):
    st.markdown("<div class='section'><div class='section-title'>🧼 Qualidade — KPIs rápidos</div>", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)

    n_quality_flag = int(df["data_quality_flag"].sum()) if "data_quality_flag" in df.columns else 0
    n_meeting_sem_data = int(((df.get("reuniao_marcada_flag", False)==True) & (df.get("reuniao_marcada_em").isna())).sum()) if "reuniao_marcada_flag" in df.columns and "reuniao_marcada_em" in df.columns else 0
    n_won_sem_data = int(((df["status"]=="won") & (df.get("ganhou_em").isna())).sum()) if "ganhou_em" in df.columns else 0
    n_lost_sem_data = int(((df["status"]=="lost") & (df.get("perdeu_em").isna())).sum()) if "perdeu_em" in df.columns else 0

    df_open = df[df["status"]=="open"] if "open" in df["status"].unique() else df
    dup_email = _duplicates(df_open, "email_norm")
    dup_phone = _duplicates(df_open, "telefone_norm")

    c1.metric("Registros com data_quality_flag", f"{n_quality_flag:,}".replace(",","."))  # só UI
    c2.metric("Reunião marcada SEM data", f"{n_meeting_sem_data:,}".replace(",","."))    # só UI
    c3.metric("Won/Lost sem data crítica", f"{n_won_sem_data + n_lost_sem_data:,}".replace(",","."))  # só UI
    c4.metric("Possíveis duplicidades (email/telefone)", f"{len(dup_email) + len(dup_phone):,}".replace(",","."))  # só UI
    st.markdown("</div>", unsafe_allow_html=True)

def _duplicates(df: pd.DataFrame, key: str) -> pd.DataFrame:
    if key not in df.columns:
        return pd.DataFrame(columns=df.columns)
    g = df[df[key].notna()].groupby(key)
    dup = g.filter(lambda x: len(x)>1).copy()
    return dup.sort_values(key)

def painel_flags(df: pd.DataFrame):
    st.markdown("<div class='section'><div class='section-title'>🚩 Flags de Qualidade e Pendências</div>", unsafe_allow_html=True)
    tabs = st.tabs(["data_quality_flag", "Reunião sem data", "Won/Lost sem data", "Duplicidades (email)", "Duplicidades (telefone)"])

    with tabs[0]:
        if "data_quality_flag" in df.columns:
            t = df[df["data_quality_flag"]==True].copy()
            _table_with_export(t, "data_quality_flag.csv")
        else:
            st.info("Coluna 'data_quality_flag' não encontrada.")

    with tabs[1]:
        if "reuniao_marcada_flag" in df.columns and "reuniao_marcada_em" in df.columns:
            t = df[(df["reuniao_marcada_flag"]==True) & (df["reuniao_marcada_em"].isna())].copy()
            _table_with_export(t, "reuniao_sem_data.csv")
        else:
            st.info("Colunas de reunião marcada não encontradas.")

    with tabs[2]:
        conds = []
        if "ganhou_em" in df.columns:
            conds.append((df["status"]=="won") & (df["ganhou_em"].isna()))
        if "perdeu_em" in df.columns:
            conds.append((df["status"]=="lost") & (df["perdeu_em"].isna()))
        if conds:
            m = conds[0]
            for c in conds[1:]:
                m = m | c
            t = df[m].copy()
            _table_with_export(t, "fechados_sem_data.csv")
        else:
            st.info("Colunas de datas de ganho/perda não encontradas.")

    with tabs[3]:
        df_open = df[df["status"]=="open"] if "open" in df["status"].unique() else df
        t = _duplicates(df_open, "email_norm")
        _table_with_export(t, "duplicidades_email.csv")

    with tabs[4]:
        df_open = df[df["status"]=="open"] if "open" in df["status"].unique() else df
        t = _duplicates(df_open, "telefone_norm")
        _table_with_export(t, "duplicidades_telefone.csv")

    st.markdown("</div>", unsafe_allow_html=True)

def _table_with_export(df: pd.DataFrame, filename: str):
    if df is None or df.empty:
        st.info("Sem registros nos filtros atuais.")
        return
    priority_cols = [c for c in ["deal_key","status","proprietario","origem_norm","valor","criado_em","perdeu_em","ganhou_em","estagio_atual_canonical"] if c in df.columns]
    cols = priority_cols + [c for c in df.columns if c not in priority_cols]
    st.dataframe(df[cols], hide_index=True, use_container_width=True)
    st.download_button("Exportar CSV", data=df[cols].to_csv(index=False).encode("utf-8"),
                       file_name=filename, mime="text/csv")

# ------------------------------- Main -------------------------------

def render_perdas_qualidade(deals_df: pd.DataFrame):
    st.title("Perdas & Qualidade — deals_master")

    df0 = _prepare(deals_df)
    params = filter_controls_top(df0)
    df = _apply_filters(df0, params)

    if df.empty:
        st.warning("Nenhuma linha com os filtros atuais.")
        st.stop()

    tab_perdas, tab_qualidade = st.tabs(["Perdas", "Qualidade (Higiene)"])

    with tab_perdas:
        perdas_kpis(df)
        st.divider()
        pareto_perdas(df)
        st.divider()
        tempo_ate_perder(df)
        st.divider()
        matriz_origem_motivo(df)

    with tab_qualidade:
        qualidade_kpis(df)
        st.divider()
        painel_flags(df)

# Entradas possíveis
if __name__ == "__main__":
    st.set_page_config(page_title="Perdas & Qualidade — deals_master", layout="wide")
    df_candidate = None
    for key in ("deals_master", "jaws_master", "df_deals", "df"):
        if key in st.session_state and isinstance(st.session_state[key], pd.DataFrame):
            df_candidate = st.session_state[key]
            break
    if df_candidate is None:
        g = globals()
        for key in ("deals_master", "jaws_master", "df_deals", "df"):
            if key in g and isinstance(g[key], pd.DataFrame):
                df_candidate = g[key]
                break
    if df_candidate is None:
        st.error("Não encontrei o DataFrame. Passe-o para render_perdas_qualidade(df) ou coloque em st.session_state['deals_master'].")
    else:
        render_perdas_qualidade(df_candidate)
