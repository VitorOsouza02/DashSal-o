import streamlit as st
import pandas as pd
from auth import apply_page_visibility_filter

st.set_page_config(
    page_title="Central de Dashboards",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- Autenticação simples ---
try:
    USUARIO_MESTRE = st.secrets["auth"]["master_user"]
    SENHA_MESTRE = st.secrets["auth"]["master_password"]
    HEAD_CREDENTIALS = dict(st.secrets.get("heads", {}))
except Exception:
    st.error("Configuração de autenticação não encontrada em .streamlit/secrets.toml")
    st.stop()

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

def _reset_auth_state():
    for key in ['autenticado', 'usuario', 'pages_permitidas', 'linhas_permitidas', 'auth_error', 'head_info']:
        st.session_state.pop(key, None)

def _set_session_for_mestre():
    st.session_state['autenticado'] = True
    st.session_state['usuario'] = USUARIO_MESTRE
    st.session_state['pages_permitidas'] = None  # acesso completo
    st.session_state['linhas_permitidas'] = []  # vazio => acesso total
    st.session_state['auth_error'] = None

def _set_session_for_head(username: str, dados_head: dict):
    st.session_state['autenticado'] = True
    st.session_state['usuario'] = username
    st.session_state['pages_permitidas'] = ['Dashboard_Áreas.py']
    st.session_state['linhas_permitidas'] = dados_head.get('linhas', [])
    st.session_state['auth_error'] = None
    st.session_state['head_info'] = dados_head.get('descricao', '')

def login_form():
    st.markdown('<h2 style="color:#fff;">Login</h2>', unsafe_allow_html=True)
    usuario = st.text_input('Usuário', key='usuario_login')
    senha = st.text_input('Senha', type='password', key='senha_login')
    if st.button('Entrar', key='btn_login'):
        _reset_auth_state()
        if usuario == USUARIO_MESTRE and senha == SENHA_MESTRE:
            _set_session_for_mestre()
            st.rerun()

        head_data = HEAD_CREDENTIALS.get(usuario)
        if head_data and senha == head_data['senha']:
            _set_session_for_head(usuario, head_data)
            st.rerun()

        st.error('Usuário ou senha incorretos.')

if not st.session_state['autenticado']:
    login_form()
    st.stop()


# Oculta páginas não permitidas para o usuário atual
apply_page_visibility_filter()

st.markdown("""
<style>
    /* 1. FUNDO GERAL (Dark Mode forçado) */
    body, .stApp, .block-container, .main, [data-testid="stAppViewContainer"] { 
        background-color: #E6EAE1 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* 2. SIDEBAR - Cor de fundo e remoção de bordas estranhas */
    [data-testid="stSidebar"] {
        background-color: #20352f !important;
        border-radius: 10px !important;
        border-right: 1px solid #2ecc71 !important; 
        border-bottom: 1px solid #2ecc71 !important;
        border-top: 1px solid #2ecc71 !important;
    }

    /* Garante que textos da sidebar sejam brancos */
    [data-testid="stSidebar"] *, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] div {
        color: #ffffff !important;
    }

    /* 3. MENU DE NAVEGAÇÃO (Ajuste do título e espaçamento) */
    [data-testid="stSidebarNav"] {
        padding-top: 0px !important;
    }

    /* Título "Menu Principal" estilizado */
    [data-testid="stSidebarNav"]::before {
        content: "Menu Principal";
        display: block;
        margin-left: 20px;
        margin-bottom: 20px;
        font-size: 1.1rem; /* Tamanho bom */
        font-weight: 600;
        color: #2ecc71 !important; /* Verde destaque no título */
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 1px solid rgba(255,255,255,0.2); /* Linha divisória sutil */
        padding-bottom: 10px;
        width: 85%;
    }

    /* 4. ITEM DO MENU ATIVO (Onde você está clicado) */
    ul[data-testid="stSidebarNavItems"] li div a[aria-current="page"] {
        background-color: #2ecc71 !important; /* Fundo Verde */
        border-radius: 5px !important;
    }
    
    /* Texto do item ativo fica preto para contraste */
    ul[data-testid="stSidebarNavItems"] li div a[aria-current="page"] span,
    ul[data-testid="stSidebarNavItems"] li div a[aria-current="page"] p {
        color: #263238 !important; 
        font-weight: bold !important;
    }

    /* 5. HOVER (Quando passa o mouse nos itens) */
    ul[data-testid="stSidebarNavItems"] li div a:hover {
        background-color: #88E788 !important;
        border-radius: 5px !important;
    }
    ul[data-testid="stSidebarNavItems"] li div a:hover span,
    ul[data-testid="stSidebarNavItems"] li div a:hover p {
        color: #20352f !important;
        font-weight: bold !important;
    }

    /* Centralizar a logo na Home (Mantido do seu código) */
    .central-logo-container {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: flex-start;
        height: 50vh;
        width: 100%;
        margin-left: 3vw;
        margin-top: 15px;
    }
    .central-logo-container img {
        max-width: 70vw;
        width: 90%;
        height: auto;
        margin-top: 0;
    }
</style>
""", unsafe_allow_html=True)

# Conteúdo principal: só o título e a logo centralizada
st.markdown("""
<h1 style='margin-left: 17vw; color: #20352F; font-size: 2.2rem;'>👋 Bem-vindo à Central de Dashboards</h1>
""", unsafe_allow_html=True)
