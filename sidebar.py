import streamlit as st

def logout():
    """Função para resetar o estado de login e recarregar a página."""
    st.session_state.authenticated = False
    st.session_state.user_type = None
    st.session_state.team = None
    st.rerun()  # Garante que o logout seja processado corretamente

def setup_sidebar():
    """Configura a sidebar com base no tipo de usuário logado."""

    # Se não estiver logado, oculta a sidebar
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        return

    # Configura a sidebar apenas para usuários logados
    with st.sidebar:
        st.header("Navegação")

        # Se for admin, exibe todas as páginas
        if st.session_state.user_type == "admin":
            st.page_link("pages/1_Admin.py", label="Admin")
            st.page_link("pages/2_time_alfa.py", label="Time Alfa")
            st.page_link("pages/3_time_beta.py", label="Time Beta")
            st.page_link("pages/4_time_charlie.py", label="Time Charlie")
            st.page_link("pages/5_Espec.py", label="Visão de Espectador")

        # Se for líder, exibe apenas sua página e a de espectador
        elif st.session_state.user_type == "líder":
            if st.session_state.team == "time_alfa":
                st.page_link("pages/2_time_alfa.py", label="Time Alfa")
            elif st.session_state.team == "time_beta":
                st.page_link("pages/3_time_beta.py", label="Time Beta")
            elif st.session_state.team == "time_charlie":
                st.page_link("pages/4_time_charlie.py", label="Time Charlie")

            st.page_link("pages/5_Espec.py", label="Visão de Espectador")

        # Botão de Logout corrigido
        if st.button("Sair"):
            logout()  # Chama a função de logout corretamente
