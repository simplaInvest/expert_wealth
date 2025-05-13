import streamlit as st
from funcs import carregar_planilha, preparar_dataframe, adicionar_time

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
    
    # Verifica o login e define permissões
    if login_button:
        if username == "admin" and password == logins["admin"]:
            st.session_state.authenticated = True
            st.session_state.user_type = "admin"

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
                st.success("Bem-vindo, Admin! Redirecionando...")
                st.switch_page("pages/0_Metrics.py")


        # elif username == "bravo" and password == logins["bravo"]:
        #     st.session_state.authenticated = True
        #     st.session_state.user_type = "líder"
        #     st.session_state.team = "time_bravo"
        #     try:
        #         df_ligacoes = carregar_planilha(sheet_url, aba_lig)
        #         df_ligacoes = preparar_dataframe(df_ligacoes)
        #         #df_usuarios = carregar_planilha(sheet_url, aba_usu)
        #         st.success("Planilha carregada com sucesso!")
        #         st.success("Bem-vindo, Líder do Time bravo! Redirecionando...")
        #         st.switch_page("pages/3_time_bravo.py")
        #     except Exception as e:
        #         st.error(f"Erro ao carregar planilha: {e}")

        # elif username == "fenix" and password == logins["fenix"]:
        #     st.session_state.authenticated = True
        #     st.session_state.user_type = "líder"
        #     st.session_state.team = "time_fenix"
        #     try:
        #         df_ligacoes = carregar_planilha(sheet_url, aba_lig)
        #         df_ligacoes = preparar_dataframe(df_ligacoes)
        #         #df_usuarios = carregar_planilha(sheet_url, aba_usu)
        #         st.success("Planilha carregada com sucesso!")
        #         st.success("Bem-vindo, Líder do Time Fenix! Redirecionando...")
        #         st.switch_page("pages/4_time_fenix.py")
        #     except Exception as e:
        #         st.error(f"Erro ao carregar planilha: {e}")

        # elif username == "bulls" and password == logins["bulls"]:
        #     st.session_state.authenticated = True
        #     st.session_state.user_type = "líder"
        #     st.session_state.team = "time_bulls"
        #     try:
        #         df_ligacoes = carregar_planilha(sheet_url, aba_lig)
        #         df_ligacoes = preparar_dataframe(df_ligacoes)
        #         #df_usuarios = carregar_planilha(sheet_url, aba_usu)
        #         st.success("Planilha carregada com sucesso!")
        #         st.success("Bem-vindo, Líder do Time Bulls! Redirecionando...")
        #         st.switch_page("pages/6_time_bulls.py")
        #     except Exception as e:
        #         st.error(f"Erro ao carregar planilha: {e}")

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
