import streamlit as st
from sidebar import setup_sidebar

st.set_page_config(page_title="Espectador", page_icon="👀")

# Se o usuário estiver logado, exibe a sidebar
# Chama a sidebar
setup_sidebar()

    
st.title("Modo Espectador")
st.write("Bem-vindo ao modo espectador do Dashboard.")
