import json 
import requests # type: ignore
import os
import datetime
from datetime import date, timedelta, datetime
import pandas as pd # type: ignore
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

def load_calls(start_date, end_date):
    # API  
    api_hostname = 'mybilling.fvx.com.br:8444' 
    api_user = 'gustavo.andrade@simplawealth.com'
    password = '$impl@123'
    api_base = 'https://%s/rest/' % api_hostname 
    # for self-signed certificates - remove before going  live 
    requests.packages.urllib3.disable_warnings() 

    # login 
    req_data = { 'params': json.dumps({'login': api_user, 'password':password})} 
    print(req_data)
    r = requests.post(api_base + 'Session/login', data=req_data, verify=False) 
    data = r.json() 
    session_id = data['session_id']

    # INFO: SET DATE/TIME
    info = {'from_date': str(start_date) ,'to_date': str(end_date), 'show_unsuccessful' : '1'}

    # GET XDRS
    req_data = { 'auth_info': json.dumps({'session_id': session_id}), 'params': json.dumps(info) } 
    r = requests.post(api_base + 'Customer/get_customer_xdrs', data=req_data, verify=False) 
    data = r.json()      

    # Verificar se a resposta contém a lista xdr_list
    if 'xdr_list' in data and data['xdr_list']:
        # Criar DataFrame com os dados
        df = pd.DataFrame(data['xdr_list'])
    else:
        # Retorna um DataFrame vazio se não houver dados
        df = pd.DataFrame()
        
    return df
    
def format_data(df):
    # Transformando em datetime
    df['connect_time'] = pd.to_datetime(df['connect_time'], format='%Y-%m-%d %H:%M:%S')
    df['disconnect_time'] = pd.to_datetime(df['disconnect_time'], format='%Y-%m-%d %H:%M:%S')

    df['connect_time'] = df['connect_time'] - pd.Timedelta(hours=3)
    df['disconnect_time'] = df['disconnect_time'] - pd.Timedelta(hours=3)

    df['call_time'] = df['disconnect_time'] - df['connect_time']

    # Padronizando as informações dos nossos números
    col_to_filter = [
        '3231420312', '1002 (3231420312 - Daniel)',
        '3231420313', '1004 (3231420313 - Toledo)',
        '3231420314', '1006 (3231420314 - Pedro Vieira)',
        '3231420315', '1008 (3231420315 - Saint Clair)',
        '3231420316', '1010 (3231420316 - Rúbio)',
        '3231420310', '1012 (3231420310 - Marioti)',
        '3231420317', '1014 (3231420317 - Gustavo B)',
        '3231420319', '1015 (3231420319 - Gabriel)',
        '3231420380', '1018 (3231420380 - Micaelli)',
        '3231420381', '1021 (3231420381 - Felipe Altmann)',
        '3231420382', '1023 (3231420382 - Rafael Sanchez)',
        '3231420383', '1025 (3231420383 - Tiago)',
        '3231420112', '2014 (3231420112 - Douglas Santos)',
        '3231420113', '2015 (3231420113 - Marlon Mendes)',
        '3231420318', '2016 (3231420318 - Victor Corrêa)',
        '3231420384', '2017 (3231420384 - Paula Leitão)',
        '3231420386', '2018 (3231420386 - Débora Bordonal)',
        '3231420387', '2020 (3231420387 - Victor Hugo)',
        '3231420388', '2021 (3231420388 - Bruno Veiga)',
        '3231420389', '2022 (3231420389 - Matheus Ferreira)',
        '3231420106', '2023 (3231420106 - Melissa)',
        '3231420114', '2024 (3231420114 - Gabriel Soares)',
        '3231420311', '2025 (3231420311 - Alexander Neto)',
        '3231420160', '2026 (3231420160 - Leonnardo Gomes)',
        '3231420161', '2027 (3231420161 - Mateus Lage)',
        '3231420162', '2028 (3231420162 - Gustavo Nogueira)',
        '3231420163', '2029 (3231420163 - Emily Rocha)'
    ]

    df = df.loc[df['CLI'].isin(col_to_filter)]


    substituicoes = {
        '3231420312': '1002 (3231420312 - Daniel)',
        '3231420313': '1004 (3231420313 - Toledo)',
        '3231420314': '1006 (3231420314 - Pedro Vieira)',
        '3231420315': '1008 (3231420315 - Saint Clair)',
        '3231420316': '1010 (3231420316 - Rúbio)',
        '3231420310': '1012 (3231420310 - Marioti)',
        '3231420317': '1014 (3231420317 - Gustavo B)',
        '3231420319': '1015 (3231420319 - Gabriel)',
        '3231420380': '1018 (3231420380 - Micaelli)',
        '3231420381': '1021 (3231420381 - Felipe Altmann)',
        '3231420382': '1023 (3231420382 - Rafael Sanchez)',
        '3231420383': '1025 (3231420383 - Tiago)',
        '3231420112': '2014 (3231420112 - Douglas Santos)',
        '3231420113': '2015 (3231420113 - Marlon Mendes)',
        '3231420318': '2016 (3231420318 - Victor Corrêa)',
        '3231420384': '2017 (3231420384 - Paula Leitão)',
        '3231420386': '2018 (3231420386 - Débora Bordonal)',
        '3231420387': '2020 (3231420387 - Victor Hugo)',
        '3231420388': '2021 (3231420388 - Bruno Veiga)',
        '3231420389': '2022 (3231420389 - Matheus Ferreira)',
        '3231420106': '2023 (3231420106 - Melissa)',
        '3231420114': '2024 (3231420114 - Gabriel Soares)',
        '3231420311': '2025 (3231420311 - Alexander Neto)',
        '3231420160': '2026 (3231420160 - Leonnardo Gomes)',
        '3231420161': '2027 (3231420161 - Mateus Lage)',
        '3231420162': '2028 (3231420162 - Gustavo Nogueira)',
        '3231420163': '2029 (3231420163 - Emily Rocha)'
    }

    df['CLI'] = df['CLI'].replace(substituicoes)


    return df

def get_last_30_days_data():
    # Data e hora de amanhã
    end_date = datetime.now() + timedelta(days=1)
    
    # Data de 31 dias antes de amanhã
    start_date = end_date - timedelta(days=31)
    
    # Chamar a função com as datas formatadas
    df = format_data(load_calls(start_date.strftime('%Y-%m-%d %H:%M:%S'),
                      end_date.strftime('%Y-%m-%d %H:%M:%S')))
    return df

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
    df["Fim da ligação"] = pd.to_datetime(df["Fim da ligação"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
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


