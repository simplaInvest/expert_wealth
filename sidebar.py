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
            st.page_link("pages/teste.py", label = "Dados do Funil")
            st.page_link("pages/Pipe.py", label = "Pipeline & Forecast")
            st.page_link("pages/Perdas&Opts.py", label = "Perdas & Oportunidades")

        # Botão de Logout (visível apenas se logado)
        if user_type:
            st.divider()
            st.markdown("### 🔐 Sessão")
            if st.button("🚪 Sair"):
                logout()

