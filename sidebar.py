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
        user_type = st.session_state.get("user_type", None)  # ✅ Seguro

        # Se for admin, exibe todas as páginas
        if user_type == "admin":
            st.page_link("pages/sheets.py", label="📝 Planilhas")
            st.page_link("pages/0_Metrics.py", label='🔻 Métricas funil')
            st.page_link("pages/2_SDR.py", label = "📞 SDRs")
            st.page_link("pages/6_time_bulls.py", label="🐂 Time Bulls - Comercial GR")

        # Botão de Logout (visível apenas se logado)
        if user_type:
            st.divider()
            st.markdown("### 🔐 Sessão")
            if st.button("🚪 Sair"):
                logout()

