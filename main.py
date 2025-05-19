import streamlit as st
from funcs import carregar_planilha, preparar_dataframe, adicionar_time, carregar_dataframes

# Carrega as senhas do secrets.toml
logins = st.secrets["logins"]

# Configuração inicial
st.set_page_config(page_title="Login - Expert Comercial Wealth", 
                   page_icon="📊", 
                   layout="wide", 
                   initial_sidebar_state="collapsed")

# Inicializa o estado de login
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_type = None
    st.session_state.team = None

# Oculta a sidebar para quem não está logado
st.sidebar.empty()

# Página de Login
def main():
    # Centraliza a logo
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        st.image("z_logo_dark.png", use_container_width=True) # Substitua pelo caminho correto da logo
    
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        st.title("Expert Comercial Wealth")

        # Formulário de Login'
        with st.form("login_form"):
            st.subheader("Acesso ao Dashboard")
            username = st.text_input("Nome", placeholder="Digite seu nome")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            login_button = st.form_submit_button("Entrar")

        # Botão Espectador (não precisa de autenticação)
        mensal_button = st.button("Viz Mensal")          
        semanal_button = st.button("Viz Semanal")

            
    # Verifica o login e define permissões
    if login_button:
        if username == "admin" and password == logins["admin"]:
            st.session_state.authenticated = True
            st.session_state.user_type = "admin"
            carregar_dataframes()
            st.switch_page("pages/0_Metrics.py")
        else:
            st.session_state.authenticated = False
            st.session_state.user_type = None
            st.error("Nome ou senha incorretos. Tente novamente.")
    
    if mensal_button:
        st.session_state.authenticated = True
        st.session_state.user_type = "spec"
        carregar_dataframes()
        st.switch_page("pages/1_Mensal.py")

    if semanal_button:
        st.session_state.authenticated = True
        st.session_state.user_type = "spec"
        carregar_dataframes()
        st.switch_page("pages/2_Semanal.py")



# Executa a função principal
if __name__ == "__main__":
    main()
