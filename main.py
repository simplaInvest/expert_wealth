import streamlit as st

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
    col1, col2, col3 = st.columns([1,3,1])
    with col2:
        st.image("path_to_logo.png", width=500)  # Substitua pelo caminho correto da logo
    
    st.title("Expert Comercial Wealth")

    # Formulário de Login
    with st.form("login_form"):
        st.subheader("Acesso ao Dashboard")
        username = st.text_input("Nome", placeholder="Digite seu nome")
        password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        login_button = st.form_submit_button("Entrar")
    
    # Verifica o login e define permissões
    if login_button:
        if username == "admin" and password == logins["admin"]:
            st.session_state.authenticated = True
            st.session_state.user_type = "admin"
            st.success("Bem-vindo, Admin! Redirecionando...")
            st.switch_page("pages/1_Admin.py")

        elif username == "alfa" and password == logins["alfa"]:
            st.session_state.authenticated = True
            st.session_state.user_type = "líder"
            st.session_state.team = "time_alfa"
            st.success("Bem-vindo, Líder do Time Alfa! Redirecionando...")
            st.switch_page("pages/2_time_alfa.py")

        elif username == "beta" and password == logins["beta"]:
            st.session_state.authenticated = True
            st.session_state.user_type = "líder"
            st.session_state.team = "time_beta"
            st.success("Bem-vindo, Líder do Time Beta! Redirecionando...")
            st.switch_page("pages/3_time_beta.py")

        elif username == "charlie" and password == logins["charlie"]:
            st.session_state.authenticated = True
            st.session_state.user_type = "líder"
            st.session_state.team = "time_charlie"
            st.success("Bem-vindo, Líder do Time Charlie! Redirecionando...")
            st.switch_page("pages/4_time_charlie.py")

        else:
            st.session_state.authenticated = False
            st.session_state.user_type = None
            st.error("Nome ou senha incorretos. Tente novamente.")

    # Botão Espectador (não precisa de autenticação)
    if st.button("Espectador"):
        st.switch_page("pages/5_Espec.py")

# Executa a função principal
if __name__ == "__main__":
    main()
