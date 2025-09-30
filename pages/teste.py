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
        title=dict(font=dict(size=18, color=WHITE, family="Inter, Segoe UI, Roboto"), x=0, xanchor="left"),
        legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)") if with_legend else dict(orientation="h", y=-0.2),
        hoverlabel=dict(bgcolor="#161922", bordercolor=GOLD, font=dict(color=WHITE, size=12)),
        margin=dict(l=16, r=16, t=40, b=16),
        xaxis=dict(gridcolor=GRAPH_GRID, zeroline=False, showspikes=True, spikethickness=1, spikecolor=GOLD, spikemode="across",
                   title_font=dict(size=12), tickfont=dict(size=12)),
        yaxis=dict(gridcolor=GRAPH_GRID, zeroline=False, showspikes=True, spikethickness=1, spikecolor=GOLD, spikemode="across",
                   title_font=dict(size=12), tickfont=dict(size=12))
    )
    return fig

# =========================
# ------ PAGE CONFIG ------
# =========================
st.set_page_config(page_title="📊 Funil", layout="wide")
st.logo(image='z_logo_light.png', size='large')
st.write(""); st.write(""); st.write("")

# =========================
# ---------- CSS ----------
# =========================
st.markdown(f"""
<style>
/* =========================================================
   Base & tokens
   =========================================================*/
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
  background:
    radial-gradient(1200px 800px at 20% -10%, rgba(212,175,55,0.06), transparent 60%),
    radial-gradient(900px 600px at 120% 10%, rgba(212,175,55,0.05), transparent 60%),
    var(--bg) !important;
}}
[data-testid="stHeader"] {{ background: transparent; }}

.block-container {{
  padding-top: .5rem !important;
  padding-bottom: 2rem !important;
  max-width: 1500px;
}}

/* =========================================================
   Tipografia & títulos
   =========================================================*/
h1, h2, h3, h4 {{
  letter-spacing: .2px;
  color: var(--text);
  margin: 0 0 .35rem 0;
}}
h1 {{ font-size: 1.6rem; font-weight: 800; }}
h2 {{ font-size: 1.25rem; font-weight: 700; }}
h3 {{ font-size: 1.05rem; font-weight: 700; color: var(--text-dim); }}

p, .stMarkdown, .caption, .stCaption {{ color: var(--text-dim) !important; }}

/* Header executivo (centralizado) */
.page-header.pro {{
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  text-align:center;
  padding: 18px 20px;
  background: linear-gradient(180deg,#141720 0%,#10141c 100%);
  border:1px solid rgba(255,255,255,0.08);
  border-radius:14px;
  box-shadow: inset 0 -3px 0 0 var(--gold);
  margin: 6px 0 18px 0;
}}
.ph-icon {{
  font-size: 2rem; line-height:1.2;
  margin-bottom: 6px;
  filter: drop-shadow(0 2px 6px rgba(212,175,55,0.25));
}}
.ph-title {{
  font-weight:800; font-size:1.6rem; color: var(--text); letter-spacing:.2px;
}}
.ph-sub {{ color: var(--text-soft); font-size:.95rem; margin-top:4px; }}

/* =========================================================
   Sidebar (polimento sutil — sem mudar lógica)
   =========================================================*/
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #0d0e12 0%, #0b0c10 100%);
  border-right: 1px solid rgba(255,255,255,0.03);
}}
[data-testid="stSidebar"] * {{ color: var(--text-dim) !important; }}
[data-testid="stSidebar"] .st-bx {{
  background: #0e1016 !important;
  border: 1px solid rgba(255,255,255,0.04) !important;
}}

/* =========================================================
   Inputs & controles (estética geral)
   =========================================================*/
.stSelectbox, .stMultiSelect, .stDateInput, .stRadio, .stSlider,
.stTextInput, .stNumberInput {{
  border-radius: 10px !important;
  background: #0f1218 !important;
  border: 1px solid var(--gold);
}}
/* Mais espaço entre label e caixa */
.stDateInput label, .stSelectbox label, .stMultiSelect label,
.stTextInput label, .stNumberInput label, .stRadio label {{
  margin-bottom: .35rem !important;
  margin-top: 0.3rem;
  margin-left: 0.5rem;
}}

/* =========================================================
   Tabs
   =========================================================*/
[data-baseweb="tab-list"] {{
  gap: .3rem;
  border-bottom: 1px solid var(--gold);
  padding-top: 4px;
}}
[data-baseweb="tab"] {{
  background: #0f1218;
  color: var(--text-soft);
  border: 1px solid var(--gold);
  border-bottom: none;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
  padding: 10px 18px;              /* respiro interno */
  min-height: 42px;                /* altura confortável */
  font-size: 0.95rem;
  font-weight: 600;
}}
[data-baseweb="tab"][aria-selected="true"] {{
  color: var(--text);
  background: linear-gradient(180deg, #12141c 0%, #0f1218 100%);
  border-color: rgba(212,175,55,0.55);
  box-shadow: inset 0 -3px 0 0 var(--gold);
}}

/* =========================================================
   Cards KPI & conversão
   =========================================================*/
[data-testid="stMetric"] {{
  background: #0e1016;
  border: 1px solid rgba(212,175,55,0.18);
  border-radius: 14px;
  padding: 10px 12px;
}}
[data-testid="stMetricValue"], [data-testid="stMetricDelta"] {{ color: var(--text) !important; }}

.conv-card {{
  padding: 0.7rem 0.9rem;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(28,28,28,0.98) 0%, rgba(18,18,18,0.98) 100%);
  border: 1px solid var(--gold-border);
  margin-bottom: 0.6rem;
  transition: transform 0.08s ease, box-shadow 0.08s ease;
}}
.conv-card:hover {{ transform: translateY(-1px); box-shadow: 0 6px 18px rgba(0,0,0,0.25); }}
.conv-flow {{ display:flex; align-items:center; gap:.45rem; font-size:.92rem; font-weight:600; color:var(--text); }}
.conv-flow .arrow {{ color: var(--gold); font-weight: 800; }}
.conv-value {{ margin-top:.15rem; font-size:1.5rem; font-weight:900; color:var(--gold); }}
.section-title {{ font-weight:700; font-size:1.0rem; margin:0 0 .6rem 0; color:var(--text); }}
.small {{ font-size:.85rem; color:#8e94a3; }}
.ok {{ color:#10b981; }} .warn{{ color:#f59e0b; }} .bad{{ color:#ef4444; }}
.pill {{ display:inline-block; padding:3px 8px; border-radius:999px; background:#131722; margin-right:6px; color:{TEXT_DIM}; border:1px solid rgba(255,255,255,0.06); }}

/* =========================================================
   Expanders
   =========================================================*/
.streamlit-expanderHeader {{
  background: #0f1218;
  border: 1px solid var(--gold);     /* dourado */
  border-radius: 10px;
  padding: 10px 12px;
}}

/* =========================================================
   DataFrame: zebra + header sticky
   =========================================================*/
[data-testid="stDataFrame"] {{
  background:#0f1117; border:1px solid rgba(255,255,255,0.06); border-radius:12px;
}}
[data-testid="stDataFrame"] .row-heading, [data-testid="stDataFrame"] .col_heading {{
  font-weight:700; color:var(--text);
}}
[data-testid="stDataFrame"] .blank {{ background:#0f1117 !important; }}
[data-testid="stDataFrame"] table tbody tr:nth-child(odd) {{ background: rgba(255,255,255,0.015); }}
[data-testid="stDataFrame"] table tbody tr:hover {{ background: rgba(212,175,55,0.05); }}
[data-testid="stDataFrame"] table thead th {{
  position: sticky; top: 0; z-index: 1;
  background: #12141c !important; border-bottom: 1px solid rgba(255,255,255,0.08) !important;
}}

/* =========================================================
   Scrollbar discreta
   =========================================================*/
*::-webkit-scrollbar {{ height: 10px; width: 10px; }}
*::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.12); border-radius: 10px; }}
*::-webkit-scrollbar-thumb:hover {{ background: rgba(212,175,55,0.35); }}

/* Legendas/captions */
.stCaption, .caption {{ color: var(--text-dim) !important; }}
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

STAGES_POS = ["Criado", "1º Contato", "Reunião Marcada", "Reunião Realizada", "Assinado"]
STAGES_TERMINAIS = ["Perdeu"]
STAGES_RAMO = ["No Show"]
ALL_STAGES = STAGES_POS + STAGES_TERMINAIS + STAGES_RAMO

stage_events = stage_events.copy()
stage_events["event_dt"] = pd.to_datetime(stage_events["event_dt"], errors="coerce")
stage_events["stage"] = stage_events["stage"].astype(str)

DIM_CANDIDATAS = ["origem", "sdr", "proprietario", "faixa_patrimonio", "tags", "times"]
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
                alc = [(s, r[c(s)]) for s in STAGES_POS if s != "Assinado" and c(s) in perdeu.columns and pd.notna(r.get(c(s)))]
                if not alc: continue
                last = max(alc, key=lambda x: x[1])[0]
                key = (idx[last], idx["Perdeu"])
                links[key] = links.get(key, 0) + 1
    pend = firsts.copy()
    ass_col, perdeu_col = c("Assinado"), c("Perdeu")
    if ass_col in pend.columns:
        pend = pend[pend[ass_col].isna()]
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

def signed_rate_por_dim(firsts: pd.DataFrame, dim: str) -> pd.DataFrame:
    def c(name): return f"dt_{name.lower().replace(' ', '_')}"
    if dim not in firsts.columns:
        return pd.DataFrame(columns=[dim, "criadas", "assinados", "signed_rate_%"])
    base = firsts.copy()
    base["_dim"] = base[dim].fillna("(sem)")
    criadas = base.groupby("_dim").size().rename("criadas")
    assinados = base[base[c("Assinado")].notna()].groupby("_dim").size().rename("assinados")
    out = pd.concat([criadas, assinados], axis=1).fillna(0)
    out["signed_rate_%"] = (out["assinados"] / out["criadas"] * 100).round(2)
    out = out.reset_index().rename(columns={"_dim": dim})
    return out.sort_values("criadas", ascending=False)

# =========================
# ------- CONTROLES -------
# =========================

st.markdown(
    """
    <div class="page-header pro">
      <div class="ph-icon">🎓</div>
      <div class="ph-title">Expert Wealth - Funil Comercial</div>
      <div class="ph-sub">Visão interna</div>
    </div>
    """,
    unsafe_allow_html=True
)

firsts_all = primeiras_datas_por_estagio(stage_events)
min_dt = pd.to_datetime(firsts_all.filter(like="dt_criado").stack().min()) if not firsts_all.empty else pd.Timestamp("2023-01-01")
max_dt = pd.to_datetime(firsts_all.filter(like="dt_criado").stack().max()) if not firsts_all.empty else pd.Timestamp.today()

with st.expander(label = "🕵️‍♀️ Filtros"):
    all_period = st.checkbox("Todos os leads (todo o período)", value=False, key="coorte_all_period")

    c0, c1 = st.columns([3,1])
    with c0:
        c02, c12 = st.columns(2)
        with c02:
            d_ini = st.date_input(
                "Data Início (Criação)",
                value=(max_dt - pd.Timedelta(days=30)).date(),
                min_value=min_dt.date(),
                max_value=max_dt.date(),
                disabled=all_period
            )
        with c12:
            d_fim = st.date_input(
                "Data Fim (Criação)",
                value=max_dt.date(),
                min_value=min_dt.date(),
                max_value=max_dt.date(),
                disabled=all_period
            )

    # Se o usuário escolher "todo o período", força limites globais
    if all_period:
        d_ini = min_dt.date()
        d_fim = max_dt.date()

#    with c1:
#        opt = st.radio("Horizonte de observação", ["Até hoje", "Até data específica", "Até X dias após criação"], horizontal=True)
#        if opt == "Até hoje":
#            horizonte = {"tipo":"hoje"}
#        elif opt == "Até data específica":
#            h_data = st.date_input("Observar eventos até", value=date.today())
#            horizonte = {"tipo":"data", "ate": h_data}
#        else:
#            h_dias = st.slider("Observar até X dias após criação", min_value=7, max_value=365, value=90, step=1)
#            horizonte = {"tipo":"dias_pos_criacao", "dias": h_dias}

    # --- Filtros (UI) ---
    cols_filters = st.columns(5)

    with cols_filters[0]:
        vals_origem = sorted(stage_events['origem'].dropna().astype(str).unique().tolist())
        sel_origem = st.multiselect("Filtrar origem", vals_origem, default=[], key="filtro_origem")

    with cols_filters[1]:
        vals_sdr = sorted(stage_events['sdr'].dropna().astype(str).unique().tolist())
        sel_sdr = st.multiselect("Filtrar SDR", vals_sdr, default=[], key="filtro_sdr")

    with cols_filters[2]:
        vals_prop = sorted(stage_events['proprietario'].dropna().astype(str).unique().tolist())
        sel_prop = st.multiselect("Filtrar proprietário", vals_prop, default=[], key="filtro_prop")

    with cols_filters[3]:
        vals_patrim = [
            'Menos de R$5 mil', 'Entre R$5 mil e R$20 mil', 'Entre R$20 mil e R$100 mil',
            'Entre R$100 mil e R$250 mil', 'Entre R$250 mil e R$500 mil',
            'Entre R$500 mil e R$1 milhão', 'Entre R$1 milhão e R$5 milhões',
            'Acima de R$5 milhões'
        ]
        sel_patrim = st.multiselect("Filtrar Patrimônio", vals_patrim, default=[], key="filtro_patrim")

    with cols_filters[4]:
        vals_times = sorted(stage_events['times'].dropna().astype(str).str.upper().unique().tolist())
        sel_times = st.multiselect("Filtrar Times", vals_times, default=[], key="filtro_times")

    # --- Aplicação dos filtros ---
    import pandas as pd

    mask = pd.Series(True, index=stage_events.index)

    if sel_origem:
        mask &= stage_events['origem'].astype(str).isin(sel_origem)

    if sel_sdr:
        mask &= stage_events['sdr'].astype(str).isin(sel_sdr)

    if sel_prop:
        mask &= stage_events['proprietario'].astype(str).isin(sel_prop)

    # ajuste o nome da coluna de patrimônio abaixo, se necessário:
    COL_PATRIM = next((c for c in ['patrimonio', 'patrimônio', 'faixa_patrimonio', 'patrimonio_faixa']
                    if c in stage_events.columns), None)
    if sel_patrim and COL_PATRIM:
        mask &= stage_events[COL_PATRIM].astype(str).isin(sel_patrim)

    # 'times' foi normalizado para MAIÚSCULO na seleção; compare em upper aqui também
    if sel_times:
        mask &= stage_events['times'].astype(str).str.upper().isin(sel_times)

    se_filtrado = stage_events[mask].copy()

    firsts = primeiras_datas_por_estagio(se_filtrado)
    firsts_coorte = filtrar_coorte(firsts, d_ini, d_fim)
    # se_coorte = aplicar_horizonte(se_filtrado, firsts_coorte.index, horizonte)

##############################################################################
##                           Velocimetros e Funil                           ##
##############################################################################

# Cálculos que devem ser mantidos
dias_selecionados = np.busday_count(d_ini, d_fim + timedelta(days=1))
mes_inicio = int(d_ini.strftime("%m"))
mes_fim = int(d_fim.strftime("%m"))

# Valores do funil
valores = {
    "Reuniões Marcadas": int(firsts_coorte.filter(like="dt_reunião_marcada").notna().any(axis=1).sum()),
    "Reuniões Realizadas": int(firsts_coorte.filter(like="dt_reunião_realizada").notna().any(axis=1).sum()),
    "Contratos Assinados": int(firsts_coorte.filter(like="dt_assinado").notna().any(axis=1).sum())
}

# Metas por dia por consultor
meta_con_rm = 2 * dias_selecionados
meta_con_rr = 0.7 * meta_con_rm
meta_con_ca = 0.5 * meta_con_rr

metas_consultor = {
    "Reuniões Marcadas": meta_con_rm,
    "Reuniões Realizadas": meta_con_rr,
    "Contratos Assinados": meta_con_ca
}

multiplicador_mes = mes_fim - mes_inicio + 1
n_consultores = len(firsts_coorte['proprietario'].dropna().unique()) 

# Meta acumulada = dias * meta_diária * número de consultores
metas_acumuladas = {
    etapa: valor_diario * n_consultores
    for etapa, valor_diario in metas_consultor.items()
}

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

    df_funil = dados_funil(firsts_coorte)

    # ordem "natural" das etapas (de cima para baixo, como vêm do df_funil)
    base_order = df_funil["estagio"].drop_duplicates().tolist()

    # KPI'S
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total = len(firsts_coorte)
    assinados = int(firsts_coorte.filter(like="dt_assinado").notna().any(axis=1).sum()) if total else 0
    perdidos = int(firsts_coorte.filter(like="dt_perdeu").notna().any(axis=1).sum()) if total else 0
    valor_total = float(firsts_coorte["valor"].fillna(0).sum()) if "valor" in firsts_coorte else 0.0

    # --- MÉTRICAS (mesma linha): 4 KPIs + 2 conversões (Consultor/SDR) no estilo .conv-card ---
    met = metricas_reunioes_sdr_vs_consultor(firsts_coorte, firsts_coorte)

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
    k1, k2, k3, k4 = st.columns([1,1,1,1])

    # KPIs antigos no novo visual
    render_card(k1, "Leads na coorte", f"{total:,}".replace(",", "."))
    render_card(k2, "Assinados", f"{assinados:,}".replace(",", "."))
    render_card(k3, "Perdidos", f"{perdidos:,}".replace(",", "."))
    render_card(k4, "Valor total (R$)", f"{valor_total:,.0f}".replace(",", "."))

    # ---- metas diárias por consultor (derivadas das suas metas do período) ----
    # Você já tem: metas_consultor = {...} com metas do PERÍODO por consultor
    metas_diarias_por_consultor = {
        etapa: (valor_periodo / max(dias_selecionados, 1))
        for etapa, valor_periodo in metas_consultor.items()
    }

    BAR_DOURADO  = "#d4af37"
    META_DOURADA = "#fbbf24"

    def _fmt_num(x):
        x = float(x)
        return f"{int(x):,}".replace(",", ".") if x.is_integer() else f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def gauge_meta_periodo(etapa: str,
                        realizado_total: float,
                        meta_periodo_equipe: float,
                        *,
                        height: int = 380,           # ↑ bem mais alto
                        domain_y=(0.02, 0.98),      # ↑ ocupa quase toda a área
                        title_size: int = 18,
                        number_size: int = 34,
                        delta_size: int = 12) -> go.Figure:

        realizado_total = float(realizado_total)
        meta_periodo_equipe = float(meta_periodo_equipe)

        # eixo ~20% acima do maior valor para não “cortar” o arco
        eixo_max = max(meta_periodo_equipe, realizado_total, 1.0) * 1.2

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=realizado_total,
            domain={"x": [0, 1], "y": list(domain_y)},
            number={"font": {"size": number_size}},
            delta={
                "reference": meta_periodo_equipe,
                "relative": False,
                "position": "top",
                "increasing": {"color": "#10b981"},
                "decreasing": {"color": "#ef4444"},
                "font": {"size": delta_size},
            },
            title={"text": f"<b>{etapa}</b>", "font": {"size": title_size}},
            gauge={
                "axis": {"range": [0, eixo_max],
                        "tickwidth": 1,
                        "tickcolor": "#94a3b8",
                        "tickfont": {"size": 12}},
                "bar": {"color": BAR_DOURADO},  # barra dourada
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 1,
                "bordercolor": "#1f2937",
                "steps": [
                    {"range": [0, 0.7 * meta_periodo_equipe], "color": "rgba(220,38,38,0.20)"},
                    {"range": [0.7 * meta_periodo_equipe, meta_periodo_equipe], "color": "rgba(234,179,8,0.20)"},
                    {"range": [meta_periodo_equipe, min(1.2 * meta_periodo_equipe, eixo_max)], "color": "rgba(16,185,129,0.20)"},
                ],
                "threshold": {
                    "line": {"color": META_DOURADA, "width": 4},
                    "thickness": 0.75,
                    "value": meta_periodo_equipe
                }
            }
        ))

        # legenda “Meta: X” no topo direito
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.99, y=0.99,
            text=f"<b>Meta:</b> {_fmt_num(meta_periodo_equipe)}",
            showarrow=False,
            font=dict(size=13, color=META_DOURADA),
            align="right",
            bgcolor="rgba(251,191,36,0.08)",
            bordercolor=META_DOURADA,
            borderwidth=1,
            borderpad=4
        )

        fig.update_layout(
            margin=dict(t=70, b=6, l=6, r=6),   # espaço pro título e topo
            height=height,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig


        # realizados totais
    rm_real = valores["Reuniões Marcadas"]
    rr_real = valores["Reuniões Realizadas"]
    ca_real = valores["Contratos Assinados"]

    # metas do período (dias * meta_diária * n_consultores)
    rm_meta = metas_acumuladas["Reuniões Marcadas"]
    rr_meta = metas_acumuladas["Reuniões Realizadas"]
    ca_meta = metas_acumuladas["Contratos Assinados"]

    # linha com 3 colunas, primeira mais larga
    col_big, col_small1, col_small2 = st.columns(3)

    with col_big:
        fig_rm = gauge_meta_periodo("Reuniões Marcadas", rm_real, rm_meta,
                                    height=250, domain_y=(0.00, 0.0),
                                    title_size=16, number_size=68)
        st.plotly_chart(fig_rm, use_container_width=True)

    with col_small1:
        fig_rr = gauge_meta_periodo("Reuniões Realizadas", rr_real, rr_meta,
                                    height=250, domain_y=(0.0, 0.0),
                                    title_size=16, number_size=68)
        st.plotly_chart(fig_rr, use_container_width=True)

    with col_small2:
        fig_ca = gauge_meta_periodo("Contratos Assinados", ca_real, ca_meta,
                                    height=250, domain_y=(0.0, 0.0),
                                    title_size=16, number_size=68)
        st.plotly_chart(fig_ca, use_container_width=True)

    # Conversões por origem da reunião (Consultor / SDR)
    def card_conv(col, rotulo):
        row = met[met["bucket"] == rotulo]
        if row.empty:
            render_card(col, f"{rotulo} → Assinado", "–", "Sem reuniões desse tipo no período/horizonte.")
            return
        r = row.iloc[0]
        conv = r["taxa_conversao_%"]
        total_b = int(r["deals_total"])
        signed_b = int(r["deals_signed"])
        lt = r.get("leadtime_mediano_dias", np.nan)
        lead_txt = f"Mediana: {lt:.1f} dias da reunião ao assinado" if pd.notna(lt) else "Mediana: —"
        render_card(col, f"{rotulo} → Assinado", f"{conv:.1f}%", lead_txt, pills=[f"Base: {total_b}", f"Assinados: {signed_b}"])
    vspace(10)
#    with st.expander(label="Conversões Consultor x SDR"):
#        k5, k6, k7 = st.columns([1,1,1])
#        card_conv(k5, "Consultor")
#        card_conv(k6, "SDR")


    # --- FILTRO DE ETAPAS (CHECKBOXES) + BLOCO DE "QUANTOS PRECISAMOS" ---
    cols_ws = st.columns([2, 3])

    # COLUNA ESQUERDA: seleção de etapas (igual à sua)
    with cols_ws[0]:
        with st.expander(label= 'Viz etapas do funil'):
            st.markdown("**Etapas do funil a exibir**")
            cb_cols = st.columns([1, 1, 1])
            selected_flags = {}
            for i, stage in enumerate(base_order):
                with cb_cols[i % 3]:
                    selected_flags[stage] = st.checkbox(stage, value=True, key=f"cb_{stage}")

            selected_stages = [s for s, v in selected_flags.items() if v]
            if len(selected_stages) == 0:
                st.info("Selecione ao menos uma etapa para visualizar o funil e as conversões.")
                st.stop()

            df_funil_sel = df_funil[df_funil["estagio"].isin(selected_stages)].copy()
            df_funil_sel["estagio"] = pd.Categorical(df_funil_sel["estagio"], categories=base_order, ordered=True)
            df_funil_sel = df_funil_sel.sort_values("estagio").reset_index(drop=True)

            # % conversão etapa atual / etapa anterior
            df_funil_sel["pct_conversao"] = df_funil_sel["count"] / df_funil_sel["count"].shift(1) * 100
            df_funil_sel.loc[0, "pct_conversao"] = 100

    # COLUNA DIREITA: "quantos precisamos para 1 avançar"
    with cols_ws[1]:
        with st.expander(label='Lembrete de esforço'):

            # Mapa transições -> necessidade (ex.: 12.5 quer dizer 'preciso de 12,5 do estágio anterior para 1 avançar')
            needs = []  # [(from, to, need_float), ...]
            df_seq = df_funil_sel.reset_index(drop=True)
            for i in range(1, len(df_seq)):
                from_stage = df_seq.loc[i - 1, "estagio"]
                to_stage   = df_seq.loc[i, "estagio"]
                pct        = float(df_seq.loc[i, "pct_conversao"])
                need_val   = (100.0 / pct) if pct > 0 else float("inf")
                needs.append((from_stage, to_stage, need_val))

            # Helper de formatação (prefere inteiro; senão, 1 casa)
            def fmt_need(x: float) -> str:
                if x == float("inf") or x <= 0 or pd.isna(x):
                    return "—"
                return f"{x:.0f}" if abs(x - round(x)) < 0.05 else f"{x:.1f}"

            # Renderização: primeiro, as 3 frases executivas (se as etapas existirem no recorte)
            frases = []
            mapa = {(f, t): v for f, t, v in needs}

            def add_if_exists(f, t, texto):
                val = mapa.get((f, t))
                if val is not None and np.isfinite(val) and val > 0:
                    frases.append(texto.replace("{N}", fmt_need(val)))
                else:
                    # só mostra se ambas etapas estiverem selecionadas; caso não, ignora silenciosamente
                    pass

            add_if_exists("1º Contato", "Reunião Marcada", "🗣️ Preciso falar com **{N} pessoas** para **marcar 1 reunião**.")
            add_if_exists("Reunião Marcada", "Reunião Realizada", "📅 Preciso **marcar {N} reuniões** para **realizar 1 reunião**.")
            add_if_exists("Reunião Realizada", "Assinado", "🤝 Preciso **realizar {N} reuniões** para **assinar 1 contrato**.")

            if frases:
                st.markdown("<br>".join(frases), unsafe_allow_html=True)

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
    col_leg = st.columns(3)
    etapas = ['dt_reunião_marcada', 'dt_reunião_realizada', 'dt_assinado']
    metas_dia = [2, 0.7, 0.5]

    # mapeia nomes bonitos por etapa (título, rótulos, etc.)
    LABELS = {
        'dt_reunião_marcada':   dict(nome='Reuniões Marcadas',   ytitle='Reuniões marcadas'),
        'dt_reunião_realizada': dict(nome='Reuniões Realizadas', ytitle='Reuniões realizadas'),
        'dt_assinado':          dict(nome='Contratos Assinados', ytitle='Contratos assinados'),
    }

    for col, (etapa, meta_individual) in zip(col_leg, zip(etapas, metas_dia)):
        with col:
            dias = pd.date_range(start=d_ini, end=d_fim, freq='B')
            meta_diaria_ajustada = meta_individual * n_consultores

            # normaliza a coluna de data da etapa para date (sem hora)
            serie_datas = pd.to_datetime(firsts_coorte[etapa], errors='coerce').dt.date

            # contagem por dia (robusto)
            counts = (
                firsts_coorte.assign(__dia=serie_datas)
                .groupby('__dia', dropna=False)
                .size()                                   # conta linhas por dia
                .reindex(dias.date, fill_value=0)         # garante todos os dias úteis
            )

            df_dia = counts.rename_axis('DATA').reset_index(name='REALIZADO')

            # rótulos dd/mm
            df_dia["LABEL"] = pd.to_datetime(df_dia["DATA"]).dt.strftime("%d/%m")

            fig = go.Figure()

            # Barras
            fig.add_trace(go.Bar(
                x=df_dia["LABEL"],
                y=df_dia["REALIZADO"],
                name=LABELS[etapa]["nome"],
                marker=dict(
                    color=df_dia["REALIZADO"],
                    colorscale=[[0, "#d4af37"], [0.5, "#d4af37"], [1, "#d4af37"]],
                    showscale=False,
                    line=dict(color='#1f2937', width=1)
                ),
                text=df_dia["REALIZADO"],
                textposition="outside",
                textfont=dict(color='#f8fafc'),
                hovertemplate=f"<b>%{{x}}</b><br>{LABELS[etapa]['nome']}: %{{y}}<extra></extra>"
            ))

            # Linha da meta (pontilhada amarela, se preferir troque a cor)
            fig.add_trace(go.Scatter(
                x=df_dia["LABEL"],
                y=[meta_diaria_ajustada] * len(df_dia),
                mode="lines",
                name="Meta Diária",
                line=dict(color="#fbbf24", dash="dash", width=3),
                hovertemplate=f"<b>Meta: {meta_diaria_ajustada}</b><extra></extra>"
            ))

            fig.update_layout(
                title=dict(
                    text=f"<b>{LABELS[etapa]['nome']} por Dia vs Meta</b>",  # <- título por etapa
                    font=dict(size=16, color="#f8fafc", family="Inter"),
                    x=0.5
                ),
                xaxis=dict(
                    title=dict(text="Data (dias úteis)", font=dict(color='#f8fafc')),
                    tickfont=dict(color='#94a3b8')
                ),
                yaxis=dict(
                    title=dict(text=LABELS[etapa]['ytitle'], font=dict(color='#f8fafc')),
                    tickfont=dict(color='#94a3b8'),
                    range=[0, max(df_dia["REALIZADO"].max(), meta_diaria_ajustada) * 1.15]
                ),
                barmode='group',
                hovermode="x unified",
                showlegend=False,
                margin=dict(t=50, b=20, l=20, r=20),
                height=240,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )

            # Anotação da meta
            fig.add_annotation(
                xref="paper", yref="y",
                x=0.99, y=meta_diaria_ajustada,
                text=f"Meta: {meta_diaria_ajustada}",
                showarrow=False,
                font=dict(size=12, color="#fbbf24", family="Inter"),
                bgcolor="rgba(251,191,36,0.08)",
                bordercolor="#fbbf24",
                borderwidth=1,
                borderpad=5
            )
            fig.update_layout(height=380)
            st.plotly_chart(fig, use_container_width=True)


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
            "#1f77b4",   # Criado
            "#2ca02c",   # 1º Contato
            "#9467bd",   # Reunião Marcada
            "#17becf",   # Reunião Realizada
            GOLD,        # Assinado (dourado destaque)
            "#e74c3c",   # Perdeu
            "#f39c12",   # No Show
            "#7f8c8d"    # Pendente
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
        # Paleta diferenciada (alta distinção + Assinado em dourado)
        color_map = {
            "Criado": "#1f77b4",
            "1º Contato": "#2ca02c",
            "Reunião Marcada": "#9467bd",
            "Reunião Realizada": "#17becf",
            "Assinado": GOLD
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
        wr = signed_rate_por_dim(firsts_coorte, dim)
        c1, c2 = st.columns([2,1])
        with c1:
            figd = px.bar(wr, x=dim, y="signed_rate_%", hover_data=["criadas","assinados"], color_discrete_sequence=[GOLD])
            figd.update_traces(marker_line_width=0)
            figd.update_layout(yaxis_title="Win rate (%)", xaxis_title=dim, height=420)
            apply_plotly_theme(figd)
            st.plotly_chart(figd, use_container_width=True)
        with c2:
            st.dataframe(wr.head(20), use_container_width=True)
        st.caption("Signed rate = #Assinado / #Criado por categoria selecionada na coorte.")

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

st.dataframe(firsts_coorte, use_container_width=True)
