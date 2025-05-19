import json 
import requests # type: ignore
import os
import datetime
from datetime import date, timedelta, datetime
import pandas as pd # type: ignore
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

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

    if planilhas_com_erro:
        st.error("Erro ao carregar as seguintes planilhas:")
        for erro in planilhas_com_erro:
            st.error(erro)
    else:
        st.success("Planilhas carregadas com sucesso!")
