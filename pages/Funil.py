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
import numpy as np

from funcs import carregar_dataframes, precisa_atualizar
from utils import formatar_data_base, metricas_reunioes_sdr_vs_consultor, vspace
from sidebar import setup_sidebar

##############################################################################
##                           Autenticação e cache                           ##
##############################################################################

# =========================
# ---------- TEMA ---------
# =========================
# Paleta & helpers
GOLD      = "#D4AF37"
GOLD_DIM  = "#b9972f"
WHITE     = "#FFFFFF"
BLACK     = "#0B0B0C"
GRAPH_BG  = "#0f1117"   # fundo dos gráficos
GRAPH_GRID= "#2a2d37"   # cor da grade
TEXT_DIM  = "#C9CCD6"
TEXT_SOFT = "#A3A7B3"
BORDER    = "rgba(212,175,55,0.25)"

def apply_plotly_theme(fig, *, with_legend=True):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=GRAPH_BG,
        plot_bgcolor=GRAPH_BG,
        font=dict(family="Inter, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, sans-serif",
                  color=WHITE, size=13),
        legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0) if with_legend else dict(orientation="h", y=-0.2),
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
st.logo(image='z_logo_light.png', size='large')
st.write(""); st.write(""); st.write("")

# =========================
# ---------- CSS ----------
# =========================
st.markdown(f"""
<style>
/* Base */
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
/* Sidebar */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #0d0e12 0%, #0b0c10 100%);
  border-right: 1px solid rgba(255,255,255,0.03);
}}
[data-testid="stSidebar"] * {{ color: var(--text-dim) !important; }}
[data-testid="stSidebar"] .st-bx {{
  background: #0e1016 !important;
  border: 1px solid rgba(255,255,255,0.04) !important;
}}
/* Títulos */
h1, h2, h3, h4 {{
  letter-spacing: 0.2px;
  color: var(--text);
}}
/* Inputs */
.stSelectbox, .stMultiSelect, .stDateInput, .stRadio, .stSlider, .stTextInput, .stNumberInput {{
  padding: 6px 10px;
  border-radius: 12px;
  background: #10131a30;
  border: 1px solid rgba(255,255,255,0.07);
}}
/* Botões */
.stButton>button {{
  background: linear-gradient(180deg, #12141c 0%, #0e1118 100%);
  border: 1px solid var(--gold-border);
  color: var(--text);
  border-radius: 12px;
  padding: 0.55rem 0.9rem;
  transition: transform .08s ease, box-shadow .08s ease, border-color .2s;
}}
.stButton>button:hover {{
  transform: translateY(-1px);
  border-color: rgba(212,175,55,0.6);
  box-shadow: 0 10px 30px rgba(212,175,55,0.08);
}}
/* Tabs */
[data-baseweb="tab-list"] {{
  gap: .25rem;
  border-bottom: 1px solid rgba(255,255,255,0.07);
}}
[data-baseweb="tab"] {{
  background: #0f1218;
  color: var(--text-soft);
  border: 1px solid rgba(255,255,255,0.06);
  border-bottom: none;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
}}
[data-baseweb="tab"][aria-selected="true"] {{
  color: var(--text);
  background: linear-gradient(180deg, #12141c 0%, #0f1218 100%);
  border-color: rgba(212,175,55,0.35);
  box-shadow: inset 0 -2px 0 0 var(--gold);
}}
/* Métricas */
[data-testid="stMetricValue"], [data-testid="stMetricDelta"] {{
  color: var(--text) !important;
}}
[data-testid="stMetric"] {{
  background: #0e1016;
  border: 1px solid rgba(212,175,55,0.18);
  border-radius: 14px;
  padding: 10px 12px;
}}
/* Dataframe */
[data-testid="stDataFrame"] {{
  background: #0f1117;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
}}
/* Cards de conversão */
.conv-card {{
  padding: 0.7rem 0.9rem;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(28,28,28,0.98) 0%, rgba(18,18,18,0.98) 100%);
  border: 1px solid var(--gold-border);
  margin-bottom: 0.6rem;
  transition: transform 0.08s ease, box-shadow 0.08s ease;
}}
.conv-card:hover {{
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(0,0,0,0.25);
}}
.conv-flow {{
  display: flex; align-items: center; gap: 0.45rem;
  font-size: 0.92rem; font-weight: 600; color: var(--text);
}}
.conv-flow .arrow {{ color: var(--gold); font-weight: 800; }}
.conv-value {{ margin-top: 0.15rem; font-size: 1.5rem; font-weight: 900; color: var(--gold); }}
.section-title {{ font-weight: 700; font-size: 1.0rem; margin: 0 0 0.6rem 0; color: var(--text); }}
.small {{ font-size: 0.85rem; color: #8e94a3; }}
.ok {{ color:#10b981; }} .warn{{ color:#f59e0b; }} .bad{{ color:#ef4444; }}
.pill {{ display:inline-block; padding:3px 8px; border-radius:999px; background:#131722; margin-right:6px; color:{TEXT_DIM}; border:1px solid rgba(255,255,255,0.06); }}
/* Expander */
.streamlit-expanderHeader {{
  background: #0f1218; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px; padding: 10px 12px;
}}
/* Legendas e captions */
.block-container p, .caption, .stCaption, .stMarkdown p {{
  color: var(--text-dim) !important;
}}
</style>
""", unsafe_allow_html=True)

# Chama a sidebar (mantém lógica original)
setup_sidebar()

with st.sidebar:
    if precisa_atualizar():
        carregar_dataframes()
        st.session_state["ultima_atualizacao"] = time.time()

    if st.button(label='🔄 Recarregar Planilhas'):
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

# =========================
# ------- ESTILO UI ------- (ajustes mínimos conservados)
# =========================
st.markdown(
    """
    <style>
    .small { font-size: 0.85rem; color:#6b7280; }
    .ok { color:#10b981; } .warn{ color:#f59e0b; } .bad{ color:#ef4444; }
    .pill { display:inline-block; padding:3px 8px; border-radius:999px; background:#131722; margin-right:6px; border:1px solid rgba(255,255,255,0.06); }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# ------ PARÂMETROS -------
# =========================

STAGES_POS = ["Criado", "1º Contato", "Reunião Marcada", "Reunião Realizada", "Assinado", "Ganhou"]
STAGES_TERMINAIS = ["Perdeu"]
STAGES_RAMO = ["No Show"]
ALL_STAGES = STAGES_POS + STAGES_TERMINAIS + STAGES_RAMO

stage_events = stage_events.copy()
stage_events["event_dt"] = pd.to_datetime(stage_events["event_dt"], errors="coerce")
stage_events["stage"] = stage_events["stage"].astype(str)

DIM_CANDIDATAS = ["origem", "sdr", "proprietario", "faixa_patrimonio", "tags"]
DIMENSOES = [c for c in DIM_CANDIDATAS if c in stage_events.columns]

if "valor" not in stage_events.columns:
    stage_events["valor"] = np.nan
valor_por_deal = (
    stage_events.sort_values("event_dt")
    .groupby("deal_key", as_index=False)["valor"]
    .first()
    .set_index("deal_key")["valor"]
)

# =========================
# ---- FUNÇÕES AUX. -------
# =========================

@st.cache_data(show_spinner=False)
def primeiras_datas_por_estagio(stage_events: pd.DataFrame) -> pd.DataFrame:
    se = stage_events[stage_events["stage"].isin(ALL_STAGES)].copy()
    first = (
        se.sort_values("event_dt")
          .groupby(["deal_key", "stage"], as_index=False)["event_dt"].min()
    )
    wide = first.pivot(index="deal_key", columns="stage", values="event_dt")
    wide = wide.rename(columns={s: f"dt_{s.lower().replace(' ', '_')}" for s in wide.columns})
    wide.columns.name = None
    dims = {}
    for d in DIMENSOES + ["valor"]:
        if d in stage_events.columns:
            dims[d] = (stage_events.groupby("deal_key")[d].first())
    dims_df = pd.DataFrame(dims)
    out = wide.join(dims_df, how="left")
    return out

def filtrar_coorte(wide: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    col = "dt_criado"
    if col not in wide.columns:
        alt = [c for c in wide.columns if c.startswith("dt_criado")]
        if alt:
            col = alt[0]
        else:
            return wide.iloc[0:0]
    mask = (wide[col].notna()) & (wide[col].dt.date >= start) & (wide[col].dt.date <= end)
    return wide.loc[mask].copy()

def aplicar_horizonte(stage_events: pd.DataFrame, deals_coorte: pd.Series, horizonte: dict) -> pd.DataFrame:
    se = stage_events[stage_events["deal_key"].isin(deals_coorte)].copy()
    if horizonte["tipo"] == "hoje":
        return se
    if horizonte["tipo"] == "data":
        limite = pd.to_datetime(horizonte["ate"]) + pd.offsets.Day(1) - pd.offsets.Second(1)
        return se[se["event_dt"] <= limite]
    if horizonte["tipo"] == "dias_pos_criacao":
        firsts = primeiras_datas_por_estagio(stage_events)
        base = firsts.loc[deals_coorte, ["dt_criado"]].copy()
        base["limite"] = base["dt_criado"] + pd.to_timedelta(horizonte["dias"], unit="D")
        se = se.merge(base[["limite"]], left_on="deal_key", right_index=True, how="left")
        return se[se["event_dt"] <= se["limite"]]
    return se

def dados_funil(firsts: pd.DataFrame) -> pd.DataFrame:
    data = []
    total_coorte = len(firsts)
    for s in STAGES_POS:
        col = f"dt_{s.lower().replace(' ', '_')}"
        count = int(firsts[col].notna().sum()) if col in firsts.columns else 0
        data.append({"estagio": s, "count": count, "pct_coorte": (count/total_coorte*100 if total_coorte else 0)})
    return pd.DataFrame(data)

def tabela_transicoes(firsts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    d = firsts
    def c(name): return f"dt_{name.lower().replace(' ', '_')}"
    for i, j in zip(STAGES_POS[:-1], STAGES_POS[1:]):
        ci, cj = c(i), c(j)
        base = d[d[ci].notna()].copy()
        expostos = len(base)
        conv_mask = base[cj].notna() & (base[cj] >= base[ci])
        convertidos = int(conv_mask.sum())
        perdeu_col = c("Perdeu")
        perdeu_mask = pd.Series(False, index=base.index)
        if perdeu_col in base.columns:
            perdeu_mask = base[perdeu_col].notna() & (base[perdeu_col] >= base[ci])
            if cj in base.columns:
                perdeu_mask &= (~base[cj].notna() | (base[perdeu_col] < base[cj]))
        noshow_col = c("No Show")
        noshow_mask = pd.Series(False, index=base.index)
        if i == "Reunião Marcada" and j == "Reunião Realizada" and noshow_col in base.columns:
            noshow_mask = base[noshow_col].notna() & (base[noshow_col] >= base[ci])
            if cj in base.columns:
                noshow_mask &= (~base[cj].notna() | (base[noshow_col] < base[cj]))
        pendentes = int((~conv_mask & ~perdeu_mask & ~noshow_mask).sum())
        lead_days = (base.loc[conv_mask, cj] - base.loc[conv_mask, ci]).dt.days
        mediana_dias = float(lead_days.median()) if not lead_days.empty else np.nan
        rows.append({
            "transicao": f"{i} → {j}",
            "expostos": int(expostos),
            "convertidos": int(convertidos),
            "% conversao": round(convertidos / expostos * 100, 2) if expostos else 0.0,
            "pendentes": int(pendentes),
            "perdeu": int(perdeu_mask.sum()),
            "no_show": int(noshow_mask.sum()),
            "mediana_dias": mediana_dias,
        })
    return pd.DataFrame(rows)

def dados_sankey(firsts: pd.DataFrame) -> tuple[list, list, list]:
    nodes = STAGES_POS + ["Perdeu", "No Show", "Pendente"]
    idx = {n:i for i,n in enumerate(nodes)}
    links = {}
    def c(name): return f"dt_{name.lower().replace(' ', '_')}"
    for i, j in zip(STAGES_POS[:-1], STAGES_POS[1:]):
        ci, cj = c(i), c(j)
        mask = firsts[ci].notna() & firsts[cj].notna() & (firsts[cj] >= firsts[ci])
        key = (idx[i], idx[j])
        links[key] = links.get(key, 0) + int(mask.sum())
    if c("Reunião Marcada") in firsts and c("No Show") in firsts:
        base = firsts[firsts[c("Reunião Marcada")].notna()].copy()
        noshow_mask = base[c("No Show")].notna()
        key = (idx["Reunião Marcada"], idx["No Show"])
        links[key] = links.get(key, 0) + int(noshow_mask.sum())
    if c("Perdeu") in firsts:
        perdeu = firsts[firsts[c("Perdeu")].notna()].copy()
        if not perdeu.empty:
            for _, r in perdeu.iterrows():
                alc = [(s, r[c(s)]) for s in STAGES_POS if s != "Ganhou" and c(s) in perdeu.columns and pd.notna(r.get(c(s)))]
                if not alc: continue
                last = max(alc, key=lambda x: x[1])[0]
                key = (idx[last], idx["Perdeu"])
                links[key] = links.get(key, 0) + 1
    pend = firsts.copy()
    ganhou_col, perdeu_col = c("Ganhou"), c("Perdeu")
    if ganhou_col in pend.columns:
        pend = pend[pend[ganhou_col].isna()]
    if perdeu_col in pend.columns:
        pend = pend[pend[perdeu_col].isna()]
    if not pend.empty:
        for _, r in pend.iterrows():
            alc = [(s, r.get(c(s))) for s in STAGES_POS if pd.notna(r.get(c(s)))]
            if not alc: continue
            last = max(alc, key=lambda x: x[1])[0]
            key = (idx[last], idx["Pendente"])
            links[key] = links.get(key, 0) + 1
    src, tgt, val = [], [], []
    for (s,t), v in links.items():
        if v > 0:
            src.append(s); tgt.append(t); val.append(v)
    return nodes, src, tgt, val

def serie_entrantes(firsts: pd.DataFrame, freq: str = "W") -> pd.DataFrame:
    records = []
    for s in STAGES_POS:
        col = f"dt_{s.lower().replace(' ', '_')}"
        if col not in firsts.columns: continue
        tmp = firsts[[col]].dropna().copy()
        tmp["dt"] = tmp[col].dt.to_period(freq).dt.start_time
        agg = tmp.groupby("dt").size().reset_index(name="count")
        agg["stage"] = s
        records.append(agg)
    if not records:
        return pd.DataFrame(columns=["dt","count","stage"])
    return pd.concat(records, ignore_index=True)

def lead_times_i_j(firsts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    def c(name): return f"dt_{name.lower().replace(' ', '_')}"
    for i, j in zip(STAGES_POS[:-1], STAGES_POS[1:]):
        ci, cj = c(i), c(j)
        mask = firsts[ci].notna() & firsts[cj].notna() & (firsts[cj] >= firsts[ci])
        if not mask.any(): continue
        dias = (firsts.loc[mask, cj] - firsts.loc[mask, ci]).dt.days
        tmp = pd.DataFrame({"transicao": f"{i} → {j}", "dias": dias})
        rows.append(tmp)
    if not rows:
        return pd.DataFrame(columns=["transicao","dias"])
    return pd.concat(rows, ignore_index=True)

def win_rate_por_dim(firsts: pd.DataFrame, dim: str) -> pd.DataFrame:
    def c(name): return f"dt_{name.lower().replace(' ', '_')}"
    if dim not in firsts.columns:
        return pd.DataFrame(columns=[dim, "criadas", "wins", "win_rate_%"])
    base = firsts.copy()
    base["_dim"] = base[dim].fillna("(sem)")
    criadas = base.groupby("_dim").size().rename("criadas")
    wins = base[base[c("Ganhou")].notna()].groupby("_dim").size().rename("wins")
    out = pd.concat([criadas, wins], axis=1).fillna(0)
    out["win_rate_%"] = (out["wins"] / out["criadas"] * 100).round(2)
    out = out.reset_index().rename(columns={"_dim": dim})
    return out.sort_values("criadas", ascending=False)

# =========================
# ------- CONTROLES -------
# =========================

st.title("Funil Comercial — Coortes e Conversões")

firsts_all = primeiras_datas_por_estagio(stage_events)
min_dt = pd.to_datetime(firsts_all.filter(like="dt_criado").stack().min()) if not firsts_all.empty else pd.Timestamp("2023-01-01")
max_dt = pd.to_datetime(firsts_all.filter(like="dt_criado").stack().max()) if not firsts_all.empty else pd.Timestamp.today()

c1, c2, c3 = st.columns([1,1,2])
with c1:
    d_ini = st.date_input("Coorte: Criado a partir de", value=(max_dt - pd.Timedelta(days=30)).date(), min_value=min_dt.date(), max_value=max_dt.date())
with c2:
    d_fim = st.date_input("Coorte: Criado até", value=max_dt.date(), min_value=min_dt.date(), max_value=max_dt.date())

with c3:
    opt = st.radio("Horizonte de observação", ["Até hoje", "Até data específica", "Até X dias após criação"], horizontal=True)
    if opt == "Até hoje":
        horizonte = {"tipo":"hoje"}
    elif opt == "Até data específica":
        h_data = st.date_input("Observar eventos até", value=date.today())
        horizonte = {"tipo":"data", "ate": h_data}
    else:
        h_dias = st.slider("Observar até X dias após criação", min_value=7, max_value=365, value=90, step=1)
        horizonte = {"tipo":"dias_pos_criacao", "dias": h_dias}

# Filtros por dimensão (opcional)
if DIMENSOES:
    with st.expander("Filtros por dimensão", expanded=False):
        filtros = {}
        cols = st.columns(len(DIMENSOES))
        for i, d in enumerate(DIMENSOES):
            with cols[i]:
                if d in stage_events.columns:
                    vals = sorted(stage_events[d].dropna().astype(str).unique().tolist())
                    sel = st.multiselect(f"Filtrar {d}", vals, default=[], key=f"filtro_{d}")
                else:
                    st.warning(f"Dimensão '{d}' não encontrada na base.")
                    sel = []
                filtros[d] = set(sel)
else:
    filtros = {}

se_filtrado = stage_events.copy()
for d, sel in filtros.items():
    if sel:
        se_filtrado = se_filtrado[se_filtrado[d].astype(str).isin(sel)]

firsts = primeiras_datas_por_estagio(se_filtrado)
firsts_coorte = filtrar_coorte(firsts, d_ini, d_fim)
se_coorte = aplicar_horizonte(se_filtrado, firsts_coorte.index, horizonte)

# =========================
# -------- VISÕES ---------
# =========================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Funil",
    "🔁 Transições",
    "🪄 Sankey",
    "📈 Série Temporal",
    "⏱️ Lead Times",
    "🧩 Quebras por Dimensão",
])

# ---------- TAB 1: FUNIL ----------
with tab1:
    st.subheader("Funil da Coorte (ever reached)")

    df_funil = dados_funil(firsts_coorte)

    # ordem "natural" das etapas (de cima para baixo, como vêm do df_funil)
    base_order = df_funil["estagio"].drop_duplicates().tolist()

    # KPI'S
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total = len(firsts_coorte)
    wins = int(firsts_coorte.filter(like="dt_ganhou").notna().any(axis=1).sum()) if total else 0
    losses = int(firsts_coorte.filter(like="dt_perdeu").notna().any(axis=1).sum()) if total else 0
    valor_total = float(firsts_coorte["valor"].fillna(0).sum()) if "valor" in firsts_coorte else 0.0

    # --- MÉTRICAS (mesma linha): 4 KPIs + 2 conversões (Consultor/SDR) no estilo .conv-card ---
    met = metricas_reunioes_sdr_vs_consultor(se_coorte, firsts_coorte)

    def render_card(col, titulo: str, valor: str, subtitulo: str = "", pills: list[str] = None):
        pills = pills or []
        with col:
            st.markdown(
                f"""
                <div class="conv-card">
                <div class="conv-flow">
                    <span class="from">{titulo}</span>
                    {''.join([f'<span class="pill">{p}</span>' for p in pills])}
                </div>
                <div class="conv-value">{valor}</div>
                {f'<div class="small">{subtitulo}</div>' if subtitulo else ''}
                </div>
                """,
                unsafe_allow_html=True
            )

    # Linha com 6 colunas (4 KPIs + 2 cards de conversão)
    k1, k2, k3, k4, k5, k6 = st.columns([1,1,1,1,2,2])

    # KPIs antigos no novo visual
    render_card(k1, "Leads na coorte", f"{total:,}".replace(",", "."))
    render_card(k2, "Wins", f"{wins:,}".replace(",", "."))
    render_card(k3, "Losses", f"{losses:,}".replace(",", "."))
    render_card(k4, "Valor total (R$)", f"{valor_total:,.0f}".replace(",", "."))

    # Conversões por origem da reunião (Consultor / SDR)
    def card_conv(col, rotulo):
        row = met[met["bucket"] == rotulo]
        if row.empty:
            render_card(col, f"{rotulo} → Ganhou", "–", "Sem reuniões desse tipo no período/horizonte.")
            return
        r = row.iloc[0]
        conv = r["taxa_conversao_%"]
        total_b = int(r["deals_total"])
        won_b = int(r["deals_won"])
        lt = r.get("leadtime_mediano_dias", np.nan)
        lead_txt = f"Mediana: {lt:.1f} dias da reunião ao ganho" if pd.notna(lt) else "Mediana: —"
        render_card(col, f"{rotulo} → Ganhou", f"{conv:.1f}%", lead_txt, pills=[f"Base: {total_b}", f"Wins: {won_b}"])

    card_conv(k5, "Consultor")
    card_conv(k6, "SDR")


    # --- FILTRO DE ETAPAS (CHECKBOXES) ---
    st.markdown("**Etapas do funil a exibir**")
    # distribui as checkboxes em 3 colunas para ficar compacto
    cb_cols = st.columns(3)
    selected_flags = {}
    for i, stage in enumerate(base_order):
        with cb_cols[i % 3]:
            selected_flags[stage] = st.checkbox(stage, value=True, key=f"cb_{stage}")

    selected_stages = [s for s, v in selected_flags.items() if v]

    # se nada selecionado, avisa e encerra a tab
    if len(selected_stages) == 0:
        st.info("Selecione ao menos uma etapa para visualizar o funil e as conversões.")
        st.stop()

    # filtra df_funil pelas etapas selecionadas e reordena pela ordem base
    df_funil_sel = (
        df_funil[df_funil["estagio"].isin(selected_stages)]
        .copy()
    )
    df_funil_sel["estagio"] = pd.Categorical(df_funil_sel["estagio"], categories=base_order, ordered=True)
    df_funil_sel = df_funil_sel.sort_values("estagio").reset_index(drop=True)

    # recalcula % conversão (etapa atual / etapa anterior dentro do filtro)
    df_funil_sel["pct_conversao"] = df_funil_sel["count"] / df_funil_sel["count"].shift(1) * 100
    df_funil_sel.loc[0, "pct_conversao"] = 100

    # FUNIL
    col1, col_right = st.columns([2, 1.2])
    with col1:
        # paleta dourada em degradê (claro -> escuro); mapearemos por estágio
        funnel_palette = [GOLD, GOLD_DIM, "#8f7a2a", "#6f5e1f", "#514619", "#3a3312"]

        # constrói um mapa estágio -> cor, seguindo a base_order
        color_map_full = {stage: funnel_palette[i % len(funnel_palette)] for i, stage in enumerate(base_order)}
        # cores apenas das etapas visíveis, na ordem do eixo Y
        y_order = df_funil_sel["estagio"].tolist()[::-1]  # eixo Y do funnel é invertido para plotar topo no alto
        marker_colors = [color_map_full[s] for s in y_order]

        # inverte a ordem dos estágios para o eixo Y do plotly (para manter topo no alto)
        stage_order_plot = y_order  # já está invertido acima

        fig = px.funnel(
            df_funil_sel,
            x="count",
            y="estagio",
            category_orders={"estagio": stage_order_plot}
        )
        fig.update_traces(
            textinfo="value+percent initial",
            textfont_color=WHITE,
            opacity=0.95,
            marker=dict(color=marker_colors)
        )
        apply_plotly_theme(fig)
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption("Regra: contabilizamos a **primeira entrada** de cada negócio em cada estágio (ever reached).")

    # Cards de conversão (etapa → etapa) considerando apenas as etapas selecionadas
    with col_right:
        st.markdown('<div class="section-title">🔄 Conversão etapa → etapa</div>', unsafe_allow_html=True)
        df_seq = df_funil_sel.reset_index(drop=True)
        for idx in range(1, len(df_seq)):
            from_stage = df_seq.loc[idx-1, "estagio"]
            to_stage   = df_seq.loc[idx, "estagio"]
            pct        = df_seq.loc[idx, "pct_conversao"]
            st.markdown(
                f"""
                <div class="conv-card">
                  <div class="conv-flow">
                    <span class="from">{from_stage}</span>
                    <span class="arrow">→</span>
                    <span class="to">{to_stage}</span>
                  </div>
                  <div class="conv-value">{pct:.1f}%</div>
                </div>
                """,
                unsafe_allow_html=True
            )

# ------ TAB 2: TRANSIÇÕES ------
with tab2:
    st.subheader("Tabela de Transições i → j")
    df_trans = tabela_transicoes(firsts_coorte)
    st.dataframe(df_trans, use_container_width=True)

    figc = px.bar(
        df_trans, x="transicao", y="% conversao",
        text="% conversao", color_discrete_sequence=[GOLD]
    )
    figc.update_traces(
        texttemplate="%{text:.1f}%",
        hovertemplate="<b>%{x}</b><br>% Conversão: %{y:.1f}%<extra></extra>",
        marker_line=dict(width=0)
    )
    figc.update_layout(yaxis_title="% conversão", xaxis_title="Transição", height=420)
    apply_plotly_theme(figc)
    st.plotly_chart(figc, use_container_width=True)

# ---------- TAB 3: SANKEY ----------
with tab3:
    st.subheader("Fluxos do Funil (Sankey)")
    nodes, src, tgt, val = dados_sankey(firsts_coorte)
    if val:
        # Paleta mais diferenciada
        node_colors = [
            "#1f77b4",   # Criado → azul
            "#2ca02c",   # 1º Contato → verde
            "#9467bd",   # Reunião Marcada → roxo
            "#17becf",   # Reunião Realizada → ciano
            "#ff7f0e",   # Assinado → laranja
            GOLD,        # Ganhou → dourado destaque
            "#e74c3c",   # Perdeu → vermelho
            "#f39c12",   # No Show → laranja forte
            "#7f8c8d"    # Pendente → cinza
        ]

        link_colors = ["rgba(255,255,255,0.2)"] * len(val)  # links neutros (brancos translúcidos)

        sankey = go.Figure(
            data=[go.Sankey(
                node=dict(label=nodes, pad=20, thickness=20, color=node_colors),
                link=dict(source=src, target=tgt, value=val, color=link_colors),
            )]
        )
        sankey.update_layout(
            paper_bgcolor=GRAPH_BG, plot_bgcolor=GRAPH_BG,
            font=dict(color=WHITE, size=12),
            margin=dict(l=10, r=10, t=10, b=10), height=520
        )
        st.plotly_chart(sankey, use_container_width=True)
    else:
        st.info("Não há fluxos suficientes para montar o Sankey nessa seleção.")

# ----- TAB 4: SÉRIE TEMPORAL -----
with tab4:
    st.subheader("Entrantes por Estágio ao Longo do Tempo")
    freq = st.radio("Frequência", ["Semanal", "Mensal"], horizontal=True, index=0)
    f = "W" if freq == "Semanal" else "M"
    serie = serie_entrantes(firsts_coorte, freq=f)
    if not serie.empty:
        # Paleta diferenciada (alta distinção + Ganhou em dourado)
        color_map = {
            "Criado": "#1f77b4",            # azul
            "1º Contato": "#2ca02c",        # verde
            "Reunião Marcada": "#9467bd",   # roxo
            "Reunião Realizada": "#17becf", # ciano
            "Assinado": "#ff7f0e",          # laranja
            "Ganhou": GOLD                  # dourado destaque
        }

        figt = px.line(
            serie,
            x="dt",
            y="count",
            color="stage",
            markers=True,
            category_orders={"stage": STAGES_POS},        # garante a ordem lógica dos estágios
            color_discrete_map=color_map                  # fixa as cores por estágio
        )
        figt.update_traces(mode="lines+markers", line=dict(width=2), marker=dict(size=6, opacity=0.9))
        figt.update_layout(
            xaxis_title="Período",
            yaxis_title="Entrantes",
            height=450
        )
        apply_plotly_theme(figt)
        st.plotly_chart(figt, use_container_width=True)
        st.caption("Contabiliza a **primeira entrada** por estágio e agrega por período.")
    else:
        st.info("Sem dados para a série temporal nesta seleção.")


# ----- TAB 5: LEAD TIMES (BOXPLOTS) -----
with tab5:
    st.subheader("Tempos de Avanço entre Estágios (dias)")
    lt = lead_times_i_j(firsts_coorte)
    if not lt.empty:
        figb = px.box(lt, x="transicao", y="dias", points="outliers",
                      color_discrete_sequence=[GOLD])
        figb.update_traces(marker=dict(opacity=0.85), selector=dict(type='box'))
        figb.update_layout(yaxis_title="Dias", xaxis_title="Transição", height=450)
        apply_plotly_theme(figb)
        st.plotly_chart(figb, use_container_width=True)
        st.caption("Dica: use a mediana como referência de SLA; p95 (não exibido) é útil para ver caudas longas.")
    else:
        st.info("Sem dados suficientes para calcular lead times.")

# ----- TAB 6: QUEBRAS POR DIMENSÃO -----
with tab6:
    st.subheader("Desempenho por Dimensão")
    if not DIMENSOES:
        st.info("Sua base não contém dimensões categóricas padrão (origem, sdr, proprietário...).")
    else:
        col1, col2 = st.columns([1,3])
        with col1:
            dim = st.selectbox("Escolha a dimensão", DIMENSOES, index=0)
        wr = win_rate_por_dim(firsts_coorte, dim)
        c1, c2 = st.columns([2,1])
        with c1:
            figd = px.bar(wr, x=dim, y="win_rate_%", hover_data=["criadas","wins"],
                          color_discrete_sequence=[GOLD])
            figd.update_traces(marker_line_width=0)
            figd.update_layout(yaxis_title="Win rate (%)", xaxis_title=dim, height=420)
            apply_plotly_theme(figd)
            st.plotly_chart(figd, use_container_width=True)
        with c2:
            st.dataframe(wr.head(20), use_container_width=True)
        st.caption("Win rate = #Ganhou / #Criado por categoria selecionada na coorte.")

# =========================
# ---- NOTAS E AJUSTES ----
# =========================
with st.expander("Notas de metodologia", expanded=False):
    st.markdown(
        """
        - A coorte é definida por **Criado entre [início–fim]** e o **horizonte** controla até quando observamos eventos (por padrão, *até hoje*).
        - O funil usa a **primeira entrada** por estágio (*ever reached*).
        - Na transição **Marcada → Realizada**, contabilizamos **No Show** como queda específica.
        - **Perdeu** é terminal e aparece no Sankey como saída do **último estágio positivo alcançado**.
        - Negócios **pendentes** (sem ganhar/perder) são enviados ao nó *Pendente* no Sankey.
        """,
        unsafe_allow_html=True
    )

st.dataframe(se_coorte, use_container_width=True)
