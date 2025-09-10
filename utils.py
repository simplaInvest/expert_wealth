# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import math
import unicodedata
from typing import Dict, Iterable, List, Optional, Tuple
import streamlit as st

import numpy as np
import pandas as pd


def formatar_data_base(
    df_raw: pd.DataFrame,
    *,
    timezone: str = "America/Sao_Paulo",
    referencia_hj: Optional[pd.Timestamp] = None,
    mapa_etapas_nativas: Optional[Dict[str, str]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    FormataçãoDataFrames
    --------------------
    Padroniza e enriquece um DataFrame exportado do CRM para alimentar um funil comercial.

    ENTRADA
    -------
    df_raw : pd.DataFrame
        Export do CRM (qualquer nome/ordem de colunas).
    timezone : str
        Timezone de referência para parsing de datas (apenas informativo; datas permanecem "naive" no tz local).
    referencia_hj : pd.Timestamp | None
        "Hoje" usado para calcular idade de negócios abertos. Se None, usa agora().
    mapa_etapas_nativas : dict[str, str] | None
        (Opcional) Mapeia nomes de etapas nativas -> estágios canônicos do funil,
        caso você queira reaproveitar 'etapa_atual' do CRM em análises. Ex.:
        {
          "cadencia 1": "Contato/Cadência",
          "agendados": "Reunião Marcada",
          "follow up - pós reunião": "Pós-reunião",
          "aguardando custódia": "Pós-assinado",
        }

    SAÍDA
    -----
    deals_master : pd.DataFrame
        1 linha por deal_key com colunas canônicas, tipos e métricas derivadas.
    stage_events : pd.DataFrame
        Formato longo: uma linha por evento de estágio (Criado, 1º Contato, etc.).

    COLUNAS CANÔNICAS (deals_master)
    ---------------------------------
    Identificação:
        deal_key, opportunity_id, contact_id
    Dimensões:
        nome, email, telefone, origem, sdr, proprietario, tags,
        faixa_patrimonio, aporte_mensal (texto), aporte_mensal_mid (float)
    Valores:
        valor (float em R$)
    Marcos/estágios (datetime):
        criado_em, primeiro_contato_em, reuniao_marcada_em, reuniao_realizada_em,
        no_show_em, assinado_em, ganhou_em, perdeu_em, movimentado_em
        reuniao_marcada_flag (bool)
    Derivados:
        status (open|won|lost), estagio_atual_canonical, idade_dias, data_quality_flag

    NOTAS
    -----
    - Parsing de datas é tolerante a formatos brasileiros (dd/mm/aaaa), ISO e *seriais de Excel*.
    - Campos monetários aceitam "R$ 1.234,56" e variações.
    - Se houver linhas duplicadas por oportunidade/contato, consolidamos marcos (min data) e última movimentação (max).
    - 'No Show' é registrado como evento, útil para drop-off entre Marcada→Realizada.
    """

    # =========================
    # Helpers de normalização
    # =========================
    def _strip_bom(s: str) -> str:
        return s.replace("\ufeff", "") if isinstance(s, str) else s

    def _unaccent(txt: str) -> str:
        return "".join(
            c for c in unicodedata.normalize("NFKD", txt) if not unicodedata.combining(c)
        )

    def _normalize_colname(c: str) -> str:
        c = _strip_bom(str(c)).strip()
        c = _unaccent(c).lower()
        c = re.sub(r"[^\w]+", "_", c)  # espaços e pontuação -> _
        c = re.sub(r"_+", "_", c).strip("_")
        return c

    def _first_existing(cols_norm: Dict[str, str], candidates: Iterable[str]) -> Optional[str]:
        """Retorna o NOME NORMALIZADO da primeira coluna existente dentre os candidatos."""
        for cand in candidates:
            if cand in cols_norm:
                return cand
        return None

    # -------------------------
    # Copia e normaliza header
    # -------------------------
    df = df_raw.copy()
    original_cols = list(df.columns)
    norm_cols = [_normalize_colname(c) for c in df.columns]

    # se houver conflitos após normalização, preserva a PRIMEIRA ocorrência
    norm_to_original: Dict[str, str] = {}
    for raw, norm in zip(original_cols, norm_cols):
        norm_to_original.setdefault(norm, raw)

    df.columns = [ _normalize_colname(c) for c in df.columns ]

    # -------------------------
    # Mapa de sinônimos
    # -------------------------
    synonyms: Dict[str, List[str]] = {
        # identificação
        "opportunity_id": ["opportunity_id", "oportunidade_id", "id_oportunidade", "deal_id"],
        "contact_id": ["contact_id", "contato_id", "id_contato", "lead_id"],
        "nome": ["nome", "contato", "pessoa", "lead", "lead_name"],
        "email": ["email", "e_mail"],
        "telefone": ["telefone", "celular", "whatsapp", "fone", "telefone_whatsapp"],
        # dimensões
        "origem": ["origem", "source", "fonte", "utm_source"],
        "tags": ["tags", "tag"],
        "sdr": ["sdr", "bdr", "pre_vendas", "pre_vendas_sdr"],
        "proprietario": ["proprietario", "owner", "responsavel", "vendedor", "executivo"],
        "faixa_patrimonio": ["faixa_patrimonio", "faixa_de_patrimonio", "patrimonio_faixa"],
        "aporte_mensal": ["aporte_mensal", "aporte", "aporte_mensal_faixa", "aporte mensal"],
        # valores
        "valor": ["valor", "amount", "valor_da_oportunidade", "valor_do_negocio", "deal_amount"],
        # etapas / marcos
        "criado_em": ["criado_em", "criado", "data_criacao", "created_at", "criado_em_"],
        "primeiro_contato_em": ["primeiro_contato_em", "1_contato", "1_contato_em", "primeiro_contato", "contato_inicial_em"],
        "cadencia_em": ["cadencia_em", "cadencia", "cadencia_data", "cadencia_rodada_em"],
        "reuniao_marcada_em": ["reuniao_marcada_em", "marcado_em", "reuniao_agendada_em", "agendado_em"],
        "reuniao_realizada_em": ["reuniao_realizada_em", "realizada_em", "reuniao_feita_em"],
        "no_show_em": ["no_show_em", "no_show", "nao_compareceu_em"],
        "assinado_em": ["assinado_em", "contrato_assinado_em", "assinatura_em", "contrato_enviado_em"],
        "ganhou_em": ["ganhou_em", "won_date", "fechado_ganho_em", "closed_won_em"],
        "perdeu_em": ["perdeu_em", "lost_date", "fechado_perdido_em", "closed_lost_em", "perdeu_em_"],
        "movimentado_em": ["movimentado_em", "updated_at", "atualizado_em", "ultima_movimentacao_em"],
        "etapa_atual": ["etapa_atual", "etapa", "stage", "fase"],
        "reuniao_marcada_flag": ["reuniao_marcada_", "reuniao_marcada_flag", "tem_reuniao_marcada", "reuniao_marcada"],
        # qualidade
        "motivo_perda": ["motivo_perda", "motivo_de_perdeu", "lost_reason", "motivo_perdeu"],
    }

    # =========================
    # Parsing e tipagem
    # =========================
    def _to_bool(x) -> Optional[bool]:
        if pd.isna(x):
            return np.nan
        s = str(x).strip().lower()
        if s in {"sim", "yes", "y", "true", "1"}:
            return True
        if s in {"nao", "não", "no", "n", "false", "0"}:
            return False
        return np.nan  # desconhecido

    def _parse_money(x) -> float:
        if pd.isna(x):
            return np.nan
        s = str(x)
        # remove R$, espaços, NBSP e sinais
        s = s.replace("R$", "").replace("\xa0", " ").strip()
        # se vier algo como "Entre R$5.000 e R$15.000", não é monetário simples
        if re.search(r"\d+\D+\d+", s):
            # mais de um número -> tratar fora (ex.: aporte faixa)
            try:
                # fallback: pega o último número como valor
                nums = re.findall(r"[\d\.\,]+", s)
                s = nums[-1]
            except Exception:
                return np.nan
        s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except Exception:
            return np.nan

    def _parse_aporte_mid(s: Optional[str]) -> float:
        """Extrai ponto médio de faixas textuais (ex.: 'Entre R$5.000 e R$15.000' -> 10000.0)."""
        if not isinstance(s, str):
            return np.nan
        nums = re.findall(r"[\d\.\,]+", s)
        vals = []
        for n in nums:
            try:
                vals.append(float(n.replace(".", "").replace(",", ".")))
            except Exception:
                pass
        if len(vals) >= 2:
            return float(np.mean([vals[0], vals[1]]))
        if len(vals) == 1:
            return float(vals[0])
        return np.nan

    def _parse_datetime_value(x) -> pd.Timestamp:
        """Tenta várias formas: dd/mm/aaaa hh:mm[:ss], ISO, e seriado de Excel (inclusive decimal com fração do dia)."""
        if pd.isna(x):
            return pd.NaT
        # já datetime?
        if isinstance(x, pd.Timestamp):
            return x
        s = str(x).strip()
        if s == "":
            return pd.NaT

        # Números/seriais de Excel (aceita '45797,684' etc.)
        s_num = s.replace(",", ".")
        try:
            f = float(s_num)
            # Excel 1900 system: origin 1899-12-30
            return pd.to_datetime(f, unit="D", origin="1899-12-30", errors="coerce")
        except Exception:
            pass

        # Formatos comuns com dayfirst
        dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
        if pd.isna(dt):
            # tentativa final sem dayfirst
            dt = pd.to_datetime(s, dayfirst=False, errors="coerce")
        return dt

    def _parse_datetime_series(ser: pd.Series) -> pd.Series:
        return ser.apply(_parse_datetime_value)

    # =========================
    # Seleção de colunas alvo
    # =========================
    def pick(name: str) -> Optional[str]:
        """Retorna o nome NORMALIZADO da coluna selecionada para 'name' canônico."""
        return _first_existing(df.columns.to_series().to_dict(), synonyms.get(name, []))

    cols = {k: pick(k) for k in synonyms.keys()}

    # =========================
    # Construção do deals_master
    # =========================
    out = pd.DataFrame(index=df.index)

    # IDs preferenciais
    if cols["opportunity_id"] in df:
        out["opportunity_id"] = df[cols["opportunity_id"]].astype(str).str.strip()
    else:
        out["opportunity_id"] = np.nan

    if cols["contact_id"] in df:
        out["contact_id"] = df[cols["contact_id"]].astype(str).str.strip()
    else:
        out["contact_id"] = np.nan

    # deal_key (preferência: opportunity_id -> contact_id -> índice)
    deal_key = out["opportunity_id"].where(out["opportunity_id"].notna() & (out["opportunity_id"].str.len() > 0), out["contact_id"])
    deal_key = deal_key.where(deal_key.notna() & (deal_key.str.len() > 0), df.index.astype(str))
    out["deal_key"] = deal_key

    # Dimensões básicas
    for tgt in ["nome", "email", "telefone", "origem", "tags", "sdr", "proprietario", "faixa_patrimonio", "aporte_mensal", "etapa_atual", "motivo_perda"]:
        col = cols.get(tgt)
        out[tgt] = df[col] if col in df else np.nan
        if tgt in {"origem", "tags", "sdr", "proprietario", "faixa_patrimonio", "etapa_atual", "motivo_perda"}:
            out[tgt] = out[tgt].astype(str).str.strip().str.lower().replace({"nan": np.nan, "": np.nan})

    # Valor (R$)
    out["valor"] = np.nan
    if cols["valor"] in df:
        out["valor"] = df[cols["valor"]].apply(_parse_money)

    # Aporte mensal (texto -> ponto médio numérico auxiliar)
    out["aporte_mensal_mid"] = out["aporte_mensal"].apply(_parse_aporte_mid)

    # Flags/booleans
    out["reuniao_marcada_flag"] = np.nan
    if cols["reuniao_marcada_flag"] in df:
        out["reuniao_marcada_flag"] = df[cols["reuniao_marcada_flag"]].apply(_to_bool)

    # Datas dos marcos
    date_targets = [
        "criado_em",
        "primeiro_contato_em",
        "cadencia_em",
        "reuniao_marcada_em",
        "reuniao_realizada_em",
        "no_show_em",
        "assinado_em",
        "ganhou_em",
        "perdeu_em",
        "movimentado_em",
    ]
    for tgt in date_targets:
        col = cols.get(tgt)
        if col in df:
            out[tgt] = _parse_datetime_series(df[col])
        else:
            out[tgt] = pd.NaT

    # Alguns CRMs misturam textos/URLs em "cadencia_em": mantemos apenas valores que viram data
    # (já garantido pelo parser; strings não-datas viram NaT)

    # -------------------------
    # Consolidação por deal_key
    # -------------------------
    # Se houver duplicidade por deal_key, consolidar:
    # - marcos: pegar a MENOR data (primeira ocorrência do marco)
    # - movimentado_em: MAIOR data
    # - dimensões: primeira não-nula
    agg_rules = {
        "opportunity_id": "first",
        "contact_id": "first",
        "nome": "first",
        "email": "first",
        "telefone": "first",
        "origem": "first",
        "tags": "first",
        "sdr": "first",
        "proprietario": "first",
        "faixa_patrimonio": "first",
        "aporte_mensal": "first",
        "aporte_mensal_mid": "first",
        "valor": "max",  # valor pode variar; mantemos o MAIOR (ou poderia ser 'first')
        "reuniao_marcada_flag": "max",  # True>False
        "etapa_atual": "first",
        "motivo_perda": "first",
        # datas (min = primeira vez que atingiu o marco)
        "criado_em": "min",
        "primeiro_contato_em": "min",
        "cadencia_em": "min",
        "reuniao_marcada_em": "min",
        "reuniao_realizada_em": "min",
        "no_show_em": "min",
        "assinado_em": "min",
        "ganhou_em": "min",
        "perdeu_em": "min",
        "movimentado_em": "max",
    }

    deals_master = (
        out.groupby("deal_key", as_index=False)
        .agg(agg_rules)
        .reset_index(drop=True)
    )

    # -------------------------
    # Derivados: status, estágio atual, idade, flags de qualidade
    # -------------------------
    won = deals_master["ganhou_em"].notna()
    lost = deals_master["perdeu_em"].notna()
    deals_master["status"] = np.where(won, "won", np.where(lost, "lost", "open"))

    # estágio atual canônico (para abertos): último marco não-nulo
    def _estagio_atual(row) -> str:
        if row["status"] == "won":
            return "Closed Won"
        if row["status"] == "lost":
            return "Closed Lost"
        order = [
            ("reuniao_realizada_em", "Reunião Realizada"),
            ("reuniao_marcada_em", "Reunião Marcada"),
            ("primeiro_contato_em", "1º Contato"),
            ("criado_em", "Criado"),
        ]
        for col, nome in order:
            if pd.notna(row[col]):
                return nome
        return "Indefinido"

    deals_master["estagio_atual_canonical"] = deals_master.apply(_estagio_atual, axis=1)

    # idade em dias (desde último evento conhecido)
    if referencia_hj is None:
        referencia_hj = pd.Timestamp.now()
    last_touch = deals_master[
        [
            "criado_em",
            "primeiro_contato_em",
            "reuniao_marcada_em",
            "reuniao_realizada_em",
            "assinado_em",
            "ganhou_em",
            "perdeu_em",
            "movimentado_em",
        ]
    ].max(axis=1, skipna=True)
    deals_master["idade_dias"] = (referencia_hj.normalize() - last_touch.fillna(referencia_hj).dt.normalize()).dt.days.clip(lower=0)

    # flags de qualidade
    dq_conflict = won & lost
    # inversões temporais: algum marco posterior com data < anterior
    def _has_inversion(row) -> bool:
        seq = [
            row.get("criado_em"),
            row.get("primeiro_contato_em"),
            row.get("reuniao_marcada_em"),
            row.get("reuniao_realizada_em"),
            row.get("assinado_em"),
            row.get("ganhou_em") if row.get("ganhou_em") is not pd.NaT else row.get("perdeu_em"),
        ]
        seq = [d for d in seq if pd.notna(d)]
        return any(seq[i] > seq[i + 1] for i in range(len(seq) - 1))

    dq_inversion = deals_master.apply(_has_inversion, axis=1)
    deals_master["data_quality_flag"] = np.where(dq_conflict | dq_inversion, True, False)

    # Mapeamento opcional de etapa nativa -> canônica (informativo)
    if mapa_etapas_nativas:
        def _map_stage(s: Optional[str]) -> Optional[str]:
            if not isinstance(s, str):
                return np.nan
            key = s.strip().lower()
            return mapa_etapas_nativas.get(key, np.nan)
        deals_master["etapa_nativa_mapeada"] = deals_master["etapa_atual"].apply(_map_stage)

    # Ordena colunas de saída
    col_order = [
        # ids
        "deal_key", "opportunity_id", "contact_id",
        # dimensões
        "nome", "email", "telefone", "origem", "tags", "sdr", "proprietario",
        "faixa_patrimonio", "aporte_mensal", "aporte_mensal_mid",
        # valores
        "valor",
        # marcos
        "criado_em", "primeiro_contato_em", "cadencia_em",
        "reuniao_marcada_em", "reuniao_realizada_em", "no_show_em",
        "assinado_em", "ganhou_em", "perdeu_em", "movimentado_em",
        "reuniao_marcada_flag",
        # derivados
        "status", "estagio_atual_canonical", "idade_dias", "data_quality_flag",
        "etapa_atual",
    ]
    if "etapa_nativa_mapeada" in deals_master:
        col_order.append("etapa_nativa_mapeada")

    # garante existência das colunas no order
    col_order = [c for c in col_order if c in deals_master.columns]
    deals_master = deals_master[col_order].copy()

    # =========================
    # Tabela de eventos (longo)
    # =========================
    stage_map = [
        ("Criado", "criado_em"),
        ("1º Contato", "primeiro_contato_em"),
        ("Reunião Marcada", "reuniao_marcada_em"),
        ("Reunião Realizada", "reuniao_realizada_em"),
        ("No Show", "no_show_em"),
        ("Assinado", "assinado_em"),
        ("Ganhou", "ganhou_em"),
        ("Perdeu", "perdeu_em"),
    ]

    events_rows = []
    dim_cols = ["valor", "origem", "sdr", "proprietario", "faixa_patrimonio", "aporte_mensal", "aporte_mensal_mid", "tags"]
    for _, row in deals_master.iterrows():
        for stage_name, col_dt in stage_map:
            dt = row.get(col_dt)
            if pd.notna(dt):
                ev = {
                    "deal_key": row["deal_key"],
                    "stage": stage_name,
                    "event_dt": dt,
                }
                for d in dim_cols:
                    ev[d] = row.get(d, np.nan)
                events_rows.append(ev)

    stage_events = pd.DataFrame(events_rows)
    if not stage_events.empty:
        # ordena cronologicamente por deal
        stage_events = stage_events.sort_values(by=["deal_key", "event_dt"], kind="mergesort").reset_index(drop=True)
    
    st.session_state['stage_events'] = stage_events
    st.session_state['deals_master'] = deals_master

    return st.session_state['deals_master'], st.session_state['stage_events']

def vspace(px: int = 16):
    """Espaço em branco vertical (px)."""
    st.markdown(f"<div style='height:{px}px'></div>", unsafe_allow_html=True)

def metricas_reunioes_sdr_vs_consultor(se_coorte: pd.DataFrame, firsts_coorte: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula conversão e lead time (mediana de dias) para reuniões marcadas por SDR (tag 'reuniao-sdr')
    versus reuniões marcadas por Consultor (sem a tag), considerando a primeira 'Reunião Marcada'
    de cada deal dentro do horizonte aplicado (se_coorte).

    Retorna um DF com colunas:
    ['bucket', 'deals_total', 'deals_won', 'taxa_conversao_%', 'leadtime_mediano_dias']
    """
    if "stage" not in se_coorte.columns or "deal_key" not in se_coorte.columns:
        return pd.DataFrame(columns=["bucket","deals_total","deals_won","taxa_conversao_%","leadtime_mediano_dias"])

    # Normaliza tags
    tags_col = "tags" if "tags" in se_coorte.columns else None
    se = se_coorte.copy()
    if tags_col:
        se["_tags_norm"] = se[tags_col].astype(str).str.lower()
    else:
        se["_tags_norm"] = ""

    # Somente eventos de "Reunião Marcada"
    meet = se[se["stage"].astype(str).str.lower() == "reunião marcada"].copy()
    if meet.empty:
        return pd.DataFrame(columns=["bucket","deals_total","deals_won","taxa_conversao_%","leadtime_mediano_dias"])

    meet = meet.sort_values("event_dt")
    # Primeiro agendamento por deal
    first_meet = (
        meet.loc[meet.groupby("deal_key")["event_dt"].idxmin(), ["deal_key", "event_dt", "_tags_norm"]]
        .rename(columns={"event_dt": "meeting_dt"})
        .reset_index(drop=True)
    )

    # Bucket: SDR se tem 'reuniao-sdr' na primeira reunião, senão Consultor
    first_meet["bucket"] = np.where(first_meet["_tags_norm"].str.contains("reuniao-sdr", na=False), "SDR", "Consultor")

    # Junta com Ganhou (primeira data de ganho)
    ganhou_col = [c for c in firsts_coorte.columns if c.startswith("dt_ganhou")]
    win_col = ganhou_col[0] if ganhou_col else None
    if win_col is None:
        first_meet["won_after_meeting"] = False
    else:
        base = firsts_coorte[[win_col]].rename(columns={win_col: "first_win_dt"})
        first_meet = first_meet.merge(base, left_on="deal_key", right_index=True, how="left")
        first_meet["won_after_meeting"] = (
            first_meet["first_win_dt"].notna() &
            (first_meet["first_win_dt"] >= first_meet["meeting_dt"])
        )

    # KPIs por bucket
    out = (
        first_meet.groupby("bucket")
        .agg(
            deals_total=("deal_key", "nunique"),
            deals_won=("won_after_meeting", "sum"),
        )
        .reset_index()
    )
    out["taxa_conversao_%"] = (out["deals_won"] / out["deals_total"] * 100).round(2)

    # Lead time mediano (dias) para quem ganhou
    won_rows = first_meet[first_meet["won_after_meeting"]].copy()
    if not won_rows.empty and "first_win_dt" in won_rows.columns:
        won_rows["leadtime_dias"] = (won_rows["first_win_dt"] - won_rows["meeting_dt"]).dt.total_seconds() / 86400.0
        lt = won_rows.groupby("bucket")["leadtime_dias"].median().round(1).reset_index()
        out = out.merge(lt.rename(columns={"leadtime_dias": "leadtime_mediano_dias"}), on="bucket", how="left")
    else:
        out["leadtime_mediano_dias"] = np.nan

    # Ordenar como Consultor, SDR
    cat = pd.Categorical(out["bucket"], categories=["Consultor", "SDR"], ordered=True)
    out = out.assign(bucket=cat).sort_values("bucket").reset_index(drop=True)
    return out
