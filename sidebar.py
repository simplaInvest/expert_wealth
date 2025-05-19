import streamlit as st

def logout():
    """Função para resetar o estado de login e recarregar a página."""
    st.session_state.authenticated = False
    st.session_state.user_type = None
    st.session_state.team = None
    st.switch_page("main.py")
    st.rerun()  # Garante que o logout seja processado corretamente

def setup_sidebar():
    """Configura a sidebar com base no tipo de usuário logado."""

    with st.sidebar:
        st.header("Navegação")

        # Se for admin, exibe todas as páginas
        if st.session_state.user_type == "admin":
            st.page_link("pages/0_Metrics.py", label = '🔻 Métricas funil')
            st.page_link("pages/1_Mensal.py", label = '📅 Viz Mensal')
            st.page_link("pages/2_Semanal.py", label = '7️⃣ Viz Semanal')
            st.page_link("pages/6_time_bulls.py", label="🐂 Time Bulls - Comercial GR")

        # Espectador
        elif st.session_state.user_type == 'spec':
            st.page_link("pages/1_Mensal.py", label = '📅 Viz Mensal')
            st.page_link("pages/2_Semanal.py", label = '7️⃣ Viz Semanal')

        # Botão de Logout corrigido
        if st.button("Sair"):
            logout()  # Chama a função de logout corretamente
