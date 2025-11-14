import json
import streamlit as st
import streamlit.components.v1 as components

_PAGE_DISPLAY_NAMES = {
    'Home.py': 'Home',
    'Dashboard_Áreas.py': 'Dashboard Áreas',
    'Dashboard_Captação.py': 'Dashboard Captação',
    'Dashboard_FeeBased.py': 'Dashboard FeeBased',
    'Dashboard_Receitas.py': 'Dashboard Receitas',
    'Dashboard_Visão_Assessor.py': 'Dashboard Visão Assessor',
}

def _go_home():
    """Redireciona para a página inicial."""
    try:
        st.switch_page("Home.py")   # Home na RAIZ (sem "pages/")
    except Exception:
        try:
            st.switch_page("Home")  # algumas versões aceitam só o rótulo
        except Exception:
            st.page_link("Home.py", label="🏠 Voltar para a Home")
    st.stop()


def check_auth(required_page: str | None = None):
    if not st.session_state.get('autenticado'):
        _go_home()
        return

    allowed_pages = st.session_state.get('pages_permitidas')
    if required_page and allowed_pages and required_page not in allowed_pages:
        st.session_state['auth_error'] = "Você não possuí acesso a esta página."
        _go_home()
        return


    allowed_pages = st.session_state.get('pages_permitidas')
    if required_page and allowed_pages:
        if required_page not in allowed_pages:
            st.session_state['auth_error'] = "Você não possuí acesso a esta página."
            _go_home()

def user_has_access_to_linha(linha: str) -> bool:
    """Retorna True se o usuário pode visualizar a linha de receita informada."""
    linhas = st.session_state.get('linhas_permitidas')
    if not linhas:
        return True  # nenhum filtro → acesso total (usuário mestre)
    return linha in linhas

def is_head_user() -> bool:
    """Indica se o usuário logado é um head (possui linhas restritas)."""
    linhas = st.session_state.get('linhas_permitidas')
    return bool(linhas)

def _allowed_nav_labels() -> list[str] | None:
    allowed_pages = st.session_state.get('pages_permitidas')
    if allowed_pages is None:
        return None

    labels = []
    for page in allowed_pages:
        label = _PAGE_DISPLAY_NAMES.get(page)
        if not label:
            label = page.replace('.py', '').replace('_', ' ').strip()
        labels.append(label)

    labels.append(_PAGE_DISPLAY_NAMES.get('Home.py', 'Home'))
    return labels

def apply_page_visibility_filter():
    allowed_labels = _allowed_nav_labels()
    if not allowed_labels:
        return

    script = f"""
    <script>
    const allowed = {json.dumps(allowed_labels, ensure_ascii=False)};
    function filterNav() {{
        const navRoot = window.parent.document.querySelector('[data-testid="stSidebarNav"]');
        if (!navRoot) {{ return; }}
        const items = navRoot.querySelectorAll('li a div span, li a span, li button span');
        items.forEach(el => {{
            const label = el.textContent.trim();
            const item = el.closest('li');
            if (!allowed.includes(label) && item) {{
                item.style.display = 'none';
            }}
        }});
    }}
    const observer = new MutationObserver(filterNav);
    observer.observe(window.parent.document.body, {{ childList: true, subtree: true }});
    window.addEventListener('load', filterNav);
    filterNav();
    </script>
    """

    components.html(script, height=0, width=0)
