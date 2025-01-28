import streamlit as st
from sidebar import setup_sidebar  # Importa a sidebar

st.set_page_config(page_title="Time Beta", page_icon="⚽", layout="wide")

# Verifica autenticação
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Acesso negado. Faça login para acessar esta página.")
    st.switch_page("main.py")

# Permite acesso se for admin ou líder do Time Beta
if st.session_state.user_type == "admin" or (st.session_state.user_type == "líder" and st.session_state.team == "time_beta"):
    
    # Exibe a sidebar configurada corretamente
    setup_sidebar()

    # Conteúdo da página
    st.title("Painel do Time Beta")
    st.write("Bem-vindo à página do Time Beta.")

else:
    st.warning("Acesso negado.")
    st.switch_page("main.py")
