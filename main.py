import streamlit as st
from funcs import carregar_planilha, preparar_dataframe

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
        st.image("path_to_logo.png", use_container_width=True)  # Substitua pelo caminho correto da logo
    
    st.title("Expert Comercial Wealth")

    # Formulário de Login'
    with st.form("login_form"):
        st.subheader("Acesso ao Dashboard")
        username = st.text_input("Nome", placeholder="Digite seu nome")
        password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        login_button = st.form_submit_button("Entrar")

    sheet_url = "https://docs.google.com/spreadsheets/d/17b9kaTH9TjSg2b32m0iHqxKF4XGWC9g6Cl2xl4VdivY/edit?usp=sharing"
    aba_lig = "LIGACOES"
    #aba_usu = "USUARIOS"
    
    # Verifica o login e define permissões
    if login_button:
        if username == "admin" and password == logins["admin"]:
            st.session_state.authenticated = True
            st.session_state.user_type = "admin"
            try:
                df_ligacoes = carregar_planilha(sheet_url, aba_lig)
                df_ligacoes = preparar_dataframe(df_ligacoes)
                #df_usuarios = carregar_planilha(sheet_url, aba_usu)
                st.success("Planilha carregada com sucesso!")
                st.success("Bem-vindo, Admin! Redirecionando...")
                st.switch_page("pages/1_Admin.py")
            except Exception as e:
                st.error(f"Erro ao carregar planilha: {e}")

        elif username == "bravo" and password == logins["bravo"]:
            st.session_state.authenticated = True
            st.session_state.user_type = "líder"
            st.session_state.team = "time_bravo"
            try:
                df_ligacoes = carregar_planilha(sheet_url, aba_lig)
                df_ligacoes = preparar_dataframe(df_ligacoes)
                #df_usuarios = carregar_planilha(sheet_url, aba_usu)
                st.success("Planilha carregada com sucesso!")
                st.success("Bem-vindo, Líder do Time bravo! Redirecionando...")
                st.switch_page("pages/3_time_bravo.py")
            except Exception as e:
                st.error(f"Erro ao carregar planilha: {e}")

        elif username == "fenix" and password == logins["fenix"]:
            st.session_state.authenticated = True
            st.session_state.user_type = "líder"
            st.session_state.team = "time_fenix"
            try:
                df_ligacoes = carregar_planilha(sheet_url, aba_lig)
                df_ligacoes = preparar_dataframe(df_ligacoes)
                #df_usuarios = carregar_planilha(sheet_url, aba_usu)
                st.success("Planilha carregada com sucesso!")
                st.success("Bem-vindo, Líder do Time Fenix! Redirecionando...")
                st.switch_page("pages/4_time_fenix.py")
            except Exception as e:
                st.error(f"Erro ao carregar planilha: {e}")

        elif username == "bulls" and password == logins["bulls"]:
            st.session_state.authenticated = True
            st.session_state.user_type = "líder"
            st.session_state.team = "time_bulls"
            try:
                df_ligacoes = carregar_planilha(sheet_url, aba_lig)
                df_ligacoes = preparar_dataframe(df_ligacoes)
                #df_usuarios = carregar_planilha(sheet_url, aba_usu)
                st.success("Planilha carregada com sucesso!")
                st.success("Bem-vindo, Líder do Time Bulls! Redirecionando...")
                st.switch_page("pages/6_time_bulls.py")
            except Exception as e:
                st.error(f"Erro ao carregar planilha: {e}")

        else:
            st.session_state.authenticated = False
            st.session_state.user_type = None
            st.error("Nome ou senha incorretos. Tente novamente.")

    # Botão Espectador (não precisa de autenticação)
    #if st.button("Espectador"):
    #    st.switch_page("pages/5_Espec.py")

# Executa a função principal
if __name__ == "__main__":
    main()
