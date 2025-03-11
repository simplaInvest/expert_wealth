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
            st.page_link("pages/1_Admin.py", label="🔧 Admin")
            st.page_link("pages/3_time_bravo.py", label="⚔️ Time Bravo")
            st.page_link("pages/4_time_fenix.py", label="🐦 Time Fenix")
            st.page_link("pages/6_time_bulls.py", label="🐂 Time Bulls")
            st.page_link("pages/5_Espec.py", label="👀 Visão de Espectador")

        # Se for líder, exibe apenas sua página e a de espectador
        elif st.session_state.user_type == "líder":
            if st.session_state.team == "time_bravo":
                st.page_link("pages/3_time_bravo.py", label="⚔️ Time Bravo")
            elif st.session_state.team == "time_fenix":
                st.page_link("pages/4_time_fenix.py", label="🐦 Time Fenix")
            elif st.session_state.team == "time_bulls":
                st.page_link("pages/6_time_bulls.py", label="🐂 Time Bulls")

            st.page_link("pages/5_Espec.py", label="👀 Visão de Espectador")

        # Botão de Logout corrigido
        if st.button("Sair"):
            logout()  # Chama a função de logout corretamente
