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
# Paleta base
GOLD      = "#D4AF37"
GOLD_DIM  = "#b9972f"
WHITE     = "#FFFFFF"
BLACK     = "#0B0B0C"
GRAPH_BG  = "#0f1117"   # fundo dos gráficos
GRAPH_GRID= "#2a2d37"   # grade sutil
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

/* Títulos */
h1, h2, h3, h4 {{ color: var(--text); letter-spacing: .2px; }}

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
/* Containers visuais */
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
.small {{ font-size: .85rem; color: #8e94a3; }}
</style>
""", unsafe_allow_html=True)

# Sidebar e update
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

# -------------------------------  Helpers  -------------------------------

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
def _prepare(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    # Tipos
    date_cols = [
        "criado_em", "ganhou_em", "perdeu_em", "assinado_em",
        "reuniao_realizada_em", "reuniao_marcada_em", "primeiro_contato_em",
        "movimentado_em"
    ]
    df = _coerce_dates(df, date_cols)

    # Colunas esperadas
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

    # Âncora para dias_no_estagio_atual
    stage_date_map = {
        "Closed Won": ["ganhou_em", "assinado_em", "movimentado_em", "criado_em"],
        "Closed Lost": ["perdeu_em", "movimentado_em", "criado_em"],
        "Assinado": ["assinado_em", "reuniao_realizada_em", "reuniao_marcada_em", "primeiro_contato_em", "movimentado_em", "criado_em"],
        "Reunião Realizada": ["reuniao_realizada_em", "reuniao_marcada_em", "primeiro_contato_em", "movimentado_em", "criado_em"],
        "Reunião Marcada": ["reuniao_marcada_em", "primeiro_contato_em", "movimentado_em", "criado_em"],
        "1º Contato": ["primeiro_contato_em", "movimentado_em", "criado_em"],
        "Criado": ["movimentado_em", "criado_em"],
    }
    def pick_anchor(row) -> pd.Timestamp | pd.NaT:
        stage = row.get("estagio_atual_canonical")
        order = stage_date_map.get(stage, ["movimentado_em", "criado_em"])
        for c in order:
            val = row.get(c)
            if pd.notna(val):
                return val
        return pd.NaT

    df["_anchor_dt"] = df.apply(pick_anchor, axis=1)
    today = pd.Timestamp(pd.Timestamp.today().date())
    df["dias_no_estagio_atual"] = (today - df["_anchor_dt"]).dt.days
    df.loc[df["_anchor_dt"].isna(), "dias_no_estagio_atual"] = np.nan

    if "idade_dias" not in df.columns:
        df["idade_dias"] = (today - df["criado_em"]).dt.days

    df["ultimo_evento_dt"] = df[[c for c in date_cols if c in df.columns]].max(axis=1)
    return df

# -------------------------------  Filtros  -------------------------------

def filter_controls(df: pd.DataFrame):
    st.markdown("<div class='section'><div class='section-title'>🎛️ Filtros</div>", unsafe_allow_html=True)

    cols_filters = st.columns([1.1, 1.4, 1.2, 1.2, 2.1])
    with cols_filters[0]:
        status_default = ["open"] if "open" in df["status"].unique() else list(df["status"].unique())
        status = st.multiselect("Status",
                                options=sorted(df["status"].dropna().unique()),
                                default=status_default,
                                placeholder="Selecione status…",
                                key="flt_status")
    stages_all = list(pd.Series(df["estagio_atual_canonical"].dropna().unique()).sort_values())
    default_stages = [s for s in stages_all if s not in ("Closed Won", "Closed Lost")] or stages_all
    with cols_filters[1]:
        stages = st.multiselect("Estágios",
                                options=stages_all,
                                default=default_stages,
                                placeholder="Selecione estágios…",
                                key="flt_stages")
    with cols_filters[2]:
        owners = st.multiselect("Proprietários",
                                options=sorted([o for o in df["proprietario"].dropna().unique()]),
                                default=None,
                                placeholder="Selecione owners…",
                                key="flt_owners")
    with cols_filters[3]:
        origens = st.multiselect("Origem",
                                 options=sorted([o for o in df["origem"].dropna().unique()]),
                                 default=None,
                                 placeholder="Selecione origens…",
                                 key="flt_origens")
    vmin, vmax = float(df["valor"].min()), float(df["valor"].max())
    vmax = max(1.0, vmax)
    with cols_filters[4]:
        val_range = st.slider("Faixa de valor (BRL)",
                              min_value=0.0, max_value=float(vmax),
                              value=(0.0, float(vmax)), key="flt_val_range")

    # Linha 2: SLA & Stalled
    st.markdown("<div class='section-title' style='margin-top:6px'>⏱️ SLA & Stalled</div>", unsafe_allow_html=True)
    c_sla, c_stalled = st.columns(2)
    with c_sla:
        sla_threshold = st.number_input("Fora do SLA se acima de (dias no estágio)",
                                        min_value=1, max_value=180, value=14, step=1, key="flt_sla_thr")
    with c_stalled:
        stalled_after = st.number_input("Considerar 'parado' se sem avanço há (dias)",
                                        min_value=1, max_value=365, value=14, step=1, key="flt_stalled_after")

    # Linha 3: Forecast
    st.markdown("<div class='section-title' style='margin-top:6px'>🎯 Forecast</div>", unsafe_allow_html=True)
    c_scn = st.columns(3)
    with c_scn[0]:
        scenario = st.selectbox("Cenário de probabilidade",
                                ["Conservador", "Base", "Agressivo"], index=1,
                                key="flt_scenario")
    mult = {"Conservador": 0.8, "Base": 1.0, "Agressivo": 1.2}[scenario]

    with c_scn[1]:
        vspace(25)
        with st.expander("Probabilidades por estágio (ajuste fino)"):
            base_probs = {
                "Criado": 0.05, "1º Contato": 0.10, "Reunião Marcada": 0.25,
                "Reunião Realizada": 0.50, "Assinado": 0.80,
                "Closed Won": 1.00, "Closed Lost": 0.00,
            }
            probs = {}
            for s in sorted(set(stages_all) | set(base_probs.keys())):
                p0 = float(base_probs.get(s, 0.05))
                probs[s] = st.number_input(f"P({s})", min_value=0.0, max_value=1.0, value=p0, step=0.01, key=f"prob_{s}")
            probs = {k: float(min(1.0, max(0.0, v * mult))) for k, v in probs.items()}

    with c_scn[2]:
        vspace(25)
        with st.expander("Offset de fechamento esperado (meses por estágio)"):
            base_offsets = {"Assinado": 0, "Reunião Realizada": 1, "Reunião Marcada": 2, "1º Contato": 3, "Criado": 4}
            offsets = {}
            for s in sorted(set(stages_all) | set(base_offsets.keys())):
                offsets[s] = int(st.number_input(f"Offset({s})", min_value=0, max_value=12,
                                                 value=int(base_offsets.get(s, 3)), step=1, key=f"off_{s}"))

    st.markdown("</div>", unsafe_allow_html=True)  # fecha .section

    return dict(
        status=status, stages=stages, owners=owners, origens=origens,
        val_range=val_range, sla_threshold=sla_threshold, stalled_after=stalled_after,
        probs=probs, offsets=offsets,
    )

@st.cache_data(show_spinner=False)
def _apply_filters(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    f = df.copy()
    if params["status"]:
        f = f[f["status"].isin(params["status"])]
    if params["stages"]:
        f = f[f["estagio_atual_canonical"].isin(params["stages"])]
    if params["owners"]:
        f = f[f["proprietario"].isin(params["owners"])]
    if params["origens"]:
        f = f[f["origem"].isin(params["origens"])]
    lo, hi = params["val_range"]
    f = f[(f["valor"] >= lo) & (f["valor"] <= hi)]
    return f

# -------------------------------  KPIs  -------------------------------

def render_kpis(df: pd.DataFrame, params: dict):
    df_open = df[df["status"] == "open"] if "open" in df["status"].unique() else df
    total_abertos = int(len(df_open))
    valor_aberto = float(df_open["valor"].sum())
    ticket_medio_aberto = float(df_open["valor"].mean()) if total_abertos else 0.0
    w = df[df["status"] == "won"].shape[0]
    l = df[df["status"] == "lost"].shape[0]
    win_rate = (w / (w + l)) * 100 if (w + l) > 0 else 0.0
    idade_media = float(df_open["idade_dias"].mean()) if total_abertos else 0.0

    st.markdown("<div class='section'><div class='section-title'>📌 KPIs</div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Negócios Abertos", f"{total_abertos:,}".replace(",", "."))
    c2.metric("Valor Aberto", _fmt_brl(valor_aberto))
    c3.metric("Ticket Médio (abertos)", _fmt_brl(ticket_medio_aberto))
    c4.metric("Win Rate (global)", f"{win_rate:.1f}%")
    c5.metric("Idade média do pipeline", f"{idade_media:.0f} dias")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------  Kanban  -------------------------------

def render_kanban(df: pd.DataFrame, params: dict):
    st.markdown("<div class='section'><div class='section-title'>🗂️ Snapshot por estágio (Kanban)</div>", unsafe_allow_html=True)
    stages = list(pd.Series(df["estagio_atual_canonical"].dropna().unique()).sort_values())
    if not stages:
        st.info("Sem estágios para exibir com os filtros atuais.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    cols = st.columns(len(stages))
    for col, stage in zip(cols, stages):
        sub = df[df["estagio_atual_canonical"] == stage].copy()
        sub = sub.sort_values(["dias_no_estagio_atual", "valor"], ascending=[False, False])
        total = len(sub)
        valor = float(sub["valor"].sum())
        col.markdown(f"<span class='badge'><b>{stage}</b></span> ", unsafe_allow_html=True)
        col.caption(f"{total} deals · {_fmt_brl(valor)}")
        show_cols = [c for c in ["deal_key", "valor", "proprietario", "dias_no_estagio_atual", "origem"] if c in sub.columns]
        col.dataframe(
            sub[show_cols].head(50).rename(columns={
                "valor": "Valor", "proprietario": "Owner",
                "dias_no_estagio_atual": "Dias no estágio", "origem": "Origem", "deal_key": "Deal"
            }),
            hide_index=True, use_container_width=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------  Heatmap SLA  -------------------------------

def render_sla_heatmap(df: pd.DataFrame, params: dict):
    st.markdown("<div class='section'><div class='section-title'>🧯 SLA — % fora do limite por Owner × Estágio</div>", unsafe_allow_html=True)
    if "dias_no_estagio_atual" not in df.columns:
        st.info("Coluna 'dias_no_estagio_atual' ausente.")
        st.markdown("</div>", unsafe_allow_html=True); return

    df_open = df[df["status"] == "open"] if "open" in df["status"].unique() else df
    if df_open.empty:
        st.info("Sem dados abertos para calcular SLA.")
        st.markdown("</div>", unsafe_allow_html=True); return

    thr = params["sla_threshold"]
    df_open = df_open.copy()
    df_open["fora_sla"] = df_open["dias_no_estagio_atual"] > thr
    df_open["_owner"] = df_open["proprietario"].fillna("(sem owner)")

    pvt = pd.pivot_table(
        df_open, index="_owner", columns="estagio_atual_canonical",
        values="fora_sla",
        aggfunc=lambda x: np.mean(pd.Series(x).astype(float)) if len(x) else np.nan,
    ).fillna(0.0) * 100.0

    if pvt.empty:
        st.info("Não há dados suficientes para o heatmap nos filtros atuais.")
        st.markdown("</div>", unsafe_allow_html=True); return

    # Cores: do escuro → dourado (alta % fora do SLA chama atenção)
    colorscale = [
        [0.00, "#0f1117"],
        [0.10, "#1a1f2b"],
        [0.40, "#3b3f4a"],
        [0.70, "#6f5e1f"],
        [1.00, GOLD],
    ]
    fig = px.imshow(
        pvt, text_auto=True, aspect="auto",
        labels=dict(color="% fora do SLA"), color_continuous_scale=colorscale
    )
    fig.update_traces(texttemplate="%{z:.0f}%")
    fig.update_coloraxes(colorbar_title="% fora do SLA")
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------  Forecast  -------------------------------

def _expected_month(ts: pd.Timestamp, add_months: int) -> pd.Timestamp:
    if pd.isna(ts):
        ts = pd.Timestamp.today()
    base = pd.Timestamp(year=ts.year, month=ts.month, day=1)
    return base + pd.offsets.DateOffset(months=int(add_months))

def render_forecast(df: pd.DataFrame, params: dict):
    st.markdown("<div class='section'><div class='section-title'>📈 Forecast — Aberto vs. Ponderado e Linha do Tempo</div>", unsafe_allow_html=True)

    probs = params["probs"]; offsets = params["offsets"]
    df_open = df[df["status"] == "open"] if "open" in df["status"].unique() else df
    if df_open.empty:
        st.info("Sem deals abertos para compor forecast.")
        st.markdown("</div>", unsafe_allow_html=True); return

    df_open = df_open.copy()
    df_open["prob_win_atual"] = df_open["estagio_atual_canonical"].map(probs).fillna(0.0).astype(float)
    df_open["pipeline_ponderado"] = df_open["valor"] * df_open["prob_win_atual"]

    stage_summary = df_open.groupby("estagio_atual_canonical").agg(
        valor_aberto=("valor", "sum"),
        valor_ponderado=("pipeline_ponderado", "sum"),
        deals=("valor", "size"),
    ).reset_index()

    # Barras (aberto vs ponderado) — paleta neutra + dourado
    stage_long = stage_summary.melt(
        id_vars="estagio_atual_canonical",
        value_vars=["valor_aberto", "valor_ponderado"],
        var_name="tipo", value_name="valor"
    )
    bar_colors = {"valor_aberto": "#9aa0a6", "valor_ponderado": GOLD}
    fig1 = px.bar(
        stage_long, x="estagio_atual_canonical", y="valor", color="tipo",
        barmode="group", labels={"estagio_atual_canonical": "Estágio", "valor": "Valor (BRL)", "tipo": "Métrica"},
        color_discrete_map=bar_colors
    )
    fig1.update_traces(marker_line_width=0, hovertemplate="<b>%{x}</b><br>%{legendgroup}: R$ %{y:,.0f}<extra></extra>")
    fig1.update_yaxes(tickprefix="R$ ", separatethousands=True)
    fig1.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    apply_plotly_theme(fig1)
    st.plotly_chart(fig1, use_container_width=True)

    # Linha do tempo: realizado (wins) + previsto (ponderado)
    wins = df[df["status"] == "won"].copy()
    if not wins.empty and "ganhou_em" in wins.columns:
        wins["mes"] = wins["ganhou_em"].dt.to_period("M").dt.to_timestamp()
        wins_m = wins.groupby("mes")["valor"].sum().reset_index(name="Realizado")
    else:
        wins_m = pd.DataFrame({"mes": [], "Realizado": []})

    df_open["_offset"] = df_open["estagio_atual_canonical"].map(offsets).fillna(3).astype(int)
    today = pd.Timestamp.today()
    df_open["mes"] = df_open.apply(lambda r: _expected_month(today, int(r["_offset"])), axis=1)
    prev_m = df_open.groupby("mes")["pipeline_ponderado"].sum().reset_index(name="Previsto (ponderado)")

    timeline = pd.merge(wins_m, prev_m, on="mes", how="outer").fillna(0.0).sort_values("mes")
    if timeline.empty:
        st.info("Sem dados suficientes para a linha do tempo.")
        st.markdown("</div>", unsafe_allow_html=True); return

    tl_long = timeline.melt(id_vars="mes", value_vars=["Realizado", "Previsto (ponderado)"],
                            var_name="Série", value_name="Valor")

    # Cores/dash: Realizado (branco sólido), Previsto (dourado tracejado)
    line_colors = {"Realizado": WHITE, "Previsto (ponderado)": GOLD}
    line_dash_map = {"Realizado": "solid", "Previsto (ponderado)": "dash"}

    fig2 = px.line(
        tl_long, x="mes", y="Valor", color="Série", markers=True,
        color_discrete_map=line_colors, line_dash="Série",
        category_orders={"Série": ["Previsto (ponderado)", "Realizado"]}  # legenda coerente (previsto antes)
    )
    for tr in fig2.data:
        tr.line.width = 2.5
        tr.line.dash = line_dash_map.get(tr.name, "solid")
        tr.marker.size = 7
        tr.hovertemplate = "<b>%{x|%b/%Y}</b><br>%{fullData.name}: R$ %{y:,.0f}<extra></extra>"
    fig2.update_yaxes(tickprefix="R$ ", separatethousands=True)
    fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    apply_plotly_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)

    # KPIs do forecast
    k1, k2, k3 = st.columns(3)
    k1.metric("Valor Aberto (∑)", _fmt_brl(float(df_open["valor"].sum())))
    k2.metric("Pipeline Ponderado (∑)", _fmt_brl(float(df_open["pipeline_ponderado"].sum())))
    k3.metric("Estágio com maior ∑ ponderado", stage_summary.sort_values("valor_ponderado", ascending=False)["estagio_atual_canonical"].iloc[0] if not stage_summary.empty else "—")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------  Main  -------------------------------

def render_pipeline_forecast(deals_df: pd.DataFrame):
    st.title("Pipeline & Forecast — deals_master")

    df0 = _prepare(deals_df)
    params = filter_controls(df0)
    df = _apply_filters(df0, params)

    if df.empty:
        st.warning("Nenhuma linha com os filtros atuais.")
        st.stop()

    render_kpis(df, params)
    st.divider()

    # Duas colunas: Kanban e Heatmap lado a lado
    cL, cR = st.columns([2, 1])
    with cL:
        render_kanban(df, params)
    with cR:
        render_sla_heatmap(df, params)

    st.divider()
    render_forecast(df, params)

# Entradas possíveis
if __name__ == "__main__":
    st.set_page_config(page_title="Pipeline & Forecast — deals_master", layout="wide")
    df_candidate = None
    for key in ("deals_master", "jaws_master", "df_deals", "df"):
        if key in st.session_state and isinstance(st.session_state[key], pd.DataFrame):
            df_candidate = st.session_state[key]; break
    if df_candidate is None:
        g = globals()
        for key in ("deals_master", "jaws_master", "df_deals", "df"):
            if key in g and isinstance(g[key], pd.DataFrame):
                df_candidate = g[key]; break
    if df_candidate is None:
        st.error("Não encontrei o DataFrame do deals_master/jaws_master nesta página. Passe-o para render_pipeline_forecast(df) ou coloque em st.session_state['deals_master'].")
    else:
        render_pipeline_forecast(df_candidate)
