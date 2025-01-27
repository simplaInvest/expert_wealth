import json 
import requests # type: ignore
import os
import datetime
from datetime import date, timedelta, datetime
import pandas as pd # type: ignore

def load_calls(start_date, end_date):
    # Configurações da API
    api_hostname = 'mybilling.fvx.com.br:8444'
    api_user = 'gustavo.andrade@simplawealth.com'
    password = '$impl@123'
    api_base = f'https://{api_hostname}/rest/'
    
    # Ignorar avisos de certificados autoassinados
    requests.packages.urllib3.disable_warnings()
    
    try:
        # Login na API
        req_data = {'params': json.dumps({'login': api_user, 'password': password})}
        r = requests.post(api_base + 'Session/login', data=req_data, verify=False)
        r.raise_for_status()  # Garante que não houve erro na requisição
        data = r.json()
        
        # Verificar se o login foi bem-sucedido
        if 'session_id' not in data:
            raise ValueError("Erro ao obter session_id. Verifique as credenciais.")
        
        session_id = data['session_id']
        
        # INFO: SET DATE/TIME
        info = {'from_date':'2025-01-25 00:00:00','to_date':'2025-01-28 00:00:00', 'show_unsuccessful' : '1'}

        # GET XDRS
        req_data = { 'auth_info': json.dumps({'session_id': session_id}), 'params': json.dumps(info) } 
        r = requests.post(api_base + 'Customer/get_customer_xdrs', data=req_data, verify=False)
        r.raise_for_status()  # Garante que não houve erro na requisição
        data = r.json()
        
        # Verificar se a resposta contém a lista xdr_list
        if 'xdr_list' in data and data['xdr_list']:
            # Criar DataFrame com os dados
            df = pd.DataFrame(data['xdr_list'])
        else:
            # Retorna um DataFrame vazio se não houver dados
            df = pd.DataFrame()
        
        return df
    
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição da API: {e}")
        return pd.DataFrame()  # Retorna DataFrame vazio em caso de erro
    except ValueError as e:
        print(f"Erro nos dados da API: {e}")
        return pd.DataFrame()  # Retorna DataFrame vazio em caso de erro
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return pd.DataFrame()  # Retorna DataFrame vazio em caso de erro
    
def format_data(df):
    # Transformando em datetime
    df['connect_time'] = pd.to_datetime(df['connect_time'], format='%Y-%m-%d %H:%M:%S')
    df['disconnect_time'] = pd.to_datetime(df['disconnect_time'], format='%Y-%m-%d %H:%M:%S')

    df['connect_time'] = df['connect_time'] - pd.Timedelta(hours=3)
    df['disconnect_time'] = df['disconnect_time'] - pd.Timedelta(hours=3)

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
        '3231420381', '1021 (3231420381 - Lucas)',
        '3231420382', '1023 (3231420382 - Douglas)',
        '3231420383', '1025 (3231420383 - Tiago)'
    ]

    df = df.loc[df['CLI'].isin(col_to_filter)]


    substituicoes = {
        '3231420312' : '1002 (3231420312 - Daniel)',
        '3231420313' : '1004 (3231420313 - Toledo)',
        '3231420314' : '1006 (3231420314 - Pedro Vieira)',
        '3231420315' : '1008 (3231420315 - Saint Clair)',
        '3231420316' : '1010 (3231420316 - Rúbio)',
        '3231420310' : '1012 (3231420310 - Marioti)',
        '3231420317' : '1014 (3231420317 - Gustavo B)',
        '3231420319' : '1015 (3231420319 - Gabriel)',
        '3231420380' : '1018 (3231420380 - Micaelli)',
        '3231420381' : '1021 (3231420381 - Lucas)',
        '3231420382' : '1023 (3231420382 - Douglas)',
        '3231420383' : '1025 (3231420383 - Tiago)'
    }

    df['CLI'] = df['CLI'].replace(substituicoes)


    return df