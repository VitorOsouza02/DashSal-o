# Dash_Salão_Atualizado.py

import re
import sys
import math
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from textwrap import dedent

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# --- Carregar dados do Positivador (DBV Capital_Positivador.db) ---
@st.cache_data(show_spinner=False)
def carregar_dados_positivador() -> pd.DataFrame:
    """
    Carrega os dados do Positivador do banco de dados SQLite.
    Retorna um DataFrame com as colunas Data_Posicao e Net_Em_M.
    """
    db_path = Path(__file__).parent.parent / 'DBV Capital_Positivador.db'
    try:
        conn = sqlite3.connect(str(db_path))
        df = pd.read_sql_query("SELECT * FROM positivador", conn)
        conn.close()

        # Garantir tipos corretos
        df['Data_Posicao'] = pd.to_datetime(df['Data_Posicao'], errors='coerce')
        df['Net_Em_M'] = pd.to_numeric(df['Net_Em_M'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do Positivador: {e}")
        return pd.DataFrame()

# DataFrame usado pelos gráficos de AUC
df_positivador = carregar_dados_positivador()

# =====================================================
# CONTROLE DE SEÇÕES - ATIVE/DESATIVE AQUI
# =====================================================
# Mude para True para exibir a seção de Renda Variável
# Mude para False para ocultar temporariamente
EXIBIR_RENDA_VARIAVEL = False


# =====================================================
# FUNÇÃO PARA RENDERIZAR O PAINEL "RUMO A 1BI" NA TV
# =====================================================
def render_rumo_a_1bi(auc_base_inicial_2025: float = 0.0):
    """
    Renderiza o painel 'Rumo a 1BI' na coluna atual.
    Meta: Busca valor de 2027 na coluna 'auc_objetivo_ano' (AUC Objetivo).
    Projetado: Projeção linear de 01/01/2025 até 31/12/2027.
    """
    # Define o Objetivo Final (2027) usando a função centralizada
    OBJETIVO_FINAL = obter_meta_objetivo(2027, "auc_objetivo_ano", 1_000_000_000.0)

    # AUC atual (Realizado)
    v_auc = 0.0
    try:
        mets = calcular_indicadores_objetivos(df_pos_f, df_obj, hoje=data_ref)
        if "auc" in mets and "valor" in mets["auc"]:
            v_auc = float(mets["auc"]["valor"] or 0.0)
    except Exception as e:
        st.error(f"Erro ao carregar o AUC atual: {e}")
        v_auc = 0.0

    # --- CÁLCULO DO PROJETADO (CURVA 600M / 800M / 1BI) ---
    data_atualizacao = pd.Timestamp(data_ref)

    # Metas por ano (valores acumulados de AUC alvo)
    # 31/12/2025 -> ~600M
    # 31/12/2026 -> ~800M
    # 31/12/2027 -> 1BI (OBJETIVO_FINAL)
    meta_2025 = obter_meta_objetivo(2025, "auc_objetivo_ano", 600_000_000.0)
    meta_2026 = obter_meta_objetivo(2026, "auc_objetivo_ano", 800_000_000.0)
    meta_2027 = OBJETIVO_FINAL  # normalmente 1_000_000_000.0

    # Garante que a curva seja crescente e não ultrapasse o objetivo final
    meta_2025 = max(0.0, min(meta_2025, meta_2026, meta_2027))
    meta_2026 = max(meta_2025, min(meta_2026, meta_2027))
    meta_2027 = max(meta_2026, meta_2027)

    # Marcos de datas
    d0 = pd.Timestamp(2025, 1, 1)
    d1 = pd.Timestamp(2025, 12, 31)
    d2 = pd.Timestamp(2026, 12, 31)
    d3 = pd.Timestamp(2027, 12, 31)

    # Valores de referência em cada marco
    v0 = 0.0
    v1 = meta_2025
    v2 = meta_2026
    v3 = meta_2027

    def _interp_linear(data, di, df, vi, vf) -> float:
        """
        Interpola linearmente entre (di, vi) e (df, vf)
        garantindo que no início seja vi e no fim seja vf.
        """
        if data <= di:
            return float(vi)
        if data >= df:
            return float(vf)
        total = (df - di).days
        if total <= 0:
            return float(vf)
        decorrido = (data - di).days
        return float(vi + (vf - vi) * (decorrido / total))

    # Define o projetado conforme o ano em que estamos
    if data_atualizacao < d0:
        threshold_projetado = 0.0
    elif data_atualizacao <= d1:
        # 2025: Usar o mesmo cálculo do AUC 2025 para consistência
        try:
            mets_auc = calcular_indicadores_objetivos(df_pos_f, df_obj, hoje=data_atualizacao)
            if "auc" in mets_auc and "pace_target" in mets_auc["auc"]:
                threshold_projetado = float(mets_auc["auc"]["pace_target"])
            else:
                threshold_projetado = _interp_linear(data_atualizacao, d0, d1, v0, v1)
        except Exception:
            threshold_projetado = _interp_linear(data_atualizacao, d0, d1, v0, v1)
    elif data_atualizacao <= d2:
        # 2026: meta_2025 -> meta_2026 (ex.: 600M -> 800M)
        threshold_projetado = _interp_linear(data_atualizacao, d1, d2, v1, v2)
    elif data_atualizacao <= d3:
        # 2027: meta_2026 -> meta_2027 (ex.: 800M -> 1BI)
        threshold_projetado = _interp_linear(data_atualizacao, d2, d3, v2, v3)
    else:
        # Depois de 2027-12-31 considera objetivo cheio
        threshold_projetado = float(meta_2027)

    # Cálculos auxiliares para os cards
    pct_auc = (v_auc / OBJETIVO_FINAL) * 100 if OBJETIVO_FINAL > 0 else 0
    restante_auc = max(0.0, OBJETIVO_FINAL - v_auc)

    # Dias restantes até o fim de 2027
    dias_restantes = max(0, (d3 - data_atualizacao).days)

    # Comparação para a barra: Real vs Projetado (Pace)
    diff_pace = v_auc - threshold_projetado
    pct_diff_pace = (diff_pace / threshold_projetado * 100) if threshold_projetado > 0 else 0

    if diff_pace >= 0:
        diff_text = f"<span style='color:#2ecc7a'>{fmt_valor(diff_pace)} ({pct_diff_pace:+.1f}%) 🎯</span>"
        border_style = "border-left-color: #2ecc7a !important;"
    else:
        diff_text = f"<span style='color:#e74c3c'>{fmt_valor(diff_pace)} ({pct_diff_pace:+.1f}%)</span>"
        border_style = "border-left-color: #e74c3c !important;"

    # Title removed as per request

    # Objetivo Total
    fmt_objetivo_final = formatar_valor_curto(OBJETIVO_FINAL)
    st.markdown(
        f"""
        <div class='objetivo-card-topo'>
          <span>Objetivo Total (2027):</span>
          <span class='valor'>{fmt_objetivo_final}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Barras de Progresso
    render_custom_progress_bars(
        objetivo_hoje_val=threshold_projetado,
        realizado_val=v_auc,
        max_val=OBJETIVO_FINAL,
        min_val=auc_base_inicial_2025,
    )

    # Cards
    cards_rumo_html = f"""
    <div class="tv-metric-grid">
      <div class="metric-pill metric-pill-top"
           style="min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
        <div class="label" style="font-size: 11px;">Dias Restantes</div>
        <div class="value" style="font-size: 0.9rem;">{dias_restantes}</div>
      </div>

      <div class="metric-pill metric-pill-top"
           style="{border_style} min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
        <div class="label" style="font-size: 11px;">Projetado vs Realizado</div>
        <div class="value"
             style="font-size: 0.8rem; line-height: 1.2;">
          {diff_text}
        </div>
      </div>

      <div class="metric-pill metric-pill-top"
           style="min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
        <div class="label" style="font-size: 11px; white-space: nowrap;">
          Percentual Realizado
        </div>
        <div class="value"
             style="font-size: 0.9rem; font-weight: bold;">
          {fmt_pct(pct_auc/100)}
        </div>
      </div>

      <div class="metric-pill metric-pill-top"
           style="min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
        <div class="label" style="font-size: 11px; white-space: nowrap;">
          Valor Restante
        </div>
        <div class="value"
             style="font-size: 0.9rem; font-weight: bold;">
          <span style="color:white">{fmt_valor(restante_auc)}</span>
        </div>
      </div>
    </div>
    """
    st.markdown(cards_rumo_html, unsafe_allow_html=True)

    # Top 3
    st.markdown("<div style='height: 0px;'></div>", unsafe_allow_html=True)
    items_rumo_auc, _ = top3_mes_cap(df_pos_f, value_col="Net_Em_M")
    _render_top3_horizontal(items_rumo_auc, header_text="Top 3 — AUC")


# ---------------------------------------------------------------------
# Bootstrapping: path + auth/visibility
# ---------------------------------------------------------------------
sys.path.append(str(Path(__file__).parent.parent))
from auth import check_auth, apply_page_visibility_filter  # noqa: E402

# IMPORTANTE: nome do arquivo atualizado
check_auth("Dash_Salão_Atualizado.py")
apply_page_visibility_filter()

# ---------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------# --- Configuração da Página ---
st.set_page_config(
    layout="wide",
    page_title="Dashboard Salão",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
<style>

/* Remove todo espaço superior do Streamlit */
[data-testid="stAppViewContainer"] {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* Container principal sem margem */
.block-container {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* Remove margem que o Streamlit cria no topo do body */
html, body {
    margin: 0 !important;
    padding: 0 !important;
    height: 100%;
}

/* Oculta completamente o menu e a barra superior do Streamlit */
header[data-testid="stHeader"] {
    display: none !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Styles (CSS)
# ---------------------------------------------------------------------
st.markdown(
    """
<style>
:root {
    --radius: 20px; /* Increased border radius for softer look */
    --border-width: 1px;
    --border-color: #d1d9d5; /* Lighter border color */
    --border: var(--border-width) solid var(--border-color);
    --shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    --hover-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    --bg-primary: #20352f; /* Dark green for cards */
    --bg-secondary: #1a2b26;
    --bg-odd: #1e2e29;
    --bg-even: #253a33;
    --text-primary: #ffffff; /* White text for dark cards */
    --text-secondary: #b8f7d4;
    --text-dark: #20352f; /* Dark green text for light background */
    --accent: #2ecc71;
    --accent-hover: #27ae60;
    --transition: all 0.3s ease;
    --yellow: #948161;
    --tv-block-width: 720px;
    --page-bg: #E8EFE9; /* Off-white greenish background */
}

/* Fundo e texto */
html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow-x: hidden;
    background-color: var(--page-bg) !important;
    color: var(--text-dark) !important;
}

/* Main app container */
.stApp, [data-testid="stAppViewContainer"], .main {
    background: var(--page-bg) !important;
    color: var(--text-dark) !important;
    margin: 0 !important;
    padding: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
}

/* Main content container */
[data-testid="stAppViewContainer"] {
    padding: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
    background: var(--page-bg) !important;
}

/* Streamlit block container */
.block-container {
    padding: 0.5rem 0.5% !important;
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 auto !important;
    background: transparent !important;
}

/* Base card style */
.dashboard-card {
    background-color: var(--bg-primary) !important;
    border-radius: var(--radius) !important;
    padding: 20px !important;
    box-shadow: var(--shadow) !important;
    color: var(--text-primary) !important;
    margin-bottom: 20px !important;
    border: 1px solid #2ECC71 !important;
    transition: var(--transition) !important;
}

.dashboard-card:hover {
    box-shadow: var(--hover-shadow) !important;
}

/* Ensure text inside cards is white */
.dashboard-card, 
.dashboard-card h1, 
.dashboard-card h2, 
.dashboard-card h3, 
.dashboard-card p,
.dashboard-card div,
.dashboard-card span {
    color: var(--text-primary) !important;
}

/* Individual KPI Cards */
.metric-card-kpi {
    background: #20352F !important;
    border-radius: 16px !important;
    border: 1px solid #2ECC71 !important;
    padding: 12px 16px 8px 16px !important;   /* reduziu o padding inferior de 16px para 8px */
    margin: 8px 4px 8px 4px !important;       /* reduziu a margem inferior de 14px para 8px */
    box-shadow: 0 6px 16px rgba(0,0,0,0.35) !important;
    color: white !important;
    height: 100%;
}

/* Ensure KPI cards maintain proper spacing */
[data-testid="stHorizontalBlock"] > [data-testid="stHorizontalBlock"] > [data-testid="stHorizontalBlock"] {
    gap: 8px !important;
}

/* Remove any conflicting background colors from parent containers */
div[data-testid="stVerticalBlock"]:not(:has(.metric-card-kpi)) {
    background: transparent !important;
}

/* Section titles in cards */
.section-title {
    color: var(--text-primary) !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    margin-bottom: 15px !important;
    padding-bottom: 8px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* Gráficos e tabelas como cards */
.stPlotlyChart,
.table-container,
.plotly-graph-div {
    border-radius: var(--radius) !important;
    background: var(--bg-primary) !important;
    box-shadow: var(--shadow) !important;
    transition: var(--transition) !important;
    border: 1px solid #2ECC71 !important;
    padding: 8px 16px 4px 16px !important;  /* topo 8px, baixo 4px */
    overflow: visible !important;           /* não cortar a borda inferior */
    box-sizing: border-box;
    height: 100%;
    display: flex;
    flex-direction: column;
    border: 1px solid #2ECC71 !important;
    margin: 0 !important;
}

/* Ensure plotly charts have proper background */
.js-plotly-plot .plotly {
    background-color: transparent !important;
}

/* Style for plotly toolbars */
.modebar {
    background-color: transparent !important;
}

.modebar-btn svg {
    fill: var(--text-primary) !important;
}
/* Alinhamento vertical: gráfico x card NPS */
/* NPS com ajuste fino de alinhamento */
.dashboard-card.nps-card {
    height: 360px !important;
    min-height: 360px !important;
    max-height: 360px !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
    margin-top: 1px !important;    /* Ajuste fino para alinhar com o topo */
}

/* Container do gráfico com ajuste fino (mesma altura do card NPS, sem faixa de data) */
.stPlotlyChart {
    height: 360px !important;
    min-height: 360px !important;
    max-height: 360px !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
    margin-top: 1px !important;    /* Ajuste fino para alinhar com o topo */
}

/* Ajuste interno para o gráfico ocupar tudo */
.stPlotlyChart > div { 
    height: 100% !important; 
}

/* Ajuste para o container do gráfico */
.stPlotlyChart .js-plotly-plot,
.stPlotlyChart .plot-container {
    height: 100% !important;
}

.stPlotlyChart:hover,
.table-container:hover {
    box-shadow: var(--hover-shadow) !important;
    border-color: var(--accent) !important;
}

/* Layout interno dos cards inferiores (sem escala para não sobrar espaço vazio) */
.col-tv-inner {
    max-width: var(--tv-block-width);
    width: 100%;
    margin: 0 auto !important;
    transform: none !important;          /* remove o scale(0.70) */
    transform-origin: top center !important;
}

/* Altura fixa e compacta para os cards */
.tv-metric-grid {
    height: 130px !important;
    min-height: 130px !important;
    margin-bottom: 0px !important;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 5px;
    overflow: hidden;
}

/* Reduz um pouco a fonte e padding dos cards individuais */
.metric-pill-top {
    padding: 2px 2px;
    min-height: 38px;
}
.metric-pill-top .value {
    font-size: 0.85rem;
}

/* Remove margens do container principal */
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
}

/* Pílulas de métricas – padrão */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin: 10px 4px 18px 4px;
    width: 100%;
}

.metric-pill {
    background-color: #334B43;
    border-radius: 12px;
    padding: 6px 8px;
    border-left: 3px solid var(--accent) !important;
    box-shadow: 0 3px 6px rgba(0,0,0,0.18);
    text-align: center;
    min-height: 70px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-sizing: border-box;
    word-wrap: break-word;
    overflow-wrap: break-word;
}

.metric-pill .label {
    font-weight: 600;
    color: #e9fff5;
    margin-bottom: 4px;
    font-size: clamp(0.70rem, 0.9vw, 0.9rem);
    line-height: 1.15;
}

.metric-pill .value {
    font-weight: 800;
    color: #fff;
    font-size: clamp(0.90rem, 1.0vw, 1.05rem);
    line-height: 1.15;
}

/* Versão compacta usada no topo das sessões */
.metric-pill-top {
    padding: 2px 4px;
    min-height: 44px;
    max-width: 260px;
    margin-left: auto;
    margin-right: auto;
    width: 100%;
}

.metric-pill-top .label {
    font-size: clamp(0.58rem, 0.65vw, 0.70rem);
}

.metric-pill-top .value {
    font-size: clamp(0.74rem, 0.80vw, 0.86rem);
}

/* Pílulas compactas para TV */
.metric-pill-tv {
    background-color: #334B43;
    border-radius: 10px;
    padding: 4px 6px;
    border-left: 2px solid var(--accent) !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.12);
    text-align: center;
    min-height: 56px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-sizing: border-box;
    word-wrap: break-word;
    overflow-wrap: break-word;
}

.metric-pill-tv .label {
    font-weight: 600;
    color: #e9fff5;
    margin-bottom: 2px;
    font-size: clamp(0.60rem, 0.7vw, 0.7rem);
    line-height: 1.05;
}

.metric-pill-tv .value {
    font-weight: 800;
    color: #fff;
    font-size: clamp(0.78rem, 0.85vw, 0.88rem);
    line-height: 1.10;
}

/* Tabela de ranking (NPS/RV) */
.ranking-table {
  margin: 0 !important;
  width: 100%;
  border-collapse: collapse !important;
  border-spacing: 0 !important;
  font-size: 1.0em !important;s
  color: var(--text-primary) !important;
  border-radius: 12px;
  overflow: hidden;
}

.ranking-table thead tr:first-child th {
  background: linear-gradient(135deg,
    rgba(46, 204, 113, 0.25),
    rgba(46, 204, 113, 0.12)
  ) !important;
  color: var(--accent) !important;
  font-weight: 700 !important;
  font-size: 1.1em !important;
  padding: 12px 10px !important;
  border: none !important;
  text-align: center !important;
  letter-spacing: 0.5px;
}

.ranking-table thead tr:nth-child(2) th {
  background: var(--bg-secondary) !important;
  color: var(--text-secondary) !important;
  border-bottom: 2px solid rgba(255,255,255,.1) !important;
  font-weight: 600 !important;
  padding: 10px 8px !important;
  text-align: center !important;
  font-size: 0.95em !important;
}
.ranking-table thead tr:nth-child(2) th + th {
  border-left: 1px solid rgba(255,255,255,.1) !important;
}

.ranking-table tbody td {
  padding: 10px 12px !important;
  text-align: center !important;
  border-bottom: 1px solid rgba(255,255,255,.08) !important;
  font-size: 1.05em !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  height: 42px;
  box-sizing: border-box;
}
.ranking-table tbody tr:nth-child(odd) {
  background-color: var(--bg-odd);
}
.ranking-table tbody tr:nth-child(even) {
  background-color: var(--bg-even);
}
.ranking-table tbody tr:hover {
  background-color: var(--accent) !important;
  color: var(--text-primary) !important;
  font-weight: 600 !important;
  transform: scale(1.01);
  transition: all 0.2s ease;
}

.nps-table-title {
  text-align: center;
  color: white;
  font-weight: 800;
  margin: 0 0 8px 0;
  font-size: 1.1em;
}

/* Card superior "Objetivo Total" */
.objetivo-card-topo {
    background-color: #334B43;
    border-radius: 10px;
    padding: 2px 8px;
    text-align: center;
    margin: 6px auto 10px auto;
    width: fit-content;
    border: 1px solid var(--accent);
    box-shadow: 0 2px 4px rgba(0,0,0,0.12);
}
.objetivo-card-topo span {
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--text-primary);
}
.objetivo-card-topo .valor {
    color: var(--accent);
    margin-left: 6px;
    font-size: 0.90rem;
}

/* Card base genérico de sessão */
.dashboard-card-wrap {
    background-color: #212C28;
    border-radius: 12px;
    padding: 20px;
    border: var(--border) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    margin-bottom: 20px;
    position: relative;
}

/* Barras de progresso customizadas */
.progress-wrapper {
    font-family: 'Segoe UI', Roboto, sans-serif;
    padding: 0;
    margin: 4px auto 18px auto;
    max-width: var(--tv-block-width);
    width: 100%;
}

.progress-container {
    display: flex;
    align-items: center;
    margin-bottom: 4px;
    width: 100%;
}

.progress-wrapper .progress-container:first-child {
    margin-bottom: 12px;
}

.progress-label {
    font-weight: 600;
    font-size: 0.8rem;
    color: #e9fff5;
    min-width: 60px;
    text-align: right;
    margin-right: 8px;
    letter-spacing: 0.3px;
}

.progress-bar-track {
    flex: 1;
    height: 40px;
    background-color: #2a3f38;
    border-radius: 8px;
    position: relative;
    overflow: hidden;
    box-shadow: inset 0 3px 6px rgba(0,0,0,0.3);
    border: 1px solid rgba(0,0,0,0.3);
    margin: 4px 0;
    box-sizing: border-box;
}

.progress-bar-fill {
    position: absolute;
    top: 2px;
    bottom: 2px;
    left: 0;
    width: 0;
    background: linear-gradient(90deg, #2ecc71, #27ae60);
    border-radius: 7px;
    transition: width 0.5s ease-in-out;
    box-shadow: inset 0 2px 4px rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.1);
}

.progress-bar-value-label {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-weight: 700;
    font-size: 0.75rem;
    padding: 1px 4px;
    white-space: nowrap;
    color: #ffffff;
    background-color: transparent;
    z-index: 2;
}

/* Rótulos de mínimo/máximo nas extremidades da barra */
.progress-bar-limit-label {
    position: absolute;
    font-size: 0.75rem;
    color: #b8f7d4;
    top: 50%;
    transform: translateY(-50%);
    font-weight: 500;
    opacity: 0.9;
    z-index: 1;
}

.progress-bar-limit-label.left {
    left: 6px;
    text-align: left;
}

.progress-bar-limit-label.right {
    right: 6px;
    text-align: right;
}

/* Efeito de brilho */
.progress-bar-fill::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(
        to right,
        rgba(255, 255, 255, 0) 0%,
        rgba(255, 255, 255, 0.2) 50%,
        rgba(255, 255, 255, 0) 100%
    );
    transform: translateX(-100%);
    animation: shine 2s infinite;
}
@keyframes shine {
    100% {
        transform: translateX(200%);
    }
}

/* Responsivo: metrics-row em 2 colunas em telas menores */
@media (max-width: 1100px) {
  .metrics-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .nps-grid, .rv-table-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}

/* Card NPS genérico */
.nps-card {
  margin-top: 0;
  margin-bottom: 0;
  padding: 14px 16px 10px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

/* Grid dentro do card NPS/RV */
.nps-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-top: 10px;
    width: 100%;
    flex: 1;
}

.nps-grid .metric-pill {
    flex: 1;
    min-width: 0;
}

.nps-card-header {
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom: 12px;
}

/* Card RV reaproveitando layout do NPS */
.rv-card .nps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  width: 100%;
}

.rv-card .metric-pill {
    width: 100%;
    box-sizing: border-box;
    max-width: 100%;
    overflow: hidden;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    position: relative;
}

.rv-card .metric-row {
    display: grid;
    grid-template-columns: 1fr minmax(70px, auto) minmax(60px, auto);
    align-items: center;
    gap: 10px;
    padding: 5px 0;
    border-bottom: 1px solid #2ecc71;
}
.rv-card .metric-row:last-child { border-bottom: none; }

.rv-card .metric-label {
    min-width: 0;
    overflow: hidden;
    text-overflow: unset;
    white-space: normal;
    word-break: break-word;
    color: #fff;
    opacity: .9;
    font-size: .9rem;
    text-align: left;
}
.rv-card .metric-value {
    text-align: right;
    font-weight: 700;
    color: #fff;
    font-size: .98rem;
    white-space: nowrap;
    min-width: 0;
}

/* Grid para tabelas RV */
.rv-table-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 20px;
}

/* Layout TV: Captação / AUC / Rumo a 1BI */
/* Removendo definição duplicada de .col-tv-inner */

.col-tv-inner .progress-bar-track {
  height: 70px;
}

.col-tv-inner .progress-bar-fill {
  top: 6px;
  bottom: 6px;
}

.col-tv-inner .progress-bar-value-label {
  font-size: 0.90rem;
}

.col-tv-inner .progress-label {
  font-size: 0.85rem;
}

/* Grid 2x2 dos cards abaixo das barras */
.tv-metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 12px;
  row-gap: 10px;
  max-width: var(--tv-block-width);
  width: 100%;
  margin: 10px auto 0 auto;
}

.tv-metric-grid .metric-pill.metric-pill-top {
  max-width: 100%;
  width: 100%;
  margin-left: 0;
  margin-right: 0;
}

/* Wrapper do Top 3 alinhado com o bloco da TV */
.col-tv-inner .top3-h-wrap {
  max-width: var(--tv-block-width);
  margin-left: auto;
  margin-right: auto;
}

</style>
""",
    unsafe_allow_html=True,
)

# Ajuste de escala da sessão TV
st.markdown(
    """
<style>

/* Card verde para cada uma das 4 colunas da seção inferior */
div[data-testid="stVerticalBlock"]:has(.metric-card-kpi) {
    background: #20352F !important;            /* verde escuro do dashboard */
    border-radius: 20px !important;
    border: 1px solid #2ECC71 !important;      /* borda verde-clara */
    padding: 18px 20px !important;
    margin: 8px 4px 14px 4px !important;
    box-shadow: 0 10px 24px rgba(0,0,0,0.45);
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Constantes & Mapeamento
# ---------------------------------------------------------------------
YELLOW = "#948161"
GREEN = "#2ecc71"

ASSESSORES_MAP = {
    "A92300": "Adil Amorim",
    "A95715": "André Norat",
    "A87867": "Arthur Linhares",
    "A95796": "Artur Vaz",
    "A95642": "Bruna Lewis",
    "A26892": "Carlos Monteiro",
    "A71490": "Cesar Lima",
    "A93081": "Daniel Morone",
    "A23594": "Diego Monteiro",
    "A23454": "Eduardo Monteiro",
    "A91619": "Eduardo Parente",
    "A95635": "Enzo Rei",
    "A50825": "Fabiane Souza",
    "A46886": "Fábio Tomaz",
    "A96625": "Gustavo Levy",
    "A95717": "Henrique Vieira",
    "A94115": "Israel Oliveira Moraes",
    "A97328": "João Goldenberg ",
    "A41471": "João Pedro Georg de Andrade",
    "A69453": "Guilherme Peçanha",
    "A51586": "Luiz Eduardo Mesquita",
    "A28215": "Luiz Coimbra",
    "A92301": "Marcus Faria",
    "A38061": "Paulo Pinho",
    "A69265": "Paulo Gomes",
    "A25214": "Renato Zanin",
    "A21652": "Rodrigo Teísta",
    "A93282": "Samuel Monteiro",
    "A72213": "Thiago Cordeiro",
    "A26914": "Victor Garrido",
}
NOME_TO_COD = {v.upper(): k for k, v in ASSESSORES_MAP.items()}


def obter_nome_assessor(codigo: str) -> str:
    return ASSESSORES_MAP.get(codigo, codigo)


# ---------------------------------------------------------------------
# Helpers de Formatação / Datas
# ---------------------------------------------------------------------
def formatar_valor_curto(valor: Any) -> str:
    """Formata valores de forma curta (K, M, bi) com R$."""
    if pd.isna(valor) or valor is None:
        return "R$ 0"
    try:
        valor = float(valor)
        if valor == 0:
            return "R$ 0"
        if abs(valor) >= 1_000_000_000:
            return f"R$ {valor / 1_000_000_000:.1f} bi"
        if abs(valor) >= 1_000_000:
            return f"R$ {valor / 1_000_000:.1f} mi"
        if abs(valor) >= 1_000:
            return f"R$ {valor / 1_000:.1f} mil"
        return f"R$ {valor:.0f}"
    except (ValueError, TypeError):
        return str(valor)


def fmt_valor(v: Any) -> str:
    """Formatação monetária usada em RV / Rumo a 1BI."""
    try:
        v = float(v)
    except Exception:
        return str(v)

    if v < 0:
        return f"-{fmt_valor(abs(v))}"
    if v >= 1_000_000:
        return f"R$ {v / 1_000_000:,.2f} Mi".replace(",", "X").replace(".", ",").replace("X", ".")
    if v >= 1_000:
        return f"R$ {v / 1_000:,.2f} K".replace(",", "X").replace(".", ",").replace("X", ".")
    if v == int(v):
        return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {v:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")


def arredondar_valor(valor: Any, casas_decimais: int = 2) -> float:
    """Arredonda um valor numérico (0.5 para cima)."""
    try:
        if valor is None:
            return 0.0
        fator = 10 ** casas_decimais
        return float(int(valor * fator + 0.5) / fator)
    except (TypeError, ValueError):
        return 0.0


def fmt_pct(x: Any) -> str:
    """Formata um valor 0-1 em % brasileiro."""
    try:
        x = arredondar_valor(float(x) * 100, 2)
        return f"{x:,.2f}%".replace(".", "X").replace(",", ".").replace("X", ",")
    except Exception:
        return "-"


def _pct_br(v: float) -> str:
    try:
        return f"{float(v):.2f}%".replace(".", ",")
    except Exception:
        return "0,00%"


def _media_br(v: float) -> str:
    try:
        return f"{float(v):.2f}".replace(".", ",")
    except Exception:
        return "0,00"


def ultima_data(
    df: pd.DataFrame, date_col: str = "Data_Posicao", filter_col: Optional[str] = None
) -> Optional[datetime]:
    if date_col not in df.columns:
        return None
    s = df[date_col]
    if filter_col and filter_col in df.columns:
        s = df.loc[df[filter_col].notna(), date_col]
    s = pd.to_datetime(s, errors="coerce").dropna()
    if s.empty:
        return None
    return s.max()


def extract_assessor_code(x: Any) -> Optional[str]:
    s = str(x or "").strip()
    if not s:
        return None
    up = re.sub(r"\s+", " ", s).upper()

    m = re.search(r"A\s*?(\d{5})", up)
    if m:
        return f"A{m.group(1)}"

    m2 = re.search(r"(^|\D)(\d{5})(\D|$)", up)
    if m2:
        return f"A{m2.group(2)}"

    if up in NOME_TO_COD:
        return NOME_TO_COD[up]

    return None


def _primeiro_nome_sobrenome(nome_completo: str) -> str:
    if not nome_completo:
        return "-"
    tokens = re.split(r"\s+", str(nome_completo).strip())
    if not tokens:
        return "-"
    if len(tokens) == 1:
        return tokens[0]

    particulas = {"de", "da", "das", "do", "dos", "e"}
    nome = tokens[0]
    sobrenome = None
    for t in tokens[1:]:
        if t.lower() in particulas:
            continue
        sobrenome = t
        break
    if not sobrenome:
        sobrenome = tokens[1]
    return f"{nome} {sobrenome}"


def _strip_accents(txt: str) -> str:
    if txt is None:
        return ""
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", str(txt)) if not unicodedata.combining(ch)
    )


def _norm_upper_noaccents_series(s: pd.Series) -> pd.Series:
    return s.astype(str).map(_strip_accents).str.upper().str.strip().fillna("")


# ---------------------------------------------------------------------
# Data Loaders
# ---------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def carregar_dados_objetivos_pj1() -> pd.DataFrame:
    caminho_db = Path(__file__).parent.parent / "DBV Capital_Objetivos.db"
    conn = sqlite3.connect(str(caminho_db))
    df = pd.read_sql_query("SELECT * FROM objetivos", conn)
    conn.close()

    # Converter coluna Objetivo para numérico
    if "Objetivo" in df.columns:
        df["Objetivo"] = pd.to_numeric(df["Objetivo"], errors="coerce")
    
    # Converter outras colunas para numérico se necessário
    for c in [
        "auc_objetivo_ano",
        "auc_acumulado",
        "auc_diario_ano",
        "cap_objetivo_ano",
        "cap_acumulado",
        "cap_diario_ano",
        "rec_objetivo_ano",
        "rec_acumulado_ano",
        "rec_diario_ano",
        "c_ativadas_objetivo_ano",
        "c_ativadas_acumulado_ano",
        "c_ativadas_diario_ano",
    ]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def obter_meta_objetivo(ano_meta: int, coluna: str, fallback: float = 0.0) -> float:
    """
    Busca um valor de objetivo na tabela objetivos filtrando por ano e coluna.

    Regra:
    - Se existir valor no banco:
        - Se o fallback for 0 ou menor/igual ao valor do banco -> usa o valor do banco
        - Se o fallback for MAIOR que o valor do banco -> usa o fallback (valor "forçado")
    - Se não existir linha/coluna ou der erro -> usa o fallback
    """
    try:
        objetivos_df = carregar_dados_objetivos_pj1()
        if objetivos_df.empty:
            return float(fallback)

        # Mapeamento de colunas esperadas -> colunas reais
        col_mapping = {
            "auc_objetivo_ano": "AUC Objetivo",
            "cap_objetivo_ano": "Cap. Liq Objetivo", 
            "rec_objetivo_ano": "Receita Objetivo",
            "c_ativadas_objetivo_ano": "Contas Ativadas"
        }
        
        # Usar coluna mapeada ou original se não houver mapeamento
        coluna_real = col_mapping.get(coluna, coluna)

        # Usar a coluna 'Objetivo' diretamente
        row_ano = objetivos_df.loc[objetivos_df["Objetivo"] == ano_meta]
        if not row_ano.empty and coluna_real in row_ano.columns:
            val_banco = float(row_ano[coluna_real].max())
            if val_banco > 0:
                # Se foi passado um fallback > 0 e ele é MAIOR que o valor do banco,
                # damos prioridade ao fallback (meta "fixada" no código)
                if fallback and fallback > val_banco:
                    return float(fallback)
                return val_banco

        return float(fallback)
    except Exception:
        return float(fallback)


@st.cache_data(show_spinner=False)
def carregar_dados_objetivos() -> pd.DataFrame:
    caminho_db = Path(__file__).parent.parent / "DBV Capital_Objetivos.db"
    if not caminho_db.exists():
        caminho_db = Path("DBV Capital_Objetivos.db")

    conn = sqlite3.connect(str(caminho_db))

    try:
        tabs = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
            conn,
        )["name"].tolist()

        if not tabs:
            st.error("❌ Nenhuma tabela encontrada no banco de Objetivos.")
            return pd.DataFrame()

        if "objetivos_pj1" in tabs:
            table = "objetivos_pj1"
        elif "objetivos" in tabs:
            table = "objetivos"
        else:
            table = tabs[0]

        df = pd.read_sql_query(f'SELECT * FROM "{table}";', conn)

    except Exception as e:
        st.error(f"Erro ao carregar dados de Objetivos: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return pd.DataFrame(
            {
                "data": [pd.Timestamp.today()],
                "ano": [pd.Timestamp.today().year],
                "auc_total": [1.0],
                "captacao_total_diaria": [1.0],
            }
        )

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df["ano"] = df["data"].dt.year
        df["mes"] = df["data"].dt.month

    if "auc_objetivo_ano" in df.columns:
        df["auc_total"] = df["auc_objetivo_ano"]

    if "cap_objetivo_ano" in df.columns:
        df["captacao_total_diaria"] = df["cap_objetivo_ano"]

    for col in ["auc_total", "captacao_total_diaria"]:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


@st.cache_data(show_spinner=False)
def carregar_dados_positivador_mtd() -> pd.DataFrame:
    """
    Carrega o Positivador a partir do novo banco DBV Capital_Positivador.db,
    mantendo compatibilidade com o antigo (MTD) caso ainda exista.
    """
    base_dir = Path(__file__).parent.parent

    candidate_paths = [
        base_dir / "DBV Capital_Positivador.db",
        base_dir / "DBV Capital_Positivador_MTD.db",
        Path("DBV Capital_Positivador.db"),
        Path("DBV Capital_Positivador_MTD.db"),
    ]

    db_path = None
    for p in candidate_paths:
        if p.exists():
            db_path = p
            break

    if db_path is None:
        st.error("❌ Nenhum banco de Positivador encontrado (DBV ou MTD).")
        return pd.DataFrame()

    conn = sqlite3.connect(str(db_path))
    try:
        tabs = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';", conn
        )["name"].tolist()

        if not tabs:
            st.error("❌ Nenhuma tabela encontrada no banco de Positivador.")
            return pd.DataFrame()

        if "positivador" in tabs:
            table = "positivador"
        elif "positivador_mtd" in tabs:
            table = "positivador_mtd"
        else:
            table = tabs[0]

        df = pd.read_sql_query(f'SELECT * FROM "{table}";', conn)

    except Exception as e:
        st.error(f"Erro ao carregar dados do Positivador: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    return df


def obter_ultima_data_posicao() -> datetime:
    """
    Retorna a data mais recente da coluna Data_Posicao do banco de dados.
    Se não conseguir acessar o banco, retorna a data de hoje como fallback.
    """
    try:
        # Carrega os dados do positivador
        df = carregar_dados_positivador_mtd()
        
        # Verifica se a coluna Data_Posicao existe
        if 'Data_Posicao' in df.columns:
            # Converte para datetime se ainda não estiver no formato correto
            if not pd.api.types.is_datetime64_any_dtype(df['Data_Posicao']):
                df['Data_Posicao'] = pd.to_datetime(df['Data_Posicao'], errors='coerce')
            
            # Remove valores nulos e retorna a data mais recente
            df = df.dropna(subset=['Data_Posicao'])
            if not df.empty:
                return df['Data_Posicao'].max().to_pydatetime()
    except Exception as e:
        st.error(f"Erro ao obter a última data do Positivador: {e}")
    
    # Fallback em caso de erro
    return datetime.today()

# Mantido para compatibilidade com código existente
def obter_data_atualizacao_positivador() -> datetime:
    """
    Função mantida para compatibilidade. Agora usa obter_ultima_data_posicao()
    para retornar a data mais recente da coluna Data_Posicao.
    """
    return obter_ultima_data_posicao()


def tratar_dados_positivador_mtd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza as colunas do Positivador, aceitando tanto nomes antigos (Excel)
    quanto os do novo banco DBV Capital_Positivador.db.
    """
    renomear = {
        "Net Em M": "Net_Em_M",
        "net_em_m": "Net_Em_M",
        "Data Posição": "Data_Posicao",
        "data_posicao": "Data_Posicao",
        "Captação Líquida em M": "Captacao_Liquida_em_M",
        "Captação Liq em M": "Captacao_Liquida_em_M",
        "Captacao Liquida em M": "Captacao_Liquida_em_M",
        "captacao_liquida_em_m": "Captacao_Liquida_em_M",
        "Assessor": "assessor",
        "cliente": "Cliente",
    }

    for origem, destino in renomear.items():
        if origem in df.columns:
            df = df.rename(columns={origem: destino})

    if "Data_Posicao" in df.columns:
        df["Data_Posicao"] = pd.to_datetime(df["Data_Posicao"], errors="coerce")

    for c in ["Net_Em_M", "Captacao_Liquida_em_M"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    has_assessor_code = "assessor_code" in df.columns
    if has_assessor_code:
        df["assessor_code"] = df["assessor_code"].astype(str).str.strip()
        valid_codes = df["assessor_code"].str.match(r"^A\d{5}$", na=False).sum()
    else:
        valid_codes = 0

    if (not has_assessor_code) or (valid_codes == 0):
        if "assessor" in df.columns:
            df["assessor"] = df["assessor"].astype(str)
            df["assessor_code"] = df["assessor"].map(extract_assessor_code)
            df["assessor_code"] = df["assessor_code"].where(
                df["assessor_code"].notna() & (df["assessor_code"] != ""),
                pd.NA,
            )
        else:
            df["assessor_code"] = pd.NA
    else:
        df["assessor_code"] = df["assessor_code"].astype(str).str.strip()

    if "Cliente" in df.columns:
        df["Cliente"] = df["Cliente"].astype(str)

    return df


# ---------------------------------------------------------------------
# Loaders NPS / RV
# ---------------------------------------------------------------------
_EXPECTED_KEYS = {
    "survey_id": {"survey id"},
    "user_id": {"id do usuario", "id usuario", "usuario id"},
    "customer_id": {"costumer id", "customer id", "cliente id"},
    "data_resposta": {"data de resposta", "data resposta", "data"},
    "pesquisa_relacionamento": {"pesquisa relacionamento"},
    "nps_assessor": {"xp relacionamento aniversario nps assessor", "nps assessor"},
    "status": {"status"},
    "codigo_assessor": {"codigo assessor", "cod assessor", "codigo do assessor"},
    "notificacao": {"notificacao", "notificacao ?"},
}
_POSSIBLE_NOTA_KEYS = {
    "nota",
    "nota nps",
    "score",
    "pontuacao",
    "resposta nota",
    "nps",
    "xp relacionamento aniversario nps assessor",
}


def _rename_columns_to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    def _norm_key(txt: str) -> str:
        s = _strip_accents(str(txt)).lower()
        s = re.sub(r"[^a-z0-9]+", " ", s).strip()
        return re.sub(r"\s+", " ", s)

    norm_map = {_norm_key(c): c for c in df.columns}
    rename_dict = {}
    for canonical, variants in _EXPECTED_KEYS.items():
        for v in variants:
            if v in norm_map:
                rename_dict[norm_map[v]] = canonical
                break
    df = df.rename(columns=rename_dict)

    nota_col = None
    for c in df.columns:
        if _norm_key(c) in _POSSIBLE_NOTA_KEYS:
            nota_col = c
            break

    if nota_col is None:
        best_col, best_cnt = None, -1
        for c in df.columns:
            s = pd.to_numeric(df[c], errors="coerce")
            if s.notna().any():
                cnt = int(s.between(0, 10, inclusive="both").sum())
                if cnt > best_cnt and cnt > 0:
                    best_col, best_cnt = c, cnt
        nota_col = best_col

    if nota_col:
        df = df.rename(columns={nota_col: "nota"})

    if "data_resposta" in df.columns:
        df["data_resposta"] = pd.to_datetime(
            df["data_resposta"], errors="coerce", dayfirst=True, infer_datetime_format=True
        )
    if "codigo_assessor" in df.columns:
        df["codigo_assessor"] = df["codigo_assessor"].astype(str).str.strip().str.upper()
    if "pesquisa_relacionamento" in df.columns:
        df["pesquisa_relacionamento_norm"] = _norm_upper_noaccents_series(
            df["pesquisa_relacionamento"]
        )
    if "nota" in df.columns:
        df["nota"] = pd.to_numeric(df["nota"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def carregar_dados_nps() -> pd.DataFrame:
    try:
        dbp = None
        for p in [
            Path(__file__).parent.parent / "DBV Capital_NPS.db",
            Path("DBV Capital_NPS.db"),
        ]:
            if p.exists():
                dbp = p
                break

        if dbp is None:
            st.error("❌ Banco NPS não encontrado.")
            return pd.DataFrame()

        with sqlite3.connect(str(dbp)) as conn:
            tabs = pd.read_sql_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
                conn,
            )["name"].tolist()
            if not tabs:
                st.error("❌ Nenhuma tabela encontrada no banco NPS.")
                return pd.DataFrame()

            candidate, best_score = None, -1
            for t in tabs:
                try:
                    df_head = pd.read_sql_query(f'SELECT * FROM "{t}" LIMIT 200;', conn)
                except Exception:
                    continue

                df_norm = _rename_columns_to_canonical(df_head.copy())
                score = (
                    int(
                        "pesquisa_relacionamento" in df_norm.columns
                        or "pesquisa_relacionamento_norm" in df_norm.columns
                    )
                    + int("codigo_assessor" in df_norm.columns)
                    + int("data_resposta" in df_norm.columns)
                    + int("nota" in df_norm.columns)
                )
                if score > best_score:
                    best_score = score
                    candidate = t

            if not candidate:
                candidate = tabs[0]
            df_all = pd.read_sql_query(f'SELECT * FROM "{candidate}";', conn)

        return _rename_columns_to_canonical(df_all)
    except Exception as e:
        st.error(f"Erro ao carregar NPS: {e}")
        return pd.DataFrame()


def _parse_money_series_rv(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip()
    s = s.str.replace("R$", "", regex=False).str.replace(" ", "", regex=False)

    def conv(x: str) -> Any:
        if x in ("", "nan", "NaN", "None"):
            return np.nan
        if re.match(r"^\d{1,3}(\.\d{3})+(,\d+)?$", x):
            return float(x.replace(".", "").replace(",", "."))
        if re.match(r"^\d{1,3}(,\d{3})+(\.\d+)?$", x):
            return float(x.replace(",", ""))
        if "," in x and "." not in x:
            return float(x.replace(",", "."))
        return float(x)

    out = s.map(lambda v: conv(v) if v not in (None, "") else None)
    return pd.to_numeric(out, errors="coerce").fillna(0.0)


def _find_auc_db_path() -> Optional[Path]:
    for p in [
        Path(__file__).parent.parent / "DBV Capital_AUC Mesa RV.db",
        Path("DBV Capital_AUC Mesa RV.db"),
    ]:
        if p.exists():
            return p
    return None


@st.cache_data(show_spinner=False)
def _load_auc_table(db_path: Path) -> pd.DataFrame:
    if not db_path or not Path(db_path).exists():
        return pd.DataFrame()
    with sqlite3.connect(str(db_path)) as conn:
        tabs = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
            conn,
        )["name"].tolist()
        table = "auc_mesa_rv" if "auc_mesa_rv" in tabs else (tabs[0] if tabs else None)
        if not table:
            return pd.DataFrame()
        df = pd.read_sql_query(f'SELECT * FROM "{table}";', conn)

    cols = {c.lower(): c for c in df.columns}
    c_data = cols.get("data")
    c_cli = cols.get("cliente")
    c_ass = cols.get("assessor")
    c_tipo = cols.get("tipo")
    c_auc = cols.get("auc")

    out = pd.DataFrame()
    out["data_parsed"] = (
        pd.to_datetime(df[c_data], dayfirst=True, errors="coerce") if c_data else pd.NaT
    )
    out["cliente"] = df[c_cli].astype(str).str.strip() if c_cli else ""
    out["assessor"] = df[c_ass].astype(str).str.strip() if c_ass else ""
    out["tipo"] = df[c_tipo].astype(str).str.strip() if c_tipo else ""
    out["auc_reais"] = _parse_money_series_rv(df[c_auc]) if c_auc else 0.0
    out = out.dropna(subset=["data_parsed"])
    return out


# ---------------------------------------------------------------------
# Lógica principal KPIs de Objetivos (Captação / AUC)
# ---------------------------------------------------------------------
def calcular_indicadores_objetivos(
    df_pos: pd.DataFrame, df_obj: pd.DataFrame, hoje: datetime
) -> Dict[str, Dict[str, Any]]:
    hoje = pd.Timestamp(hoje or pd.Timestamp.today()).normalize()
    ano_atual = hoje.year

    df_pos = df_pos.copy()
    if "Data_Posicao" in df_pos.columns:
        df_pos["Data_Posicao"] = pd.to_datetime(df_pos["Data_Posicao"], errors="coerce")
    if "Captacao_Liquida_em_M" in df_pos.columns:
        df_pos["Captacao_Liquida_em_M"] = pd.to_numeric(
            df_pos["Captacao_Liquida_em_M"], errors="coerce"
        ).fillna(0)
    if "Net_Em_M" in df_pos.columns:
        df_pos["Net_Em_M"] = pd.to_numeric(df_pos["Net_Em_M"], errors="coerce").fillna(0)

    mesref_pos = None
    if "Data_Posicao" in df_pos.columns and not df_pos["Data_Posicao"].isna().all():
        mesref_pos = df_pos["Data_Posicao"].dt.to_period("M").max()

    capliq_mes_atual = 0.0
    if mesref_pos is not None and "Captacao_Liquida_em_M" in df_pos.columns:
        grp_mes = df_pos.groupby(df_pos["Data_Posicao"].dt.to_period("M"))[
            "Captacao_Liquida_em_M"
        ].sum()
        if mesref_pos in grp_mes.index:
            capliq_mes_atual = float(grp_mes.loc[mesref_pos])

    pace_mes = None
    # Calcular pace para o mês atual da data de referência
    mes_atual_period = pd.Period(year=hoje.year, month=hoje.month, freq='M')
    mes_inicio = mes_atual_period.to_timestamp(how="start")
    mes_fim = mes_atual_period.to_timestamp(how="end")
    dias_mes = (mes_fim - mes_inicio).days + 1
    dias_corridos = (hoje - mes_inicio).days + 1
    pace_mes = dias_corridos / dias_mes

    capliq_ano_atual = 0.0
    if {"Data_Posicao", "Captacao_Liquida_em_M"} <= set(df_pos.columns):
        df_y = df_pos[df_pos["Data_Posicao"].dt.year == ano_atual].copy()
        cap_por_mes = df_y.groupby(df_y["Data_Posicao"].dt.month)["Captacao_Liquida_em_M"].sum()
        capliq_ano_atual = float(cap_por_mes.sum())

    cap_meta_eoy = 0.0
    cap_meta_hoje = 0.0
    try:
        df_pj1 = carregar_dados_objetivos_pj1()
        if not df_pj1.empty and "Objetivo" in df_pj1.columns:
            base = df_pj1[df_pj1["Objetivo"] == ano_atual].copy()
            if not base.empty:
                # Usar diretamente o valor anual de Cap. Liq Objetivo
                if "Cap. Liq Objetivo" in base.columns:
                    cap_meta_eoy = float(base["Cap. Liq Objetivo"].max())
                    # Para meta até hoje, usar proporção do ano
                    dias_decorridos = (hoje - pd.Timestamp(ano_atual, 1, 1)).days + 1
                    total_dias_ano = 366 if pd.Timestamp(ano_atual, 12, 31).dayofyear == 366 else 365
                    cap_meta_hoje = (cap_meta_eoy * dias_decorridos) / total_dias_ano
    except Exception:
        cap_meta_hoje = 0.0
        cap_meta_eoy = 0.0

    df_obj = df_obj.copy()
    # Converter coluna Objetivo para numérico se necessário
    if "Objetivo" in df_obj.columns:
        df_obj["Objetivo"] = pd.to_numeric(df_obj["Objetivo"], errors="coerce")
    
    objetivo_anual = 0.0
    if "Cap. Liq Objetivo" in df_obj.columns and not df_obj.empty:
        obj_ano = df_obj[df_obj["Objetivo"] == ano_atual]
        objetivo_anual = (
            float(obj_ano["Cap. Liq Objetivo"].max())
            if not obj_ano.empty
            else float(df_obj["Cap. Liq Objetivo"].max())
        )

    valor_alcancado_ano = capliq_ano_atual
    mes_atual = hoje.month
    obj_restante_ano = max(0.0, (objetivo_anual or 0.0) - valor_alcancado_ano)
    meses_restantes = max(1, 12 - mes_atual + 1)
    obj_capliq_mes_max = obj_restante_ano / meses_restantes

    auc_meta_eoy = 0.0
    auc_meta_hoje = 0.0
    try:
        df_pj1 = carregar_dados_objetivos_pj1()
        if not df_pj1.empty and "Objetivo" in df_pj1.columns:
            base_auc = df_pj1[df_pj1["Objetivo"] == ano_atual].copy()
            if not base_auc.empty:
                # Usar diretamente o valor anual de AUC Objetivo
                if "AUC Objetivo" in base_auc.columns:
                    auc_meta_eoy = float(base_auc["AUC Objetivo"].max())
                    # Para meta até hoje, usar proporção do ano
                    dias_decorridos = (hoje - pd.Timestamp(ano_atual, 1, 1)).days + 1
                    total_dias_ano = 366 if pd.Timestamp(ano_atual, 12, 31).dayofyear == 366 else 365
                    auc_meta_hoje = (auc_meta_eoy * dias_decorridos) / total_dias_ano
    except Exception:
        pass

    auc_atual = 0.0
    if (mesref_pos is not None) and {"Data_Posicao", "Net_Em_M"} <= set(df_pos.columns):
        mask_mesrec = df_pos["Data_Posicao"].dt.to_period("M") == mesref_pos
        auc_atual = float(df_pos.loc[mask_mesrec, "Net_Em_M"].sum())

    return {
        "capliq_mes": {
            "valor": capliq_mes_atual,
            "max": obj_capliq_mes_max,
            "pace_target": (obj_capliq_mes_max * pace_mes)
            if (pace_mes is not None and obj_capliq_mes_max is not None)
            else None,
            "mesref": str(mesref_pos) if mesref_pos is not None else "-",
        },
        "capliq_ano": {
            "valor": capliq_ano_atual,
            "max": cap_meta_eoy,
            "pace_target": cap_meta_hoje,
            "ano": ano_atual,
        },
        "auc": {
            "valor": auc_atual,
            "max": auc_meta_eoy,
            "pace_target": auc_meta_hoje,
            "mesref": str(mesref_pos) if mesref_pos is not None else "-",
        },
    }


# ---------------------------------------------------------------------
# Lógica auxiliar (NPS / RV)
# ---------------------------------------------------------------------
def _count_clientes_pos_netpos(df_pos: pd.DataFrame, periodM: pd.Period) -> int:
    if df_pos.empty:
        return 0
    date_col = None
    for cand in ["Data_Posicao", "Data_Atualizacao", "Data_Cadastro", "__data_pos__"]:
        if cand in df_pos.columns:
            date_col = cand
            break
    if not date_col:
        return 0
    aux = df_pos.copy()
    aux["ym"] = pd.to_datetime(aux[date_col], errors="coerce").dt.to_period("M")
    m = aux["ym"] == periodM
    aux = aux.loc[m].copy()
    return int(aux.loc[aux["Net_Em_M"].fillna(0) > 0, "Cliente"].astype(str).nunique())


def _latest_common_period(df_pos: pd.DataFrame, df_auc: pd.DataFrame) -> Optional[pd.Period]:
    """
    Tenta encontrar a última competência comum.
    Se não encontrar, retorna a última competência do AUC (fallback).
    """
    if df_auc.empty or "data_parsed" not in df_auc.columns:
        return None

    m_auc_periods = pd.to_datetime(df_auc["data_parsed"], errors="coerce").dt.to_period("M").dropna()
    if m_auc_periods.empty:
        return None

    unique_auc = set(m_auc_periods.astype(str).unique())

    if not df_pos.empty and "Data_Posicao" in df_pos.columns:
        m_pos_periods = pd.to_datetime(df_pos["Data_Posicao"], errors="coerce").dt.to_period("M").dropna()
        m_pos = set(m_pos_periods.astype(str).unique())

        inter = sorted(unique_auc & m_pos)
        if inter:
            return pd.Period(inter[-1])

    return m_auc_periods.max()


# ---------------------------------------------------------------------
# Render Helpers
# ---------------------------------------------------------------------
def obter_auc_inicial_ano(df: pd.DataFrame, ano: int) -> float:
    """
    Retorna o AUC inicial de um determinado ano, usando a primeira Data_Posicao desse ano.
    Soma o Net_Em_M dessa data.
    """
    if df is None or df.empty:
        return 0.0
    if 'Data_Posicao' not in df.columns or 'Net_Em_M' not in df.columns:
        return 0.0

    aux = df.copy()
    aux['Data_Posicao'] = pd.to_datetime(aux['Data_Posicao'], errors='coerce')
    aux = aux[aux['Data_Posicao'].dt.year == ano]
    if aux.empty:
        return 0.0

    primeira_data = aux['Data_Posicao'].min()
    auc_inicial = float(aux.loc[aux['Data_Posicao'] == primeira_data, 'Net_Em_M'].sum() or 0.0)
    return auc_inicial


# AUC base de janeiro/2025 para uso nas barras de progresso
AUC_BASE_2025 = obter_auc_inicial_ano(df_positivador, 2025) if 'df_positivador' in globals() else 0.0


def render_custom_progress_bars(
    objetivo_hoje_val: float, realizado_val: float, max_val: float, min_val: float = 0
) -> None:
    """
    Renderiza as duas barras de progresso (Projetado e Realizado),
    permitindo que o mínimo da escala seja diferente de zero.
    """
    objetivo_hoje_raw = float(objetivo_hoje_val or 0.0)
    realizado_raw = float(realizado_val or 0.0)
    min_val = float(min_val or 0.0)
    max_val = float(max_val or 0.0)

    # Garante range mínimo
    if max_val <= min_val:
        max_val = min_val + 1.0

    range_val = max(max_val - min_val, 0.01)

    # Valores usados para a largura das barras (normalizados na escala [min_val, max_val])
    objetivo_plot = min(max(objetivo_hoje_raw - min_val, 0.0), range_val)
    realizado_plot = min(max(realizado_raw - min_val, 0.0), range_val)

    projetado_pct = (objetivo_plot / range_val) * 100.0
    realizado_pct = (realizado_plot / range_val) * 100.0

    fmt_min = formatar_valor_curto(min_val)
    fmt_max = formatar_valor_curto(max_val)
    fmt_projetado = formatar_valor_curto(objetivo_hoje_raw) if objetivo_hoje_raw > 0 else ""
    
    # NOVA REGRA: mostrar negativos, esconder apenas zero
    if realizado_raw != 0:
        fmt_realizado = formatar_valor_curto(realizado_raw)
    else:
        fmt_realizado = ""

    html_bars = f"""
<div class="progress-wrapper">
  <div class="progress-container">
    <div class="progress-label" style="font-weight: bold;">PROJETADO</div>
    <div class="progress-bar-track">
      <div class="progress-bar-fill" style="width: {projetado_pct:.2f}%;"></div>
      <span class="progress-bar-limit-label right">{fmt_max}</span>
      <span class="progress-bar-value-label">{fmt_projetado}</span>
    </div>
  </div>

  <div class="progress-container">
    <div class="progress-label" style="font-weight: bold;">REALIZADO</div>
    <div class="progress-bar-track">
      <div class="progress-bar-fill" style="width: {realizado_pct:.2f}%;"></div>
      <span class="progress-bar-limit-label right">{fmt_max}</span>
      <span class="progress-bar-value-label">{fmt_realizado}</span>
    </div>
  </div>
</div>
"""
    st.markdown(dedent(html_bars), unsafe_allow_html=True)


def top3_mes_cap(
    df: pd.DataFrame,
    date_col: str = "Data_Posicao",
    value_col: str = "Captacao_Liquida_em_M",
    group_col: str = "assessor_code",
) -> Tuple[List[Tuple[str, float]], str]:
    """
    Retorna Top 3 por 'group_col' no ÚLTIMO mês com valor != 0.
    """
    req = {date_col, value_col}
    if date_col not in df.columns:
        return [], "-"

    if group_col not in df.columns:
        if "assessor" in df.columns:
            group_col = "assessor"
        else:
            return [], "-"

    req.add(group_col)

    if not req <= set(df.columns):
        return [], "-"

    dfx = df[list(req)].copy()
    dfx[date_col] = pd.to_datetime(dfx[date_col], errors="coerce")
    dfx[value_col] = pd.to_numeric(dfx[value_col], errors="coerce").fillna(0)

    dfx[group_col] = dfx[group_col].astype(str).str.strip()
    gnorm = dfx[group_col].str.upper()

    invalid = gnorm.isin(["", "NONE", "NENHUM", "NA", "N/A", "NULL", "-", "NAN"])
    dfx = dfx[~invalid]

    dfx = dfx[dfx[value_col] != 0]

    if dfx.empty:
        return [], "-"

    per_valid = dfx[date_col].dt.to_period("M").dropna()
    if per_valid.empty:
        return [], "-"

    mesref = per_valid.max()
    dmes = dfx[dfx[date_col].dt.to_period("M") == mesref]
    if dmes.empty:
        return [], str(mesref)

    serie = dmes.groupby(group_col)[value_col].sum().sort_values(ascending=False)

    return list(serie.items())[:5], str(mesref)


def top3_ano_cap(
    df: pd.DataFrame,
    date_col: str = "Data_Posicao",
    value_col: str = "Captacao_Liquida_em_M",
    group_col: str = "assessor_code",
) -> Tuple[List[Tuple[str, float]], str]:
    """
    Retorna Top 3 por 'group_col' no ÚLTIMO ano com valor != 0.
    """
    req = {date_col, value_col}
    if date_col not in df.columns:
        return [], "-"

    if group_col not in df.columns:
        if "assessor" in df.columns:
            group_col = "assessor"
        else:
            return [], "-"

    req.add(group_col)
    if not req <= set(df.columns):
        return [], "-"

    dfx = df[list(req)].copy()
    dfx[date_col] = pd.to_datetime(dfx[date_col], errors="coerce")
    dfx[value_col] = pd.to_numeric(dfx[value_col], errors="coerce").fillna(0)

    dfx[group_col] = dfx[group_col].astype(str).str.strip()
    gnorm = dfx[group_col].str.upper()
    invalid = gnorm.isin(["", "NONE", "NENHUM", "NA", "N/A", "NULL", "-", "NAN"])
    dfx = dfx[~invalid]

    dfx = dfx[dfx[value_col] != 0]

    if dfx.empty:
        return [], "-"

    anos = dfx[date_col].dt.year.dropna().astype(int).unique()
    if len(anos) == 0:
        return [], "-"

    ano = int(sorted(anos)[-1])
    dane = dfx[dfx[date_col].dt.year == ano]
    if dane.empty:
        return [], str(ano)

    serie = dane.groupby(group_col)[value_col].sum().sort_values(ascending=False)

    return list(serie.items())[:5], str(ano)


def _render_top3_horizontal(items: List[Tuple[str, float]], header_text: str) -> None:
    """
    Renderiza bloco Top 3 em formato VERTICAL (3 linhas),
    com medalhas e nomes dos assessores empilhados.
    """
    if not items:
        st.markdown(
            "<div class='table-container'><p style='padding:12px'>Sem dados.</p></div>",
            unsafe_allow_html=True,
        )
        return

    top3 = items[:3]
    nomes_curto = []
    for ass, _ in top3:
        full = obter_nome_assessor(ass) if ass else "-"
        nomes_curto.append(_primeiro_nome_sobrenome(full))

    css = """
    <style>
      .top3-h-wrap {
        border: 1.8px solid rgba(46, 204, 113, 0.85);
        border-radius: 14px;
        background: linear-gradient(180deg, rgba(46,204,113,0.15) 0%, rgba(46,204,113,0.06) 100%);
        padding: 10px 14px 8px 14px;
        max-width: var(--tv-block-width, 680px);
        width: 100%;
        margin: 6px auto 0 auto;
        box-shadow: 0 3px 10px rgba(0,0,0,0.22);
      }
      .top3-h-title {
        text-align: center;
        font-weight: 800;
        color: #fff;
        margin: 0 0 6px 0;
        letter-spacing: 0.4px;
        font-size: 1.05em;
      }
      .top3-v-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .top3-v-item {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 6px 10px;
        border-radius: 10px;
        font-weight: 800;
        color: #ffffff;
        font-size: 0.88em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        text-align: center;
        min-height: 32px;
      }
      .top3-v-medal {
        width:30px;
        flex-shrink:0;
        text-align:right;
        margin-right: 5px;
      }
      .top3-v-name {
        flex:1;
        text-align:center;
        padding-left: 0;
        margin-left: -20px;
      }
      .top3-v-item.pos-1 {
        background: linear-gradient(135deg, rgba(255,213,79,.15), rgba(46,204,113,.03));
      }
      .top3-v-item.pos-2 {
        background: linear-gradient(135deg, rgba(207,216,220,.15), rgba(46,204,113,.03));
      }
      .top3-v-item.pos-3 {
        background: linear-gradient(135deg, rgba(255,171,145,.15), rgba(46,204,113,.03));
      }
    </style>
    """

    rows_html = []
    medals = ["🥇", "🥈", "🥉"]
    for i, nome in enumerate(nomes_curto, start=1):
        medal = medals[i - 1]
        rows_html.append(
            f"<div class='top3-v-item pos-{i}'>"
            f"<span class='top3-v-medal'>{medal} {i}</span>"
            f"<span class='top3-v-name'>{nome}</span>"
            f"</div>"
        )

    html = f"""
    {css}
    <div class="top3-h-wrap">
      <div class="top3-h-title">{header_text}</div>
      <div class="top3-v-list">
        {''.join(rows_html)}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def _filtrar_por_pesquisa(df_nps: pd.DataFrame, token_exato: str) -> pd.DataFrame:
    if df_nps.empty:
        return pd.DataFrame()
    if "pesquisa_relacionamento" not in df_nps.columns and "pesquisa_relacionamento_norm" not in df_nps.columns:
        st.warning("Coluna 'Pesquisa Relacionamento' não encontrada no NPS.")
        return pd.DataFrame()

    token_norm = _strip_accents(token_exato).upper().strip()
    col_norm = "pesquisa_relacionamento_norm"
    if col_norm not in df_nps.columns and "pesquisa_relacionamento" in df_nps.columns:
        df_nps[col_norm] = _norm_upper_noaccents_series(df_nps["pesquisa_relacionamento"])

    return df_nps[df_nps[col_norm] == token_norm].copy()


def _calcular_metricas_nps(df_sub: pd.DataFrame) -> Dict[str, float]:
    total = int(df_sub.shape[0]) if not df_sub.empty else 0
    if total == 0:
        return {
            "total": 0,
            "respondidos": 0,
            "aderencia": 0.0,
            "media": 0.0,
            "nps": 0.0,
            "promotores": 0,
            "neutros": 0,
            "detratores": 0,
        }

    s = pd.to_numeric(df_sub.get("nota"), errors="coerce")
    valid = s.between(0, 10, inclusive="both")
    den = int(valid.sum())

    prom = int(((s >= 9) & (s <= 10) & valid).sum())
    detr = int(((s >= 0) & (s <= 6) & valid).sum())
    neut = int(((s >= 7) & (s <= 8) & valid).sum())

    aderencia = (den / total) * 100.0 if total > 0 else 0.0
    media = float(s[valid].mean()) if den > 0 else 0.0
    nps = 100.0 * (prom / den - detr / den) if den > 0 else 0.0

    return {
        "total": total,
        "respondidos": den,
        "aderencia": aderencia,
        "media": media,
        "nps": nps,
        "promotores": prom,
        "neutros": neut,
        "detratores": detr,
    }


def _top3_assessores_por_aderencia(df_sub: pd.DataFrame) -> pd.DataFrame:
    # Check for required columns (handle different possible column names)
    assessor_col = next((col for col in ["codigo_assessor", "assessor_code", "assessor"] if col in df_sub.columns), None)
    nota_col = next((col for col in ["nota", "rating", "score"] if col in df_sub.columns), None)
    
    if df_sub.empty or not assessor_col or not nota_col:
        return pd.DataFrame(columns=["ASSESSOR", "ADERENCIA", "RESPOSTAS"])

    df = df_sub.copy()
    s_nota = pd.to_numeric(df[nota_col], errors="coerce")
    df["_valid"] = s_nota.between(0, 10, inclusive="both")
    total_validos = float(df["_valid"].sum())

    agg = (
        df[df["_valid"]]
        .groupby(assessor_col)
        .agg(total_respostas=(nota_col, "size"), respondidos=("_valid", "sum"))
        .reset_index()
    )

    agg["share"] = (agg["respondidos"] / total_validos * 100.0) if total_validos > 0 else 0.0
    agg = agg.sort_values(["respondidos", "share"], ascending=[False, False]).head(3)

    # Aqui mantemos ADERENCIA numérica (em %), sem formatar como string
    out = agg[[assessor_col, "share", "respondidos"]].rename(
        columns={
            assessor_col: "ASSESSOR",
            "respondidos": "RESPOSTAS",
            "share": "ADERENCIA",
        }
    )
    return out[["ASSESSOR", "ADERENCIA", "RESPOSTAS"]]


def render_top3_assessores_aderencia_table(df_top: pd.DataFrame, header_text: str) -> None:
    if df_top is None or df_top.empty:
        st.markdown(
            "<div class='table-container'><p style='padding:12px'>Sem dados.</p></div>",
            unsafe_allow_html=True,
        )
        return

    rows = []
    for idx, row in enumerate(df_top.itertuples(index=False), 1):
        cod = str(getattr(row, "ASSESSOR", "") or "")
        nome = obter_nome_assessor(cod)
        part_total = str(getattr(row, "ADERENCIA", "") or "")
        respostas = str(getattr(row, "RESPOSTAS", "0") or "0")
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else ""
        rows.append(
            "<tr class='ranking-row rank-pos-{0}'>"
            "<td style='text-align:center; padding: 8px 4px; vertical-align: middle; font-weight: 700; font-size: 1.05em; color: #f0f0f0;'>{1} {2}</td>"
            "<td style='text-align:center; padding: 8px 4px; vertical-align: middle; font-weight: 700;'>{3}</td>"
            "<td style='text-align:center; padding: 8px 4px; vertical-align: middle; font-weight: 700; color:#b8f7d4;'>{5}</td>"
            "<td style='text-align:center; padding: 8px 4px; vertical-align: middle; font-weight: 700;'>{4}</td>"
            "</tr>".format(idx, medal, idx, nome, respostas, part_total)
        )

    if not rows:
        st.markdown(
            "<div class='table-container'><p style='padding:12px'>Sem dados.</p></div>",
            unsafe_allow_html=True,
        )
        return

    rows_html = "\n".join(rows)
    table_html = (
        f"<div class='table-container'>"
        f"<h3 class='nps-table-title' style='text-align: center; color: white; font-weight: 800; margin: 0 0 22px 0; font-size: 0.85em;'>{header_text.upper()}</h3>"
        f"<table class='ranking-table'><thead><tr>"
        f"<th style='text-align:center; width: 50px;'>#</th>"
        f"<th style='text-align:center;'>ASSESSOR</th>"
        f"<th style='text-align:center; width: 60px;'>ADERÊNCIA</th>"
        f"<th style='text-align:center; width: 80px;'>RESPOSTAS</th>"
        f"</tr></thead><tbody>"
        f"{rows_html}"
        f"</tbody></table></div>"
    )

    st.markdown(table_html, unsafe_allow_html=True)


def top3_assessores_por_pl(df_auc_snapshot: pd.DataFrame) -> List[Tuple[str, Tuple[float, int]]]:
    if df_auc_snapshot is None or df_auc_snapshot.empty:
        return []
    if not {"assessor", "auc_reais", "cliente"} <= set(df_auc_snapshot.columns):
        return []

    d = df_auc_snapshot.copy()
    d["assessor"] = d["assessor"].astype(str).str.strip()

    grouped = (
        d.groupby("assessor")
        .agg({"auc_reais": "sum", "cliente": "nunique"})
        .sort_values("auc_reais", ascending=False)
        .head(3)
    )
    return [(idx, (row["auc_reais"], row["cliente"])) for idx, row in grouped.iterrows()]


def render_ranking_table_pl(items: List[Tuple[str, Tuple[float, int]]], header_text: str) -> str:
    if not items:
        return (
            f'<div class="table-container">'
            f'<h3 class="nps-table-title" style="text-align: center; color: white; font-weight: 800; margin: 0 0 8px 0; font-size: 0.85em;">{header_text.upper()}</h3>'
            '<div style="padding: 12px; text-align: center; color: #aaa;">Sem dados</div>'
            "</div>"
        )

    rows = []
    for idx, (assessor, (_, qtd_clientes)) in enumerate(items, 1):
        nome = obter_nome_assessor(assessor) if assessor else "-"
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else ""

        rows.append(
            "<tr class='ranking-row rank-pos-{0}'>"
            "<td style='text-align:center; padding: 6px 4px; vertical-align: middle; font-weight: 700; font-size: 1.05em; color: #f0f0f0;'>{1} {2}</td>"
            "<td style='text-align:center; padding: 6px 4px; vertical-align: middle; font-weight: 700;'>{3}</td>"
            "<td style='text-align:center; padding: 6px 4px; vertical-align: middle; font-weight: 700; color:#b8f7d4;'>{4}</td>"
            "</tr>".format(idx, medal, idx, nome, int(qtd_clientes))
        )

    rows_html = "\n".join(rows)

    table_html = (
        f"<div class='table-container'>"
        f"<h3 class='nps-table-title' style='text-align: center; color: white; font-weight: 800; margin: 0 0 8px 0; font-size: 0.85em;'>{header_text.upper()}</h3>"
        f"<table class='ranking-table'><thead><tr>"
        f"<th style='text-align:center; width: 50px;'>#</th>"
        f"<th style='text-align:center;'>ASSESSOR</th>"
        f"<th style='text-align:center; width: 60px;'>Clientes</th>"
        f"</tr></thead><tbody>"
        f"{rows_html}"
        f"</tbody></table></div>"
    )
    return table_html


# ---------------------------------------------------------------------
# Execução Principal - Seção TV (Captação / AUC / Rumo a 1BI)
# ---------------------------------------------------------------------
with st.spinner("Carregando dados..."):
    try:
        df_pos = carregar_dados_positivador_mtd()
        df_pos = tratar_dados_positivador_mtd(df_pos)
        df_obj = carregar_dados_objetivos()
    except Exception as e:
        st.error(f"Erro ao carregar bases de Objetivos/Positivador: {e}")
        st.stop()

if df_pos.empty or df_obj.empty:
    st.warning("Sem dados suficientes em Positivador ou Objetivos.")
    st.stop()

df_pos_f = df_pos.copy()

# -----------------------------------------------------------------
# NOVA REGRA DE DATA DE REFERÊNCIA:
# Sempre usar a data de atualização do DBV Capital_Positivador.db
# -----------------------------------------------------------------
data_atualizacao_bd = obter_data_atualizacao_positivador()
data_ref = pd.Timestamp(data_atualizacao_bd).normalize()
data_formatada = data_ref.strftime("%d/%m/%Y")

# (Opcional) se quiser ainda saber a última Data_Posicao da base:
# data_ultima_posicao = ultima_data(df_pos_f, date_col="Data_Posicao")

# Toda a lógica de objetivos (captação / AUC / Rumo a 1BI)
# passa a usar essa data_ref como "hoje"
mets = calcular_indicadores_objetivos(df_pos_f, df_obj, hoje=data_ref)

# --- Preparação NPS (para usar na Coluna 3) ---
try:
    df_nps_all = carregar_dados_nps()
    dfx = _filtrar_por_pesquisa(df_nps_all, token_exato="XP Aniversário")
    if not dfx.empty:
        m_nps = _calcular_metricas_nps(dfx)
        top3_df = _top3_assessores_por_aderencia(dfx)
    else:
        m_nps = {
            "total": 0,
            "aderencia": 0.0,
            "nps": 0.0,
            "detratores": 0,
            "neutros": 0,
            "promotores": 0,
        }
        top3_df = pd.DataFrame()
except Exception as e:
    st.error(f"Erro ao processar dados NPS: {e}")
    m_nps = {
        "total": 0,
        "aderencia": 0.0,
        "nps": 0.0,
        "detratores": 0,
        "neutros": 0,
        "promotores": 0,
    }
    top3_df = pd.DataFrame()
    dfx = pd.DataFrame()

# =====================================================
# SEÇÃO 1 – PAINEL TV (LAYOUT 3 COLUNAS)
# =====================================================
# Add global CSS for layout
st.markdown(
    """
    <style>
        :root {
            --radius: 20px;
            --border-width: 1px;
            --border-color: #d1d9d5;
            --tv-block-width: 720px;
            --page-bg: #E8EFE9;
            /* Escala do painel TV para caber 100% na tela */
            --tv-scale: 0.90;
            /* Ajuste este valor para controlar o zoom do painel */
        }

        html, body,
        [data-testid="stAppViewContainer"],
        .stApp,
        .main {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        .dbv-dashboard-root {
            position: relative;
            width: 100%;
            max-width: 100%;
            margin: 0 auto;
            padding-bottom: 0;  /* Removido o padding inferior */
            display: flex;
            flex-direction: column;
            gap: 18px;  /* Aumentado o espaçamento entre os elementos */
        }
        
        /* Escala do painel de TV (título + gráfico + NPS + cards) para caber na tela sem scroll */
        div[data-testid="stVerticalBlock"]:has(.painel-tv-sentinel) {
            transform: scale(var(--tv-scale, 0.82));  /* mantém o zoom atual */
            transform-origin: top center;
            margin: -10px auto 20px auto !important;  /* margens ajustadas para criar espaço abaixo */
            width: 100% !important;
        }
        
        /* Ajustes de altura para os elementos principais */
        .dashboard-card.nps-card {
            height: 380px !important;
            min-height: 380px !important;
            max-height: 380px !important;
            margin-top: 0 !important;
        }

        .stPlotlyChart {
            height: 380px !important;
            min-height: 380px !important;
            max-height: 380px !important;
            box-sizing: border-box !important;
            overflow: visible !important;   /* igual ao passo anterior */
            margin-top: 0 !important;       /* sem deslocar o card em relação ao NPS */
        }
        
        .tv-metric-grid {
            height: 120px !important;
            min-height: 120px !important;
            margin-bottom: 0px !important;
        }
        
        /* Aumentar fonte das tabelas */
        .ranking-table {
            font-size: 1.05em !important;
        }
        
        .ranking-table th {
            font-size: 0.95em !important;
            padding: 6px 4px !important;
        }
        
        .ranking-table td {
            padding: 6px 4px !important;
        }
        
        .gradient-text {
            background: linear-gradient(90deg, #ffffff, #e0e0e0, #ffffff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-fill-color: transparent;
            display: inline-block;
            margin: 0;
            line-height: 1;
        }
    </style>
    """,
    unsafe_allow_html=True
)

with st.container():
    # Main dashboard wrapper
    st.markdown("<div class='dbv-dashboard-root'>", unsafe_allow_html=True)
    
    # Header with title and date
    header_html = """
    <div style='text-align: center; margin: 0 auto; width: 100%; max-width: 500px; padding: 0 0 2px 0;'>
        <h1 class='gradient-text' style='font-size: 36px; font-weight: 900; letter-spacing: 2px; margin: 0; padding: 2px 0; text-shadow: 1px 1px 3px rgba(0,0,0,0.3);'>DBV CAPITAL</h1>
        <div style='margin: 2px 0 8px 0; text-align: center;'>
            <span style='font-size: 0.80rem; color: #2ecc71; font-weight: 500; display: inline-block;'>
                Atualizado em: <strong>__DATA_ATUALIZACAO__</strong>
            </span>
        </div>
    </div>
    """
    st.markdown(
        header_html.replace("__DATA_ATUALIZACAO__", data_formatada),
        unsafe_allow_html=True
    )
    st.markdown("<div class='painel-tv-sentinel'></div>", unsafe_allow_html=True)
    
    # =====================================================
# SEÇÃO SUPERIOR: GRÁFICO + NPS
# =====================================================
col_upper_left, _, col_upper_right = st.columns([20, 1, 10], gap="small")

# Coluna esquerda superior (2/3): Gráfico de Crescimento AUC e Clientes Ativos
with col_upper_left:
    # Gráfico 1: Crescimento AUC e Clientes Ativos
    if not df_positivador.empty:
        # Preparar dados mensais
        df_positivador['ano_mes'] = df_positivador['Data_Posicao'].dt.strftime('%Y-%m')
        
        # Calcular AUC mensal (Net_Em_M somado por mês)
        df_auc_mensal = df_positivador.groupby('ano_mes')['Net_Em_M'].sum().reset_index()
        
        # Calcular quantidade de clientes com AUC > 0 por mês
        df_clientes_positivo = (
            df_positivador[df_positivador['Net_Em_M'] > 0]
            .groupby('ano_mes')
            .size()
            .reset_index(name='clientes_positivo')
        )
        
        # Juntar dados de AUC e Clientes Ativos
        df_growth_auc = pd.merge(
            df_auc_mensal,
            df_clientes_positivo,
            on='ano_mes',
            how='outer'
        ).fillna(0)
        
        # Converter para data e ordenar
        df_growth_auc['data'] = pd.to_datetime(df_growth_auc['ano_mes'] + '-01')
        df_growth_auc = df_growth_auc.sort_values('data')
        
        # --------- ESCALA DO EIXO EM MILHÕES (Y2) -----------
        min_auc = float(df_growth_auc['Net_Em_M'].min() or 0.0)
        max_auc = float(df_growth_auc['Net_Em_M'].max() or 0.0)

        # Garantir que max_auc seja maior que min_auc
        if max_auc <= min_auc:
            max_auc = min_auc + 50_000_000

        # "encaixa" a escala em múltiplos de 50M
        nice_min = math.floor(min_auc / 50_000_000.0) * 50_000_000.0
        nice_max = math.ceil(max_auc / 50_000_000.0) * 50_000_000.0

        # Pequena folga no topo para o último ponto não colar no limite
        nice_max = max(nice_max, max_auc * 1.05)

        # Ticks do eixo (valores reais em R$) e textos em milhões (300M, 350M, 400M, etc.)
        dtick_val = 50_000_000
        tick_vals = list(np.arange(nice_min, nice_max + dtick_val, dtick_val))
        tick_text = [f"R$ {int(v / 1_000_000)}M" for v in tick_vals]
        # ---------------------------------------------------

        # Criar figura com eixo secundário
        fig_growth_auc = go.Figure()
        
        # Barras: quantidade de clientes ativos (AUC > 0)
        fig_growth_auc.add_trace(
            go.Bar(
                x=df_growth_auc['ano_mes'],
                y=df_growth_auc['clientes_positivo'],
                name='Clientes Ativos',
                marker_color='#948161',
                opacity=0.9,
                hovertemplate='<b>%{x}</b><br>Clientes Ativos: %{y:,.0f}<extra></extra>'
            )
        )
        
        # Linha: AUC (Net_Em_M)
        fig_growth_auc.add_trace(
            go.Scatter(
                x=df_growth_auc['ano_mes'],
                y=df_growth_auc['Net_Em_M'],
                name='AUC',
                line=dict(color='#FFFFFF', width=2),
                yaxis='y2',
                mode='lines+markers',
                hovertemplate='<b>%{x}</b><br>AUC: R$ %{y:,.2f}<extra></extra>'
            )
        )
        
        # Layout do gráfico
        fig_growth_auc.update_layout(
            # Ajuste fino da altura para caber dentro do card de 380px
            height=330,  # ligeiramente menor para caber sem cortar a borda
            # Ajuste fino das margens
            margin=dict(l=20, r=20, t=15, b=15),  # reduzido topo e base para 15px
            title=dict(
                text='<b>CRESCIMENTO AUC E CLIENTES ATIVOS</b>',
                font=dict(size=14, color='white'),
                x=0.02,
                y=0.98,
                xanchor='left',
                yanchor='top'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=False,
                showline=True,
                linecolor='rgba(255, 255, 255, 0.2)',
                tickfont=dict(color='white', size=10),
                title=None
            ),
            yaxis=dict(
                title='Clientes Ativos',
                title_font=dict(color='#948161'),
                tickfont=dict(color='#948161'),
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.1)',
                gridwidth=0.5,
                showline=True,
                linecolor='rgba(255, 255, 255, 0.2)',
                zeroline=False
            ),
            yaxis2=dict(
                title=None,
                overlaying='y',
                side='right',
                tickfont=dict(color='white', size=10),
                showline=True,
                linecolor='rgba(255, 255, 255, 0.2)',
                gridcolor='rgba(255, 255, 255, 0.1)',
                gridwidth=0.5,
                tickmode='array',
                tickvals=tick_vals,
                ticktext=tick_text,
                range=[nice_min, nice_max],
                zeroline=False
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(color='white', size=11),
                bgcolor='rgba(0,0,0,0.2)',
                bordercolor='rgba(255, 255, 255, 0.2)'
            ),
            hoverlabel=dict(
                font_size=12,
                font_family="Arial",
                font_color='white',
                bgcolor='rgba(32, 53, 47, 0.9)',
                bordercolor='rgba(255, 255, 255, 0.2)'
            )
        )
        
        # Exibir gráfico ocupando 2/3 da tela
        st.plotly_chart(fig_growth_auc, use_container_width=True)
    else:
        st.warning("Dados insuficientes para exibir o gráfico de Crescimento AUC e Clientes Ativos.")

# Coluna direita superior (1/3): NPS
with col_upper_right:
    if not dfx.empty:
        nps_color = "#ffffff"

        # Monta HTML da tabela Top 3 dentro do mesmo card,
        # usando o mesmo layout vertical dos Top 3 das colunas inferiores
        if not top3_df.empty:
            medals = ["🥇", "🥈", "🥉"]
            row_divs = []
            for idx, row in enumerate(top3_df.itertuples(index=False), start=1):
                cod = str(getattr(row, "ASSESSOR", "") or "")
                nome = obter_nome_assessor(cod)
                medal = medals[idx - 1] if idx <= len(medals) else ""
                row_divs.append(
                    f"<div class='top3-v-item pos-{idx}'>"
                    f"<span class='top3-v-medal'>{medal} {idx}</span>"
                    f"<span class='top3-v-name'>{nome}</span>"
                    f"</div>"
                )

            css_top3_nps = """
<style>
  .top3-h-wrap {
    border: 1px solid rgba(46, 204, 113, 0.5) !important;
    border-radius: 10px !important;
    background: linear-gradient(180deg, rgba(46,204,113,0.12) 0%, rgba(46,204,113,0.04) 100%) !important;
    padding: 6px 8px 8px 8px !important;
    width: 90% !important;
    margin: 0 auto 6px auto !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15) !important;
  }
  .top3-h-title {
    text-align:center;
    font-weight:800;
    color:#fff;
    margin:0 0 3px 0 !important;
    letter-spacing:0.2px;
    font-size: 0.82em !important;
    line-height: 1.3 !important;
  }
  .top3-v-list {
    display:flex;
    flex-direction:column;
    gap:2px !important;
  }
  .top3-v-item {
    display:flex;
    align-items:center;
    justify-content:flex-start;
    padding:3px 8px !important;
    border-radius:6px !important;
    font-weight:700;
    color:#ffffff;
    font-size:0.78em !important;
    line-height: 1.4 !important;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
  }
  .top3-v-medal {
    width:40px;
    flex-shrink:0;
    text-align:left;
  }
  .top3-v-name {
    flex:1;
    text-align:left;
  }
  .top3-v-item.pos-1 {
    background: linear-gradient(135deg, rgba(255,213,79,.15), rgba(46,204,113,.03));
  }
  .top3-v-item.pos-2 {
    background: linear-gradient(135deg, rgba(207,216,220,.15), rgba(46,204,113,.03));
  }
  .top3-v-item.pos-3 {
    background: linear-gradient(135deg, rgba(255,171,145,.15), rgba(46,204,113,.03));
  }
</style>
"""
            rows_html = "".join(row_divs)
            top3_block_html = css_top3_nps + f"""
<div class="top3-h-wrap">
  <div class="top3-h-title">Top 3 — Aderência por Assessor - NPS</div>
  <div class="top3-v-list">
    {rows_html}
  </div>
</div>
"""
        else:
            top3_block_html = """
<div style="margin-top: 16px; text-align:center; color:#aaa; font-size:0.8em;">
  Sem dados disponíveis para Top 3 de aderência.
</div>
"""

        # HTML principal do card NPS
        nps_html = f"""
<div class="dashboard-card nps-card">
  <div class="nps-card-header" style="position: relative; margin-bottom: 4px;">
    <h3 class="section-title" style="margin: 0; padding-bottom: 6px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); font-size: 15px;">NPS — XP Aniversário</h3>
    <div style="position: absolute; top: 0; right: 0; text-align: right;">
      <div style="padding: 4px 8px; background: rgba(46, 204, 113, 0.15); border-radius: 12px; font-size: 0.75em; line-height: 1.2; display: block; color: #b8f7d4; margin-bottom: 4px; width: fit-content; margin-left: auto;">
        <strong>Aderência = </strong> Respondidos / Total
      </div>
      <div style="padding: 4px 8px; background: rgba(46, 204, 113, 0.15); border-radius: 12px; font-size: 0.75em; line-height: 1.2; display: block; color: #b8f7d4; width: fit-content; margin-left: auto;">
        <strong>Período = </strong> Maio 2025 - Maio 2026
      </div>
    </div>
  </div>

  <div class="nps-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin: 4px 0;">
    <div style="background: rgba(255, 255, 255, 0.05); border-radius: 6px; padding: 2px 4px; text-align: center; display: flex; flex-direction: column; justify-content: center; min-height: 44px;">
      <div style="font-size: 0.72em; opacity: 0.8; margin-bottom: 0px; color: #2ecc71; line-height: 1.1;">Total de Envios</div>
      <div style="font-size: 1.1em; font-weight: 600; line-height: 1.0; margin-top: 0px;">{m_nps['total']}</div>
    </div>
    <div style="background: rgba(255, 255, 255, 0.1); border-radius: 6px; padding: 2px 4px; text-align: center; display: flex; flex-direction: column; justify-content: center; min-height: 44px;">
      <div style="font-size: 0.72em; opacity: 0.8; margin-bottom: 0px; line-height: 1.1;">Aderência</div>
      <div style="font-size: 1.1em; font-weight: 600; line-height: 1.0; margin-top: 0px;">{_pct_br(m_nps['aderencia'])}</div>
    </div>
    <div style="background: rgba(46, 204, 113, 0.15); border-radius: 6px; padding: 2px 4px; text-align: center; display: flex; flex-direction: column; justify-content: center; min-height: 44px;">
      <div style="font-size: 0.72em; opacity: 0.8; margin-bottom: 0px; line-height: 1.1;">NPS</div>
      <div style="font-size: 1.1em; font-weight: 700; color: {nps_color}; line-height: 1.0; margin-top: 0px;">
        {_media_br(m_nps['nps'])}
      </div>
    </div>
  </div>

  <div style="background: rgba(255, 255, 255, 0.05); border-radius: 4px; padding: 3px 6px; margin: 2px 0 6px; text-align: center; font-size: 0.7em;">
    <div style="display: flex; justify-content: space-around; gap: 4px;">
      <span style="color: #ff6b6b; white-space: nowrap;">Detratores: {m_nps['detratores']}</span>
      <span style="color: #feca57; white-space: nowrap;">Neutros: {m_nps['neutros']}</span>
      <span style="color: #1dd1a1; white-space: nowrap;">Promotores: {m_nps['promotores']}</span>
    </div>
  </div>

  {top3_block_html}
</div>
"""

        # Usa dedent para remover indentação e não virar bloco de código
        st.markdown(dedent(nps_html), unsafe_allow_html=True)

    else:
        # Card placeholder quando não há dados de NPS
        empty_html = f"""
<div class="dashboard-card nps-card" style="display: flex; align-items: center; justify-content: center; text-align: center; padding: 20px;">
  <h3 class="section-title" style="width: 100%; text-align: left; margin-bottom: 20px;">NPS — XP Aniversário</h3>
  <div style="text-align: center; color: rgba(255, 255, 255, 0.5); font-size: 0.9em;">
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="opacity: 0.5; margin-bottom: 12px;">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
    </svg>
    <div>Sem dados de NPS disponíveis</div>
  </div>
</div>
"""
        st.markdown(dedent(empty_html), unsafe_allow_html=True)

# =====================================================
# SEÇÃO INFERIOR: MÉTRICAS DE NEGÓCIO (4 COLUNAS)
# =====================================================
c1, c2, c3, c4 = st.columns(4)
# Keep backward compatibility with old variable names
col1, col2, col3, col4 = c1, c2, c3, c4

# COLUNA 1: CAPTAÇÃO LÍQUIDA MÊS
with col1:
    st.markdown(
        """
        <div class="metric-card-kpi">
            <div style='text-align: center; margin: 0; padding: 4px 0;'>
                <span style='color: white; font-weight: 900; font-size: 14px; line-height: 1.1; display: inline-block; letter-spacing: 0.3px;'>
                    CAPTAÇÃO LÍQUIDA MÊS
                </span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div class='col-tv-inner'>", unsafe_allow_html=True)

    # Valor realizado de captação no mês
    v_mes = float(mets["capliq_mes"]["valor"] or 0.0)

    # META ANUAL (MESMA DA SEÇÃO ANO)
    ano_atual = data_ref.year
    fallback_cap = 152_700_000.0 if ano_atual == 2025 else 0.0

    # Meta anual de captação (ex.: 152Mi para 2025)
    meta_anual = obter_meta_objetivo(
        ano_meta=ano_atual,
        coluna="cap_objetivo_ano",
        fallback=fallback_cap,
    )

    # Quanto já foi captado no ano (valor realizado acumulado)
    v_ano = float(mets["capliq_ano"]["valor"] or 0.0)

    # OBJETIVO DO MÊS: (Meta anual - realizado) / meses restantes
    mes_atual = data_ref.month
    obj_restante_ano = max(0.0, (meta_anual or 0.0) - v_ano)
    meses_restantes = max(1, 12 - mes_atual + 1)
    obj_total_mes = obj_restante_ano / meses_restantes

    # PROJEÇÃO DENTRO DO MÊS (DIAS ÚTEIS)
    data_atualizacao = pd.Timestamp(data_ref)
    primeiro_dia_mes = pd.Timestamp(data_atualizacao.year, data_atualizacao.month, 1)
    ultimo_dia_mes = (
        pd.Timestamp(data_atualizacao.year, data_atualizacao.month, 1)
        + pd.offsets.MonthEnd(1)
    )

    dias_uteis_mes = len(pd.bdate_range(start=primeiro_dia_mes, end=ultimo_dia_mes))
    dias_ate_atualizacao = len(
        pd.bdate_range(start=primeiro_dia_mes, end=data_atualizacao)
    )

    # Linha TEÓRICA da meta: quanto deveríamos ter até hoje
    threshold_teorico = (
        (obj_total_mes * dias_ate_atualizacao) / dias_uteis_mes if dias_uteis_mes > 0 else 0
    )
    threshold_teorico = min(threshold_teorico, obj_total_mes)

    # Projetado = linha teórica (sem colar no real)
    threshold_mes = threshold_teorico

    # Texto exibido no card "Objetivo Total"
    fmt_objetivo_total = formatar_valor_curto(obj_total_mes)
    st.markdown(
        f"""
        <div class='objetivo-card-topo'>
          <span>Objetivo Total:</span>
          <span class='valor'>{fmt_objetivo_total}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_custom_progress_bars(
        objetivo_hoje_val=threshold_mes, realizado_val=v_mes, max_val=obj_total_mes, min_val=0
    )

    restante_mes = max(0.0, obj_total_mes - v_mes)
    dias_restantes = max(0, (ultimo_dia_mes - data_atualizacao).days)
    pct_realizado_total = v_mes / obj_total_mes * 100 if obj_total_mes > 0 else 0

    # Comparação entre o REALIZADO e a linha de meta TEÓRICA
    diferenca = v_mes - threshold_teorico
    pct_diferenca = diferenca / threshold_teorico if threshold_teorico != 0 else 0
    diff_style = "color: #e74c3c;" if diferenca < 0 else ""
    border_style = (
        "border-left-color: #e74c3c !important;"
        if diferenca < 0
        else "border-left-color: var(--accent) !important;"
    )

    fmt_diferenca = formatar_valor_curto(diferenca)
    fmt_pct_val = fmt_pct(pct_diferenca).replace("%", "")
    diff_text = f"{fmt_diferenca} ({fmt_pct_val}%)"

    if restante_mes >= 1_000_000:
        val_restante = f"R$ {int(round(restante_mes / 1_000_000))}M"
    else:
        val_restante = f"R$ {int(round(restante_mes / 1_000))}K"

    cards_mes_html = f"""
    <div class="tv-metric-grid">
      <div class="metric-pill metric-pill-top"
           style="min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
        <div class="label" style="font-size: 11px;">Dias Restantes</div>
        <div class="value" style="font-size: 0.9rem;">{dias_restantes}</div>
      </div>

      <div class="metric-pill metric-pill-top"
           style="{border_style} min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
        <div class="label" style="font-size: 11px;">Projetado vs Realizado</div>
        <div class="value" style="{diff_style} font-size: 0.8rem; line-height: 1.2;">
          {diff_text}
        </div>
      </div>

      <div class="metric-pill metric-pill-top"
           style="min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
        <div class="label" style="font-size: 11px; white-space: nowrap;">
          Percentual Realizado
        </div>
        <div class="value" style="font-size: 12px; font-weight: bold;">
          {pct_realizado_total:.1f}%
        </div>
      </div>

      <div class="metric-pill metric-pill-top"
           style="min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
        <div class="label" style="font-size: 11px; white-space: nowrap;">
          Valor Restante
        </div>
        <div class="value" style="font-size: 12px; font-weight: bold;">
          <span style="color:white">{val_restante}</span>
        </div>
      </div>
    </div>
    """
    st.markdown(cards_mes_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 0px;'></div>", unsafe_allow_html=True)

    # Top 3 de CAPTAÇÃO LÍQUIDA no MÊS (última competência disponível)
    items_mes, _ = top3_mes_cap(
        df_pos_f,
        date_col="Data_Posicao",
        value_col="Captacao_Liquida_em_M",
        group_col="assessor_code",
    )
    _render_top3_horizontal(items_mes, header_text="TOP 3 - Captação Mês")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# COLUNA 2: CAPTAÇÃO LÍQUIDA ANO
with col2:
    st.markdown(
        """
        <div class="metric-card-kpi">
            <div style='text-align: center; margin: 0; padding: 4px 0;'>
                <span style='color: white; font-weight: 900; font-size: 14px; line-height: 1.1; display: inline-block; letter-spacing: 0.3px;'>
                    CAPTAÇÃO LÍQUIDA ANO
                </span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div class='col-tv-inner'>", unsafe_allow_html=True)

    v_ano_col = float(mets["capliq_ano"]["valor"] or 0.0)

    ano_atual_col = data_ref.year
    fallback_cap_col = 152_700_000.0 if ano_atual_col == 2025 else 0.0
    meta_eoy_col = obter_meta_objetivo(
        ano_meta=ano_atual_col, coluna="cap_objetivo_ano", fallback=fallback_cap_col
    )

    primeiro_dia_ano_col = pd.Timestamp(data_ref.year, 1, 1)
    ultimo_dia_ano_col = pd.Timestamp(data_ref.year, 12, 31)
    data_atualizacao_ano_col = pd.Timestamp(data_ref)
    total_dias_ano_col = (ultimo_dia_ano_col - primeiro_dia_ano_col).days + 1
    dias_ate_atualizacao_ano_col = (data_atualizacao_ano_col - primeiro_dia_ano_col).days + 1
    threshold_ano_col = (
        (meta_eoy_col * dias_ate_atualizacao_ano_col) / total_dias_ano_col
        if total_dias_ano_col > 0
        else 0.0
    )
    threshold_ano_col = min(threshold_ano_col, float(meta_eoy_col or 0.0))

    fmt_objetivo_total_ano_col = formatar_valor_curto(meta_eoy_col)
    st.markdown(
        f"""
        <div class='objetivo-card-topo'>
          <span>Objetivo Total:</span>
          <span class='valor'>{fmt_objetivo_total_ano_col}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_custom_progress_bars(
        objetivo_hoje_val=threshold_ano_col,
        realizado_val=v_ano_col,
        max_val=float(meta_eoy_col or 0.01),
        min_val=0,
    )

    restante_ano_col = max(0.0, float(meta_eoy_col or 0.0) - v_ano_col)
    dias_restantes_ano_col = max(0, (ultimo_dia_ano_col - data_atualizacao_ano_col).days)
    pct_realizado_ano_col = v_ano_col / meta_eoy_col * 100 if meta_eoy_col > 0 else 0

    diferenca_ano_col = v_ano_col - threshold_ano_col
    pct_diferenca_ano_col = (
        diferenca_ano_col / threshold_ano_col if threshold_ano_col != 0 else 0
    )
    diff_style_ano_col = "color: #e74c3c;" if diferenca_ano_col < 0 else ""
    border_style_ano_col = (
        "border-left-color: #e74c3c !important;"
        if diferenca_ano_col < 0
        else "border-left-color: var(--accent) !important;"
    )

    fmt_diferenca_ano_col = formatar_valor_curto(diferenca_ano_col)
    fmt_pct_ano_col = fmt_pct(pct_diferenca_ano_col).replace("%", "")
    diff_text_ano_col = f"{fmt_diferenca_ano_col} ({fmt_pct_ano_col}%)"

    if restante_ano_col >= 1_000_000:
        val_restante_ano_col = f"R$ {int(round(restante_ano_col / 1_000_000))}M"
    else:
        val_restante_ano_col = f"R$ {int(round(restante_ano_col / 1_000))}K"

    cards_ano_html_col = f"""
    <div class="tv-metric-grid">
      <div class="metric-pill metric-pill-top"
           style="min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
        <div class="label" style="font-size: 11px;">Dias Restantes</div>
        <div class="value" style="font-size: 0.9rem;">{dias_restantes_ano_col}</div>
      </div>

      <div class="metric-pill metric-pill-top"
           style="{border_style_ano_col} min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
        <div class="label" style="font-size: 11px;">Projetado vs Realizado</div>
        <div class="value" style="{diff_style_ano_col} font-size: 0.8rem; line-height: 1.2;">
          {diff_text_ano_col}
        </div>
      </div>

      <div class="metric-pill metric-pill-top"
           style="min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
        <div class="label" style="font-size: 11px; white-space: nowrap;">
          Percentual Realizado
        </div>
        <div class="value" style="font-size: 12px; font-weight: bold;">
          {pct_realizado_ano_col:.1f}%
        </div>
      </div>

      <div class="metric-pill metric-pill-top"
           style="min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
        <div class="label" style="font-size: 11px; white-space: nowrap;">
          Valor Restante
        </div>
        <div class="value" style="font-size: 12px; font-weight: bold;">
          <span style="color:white">{val_restante_ano_col}</span>
        </div>
      </div>
    </div>
    """
    st.markdown(cards_ano_html_col, unsafe_allow_html=True)

    st.markdown("<div style='height: 0px;'></div>", unsafe_allow_html=True)

    items_ano_col, _ = top3_ano_cap(df_pos_f)
    _render_top3_horizontal(items_ano_col, header_text="Top 3 — Captação Ano")

    st.markdown("</div>", unsafe_allow_html=True)

# COLUNA 3: AUC - 2025
with col3:
    st.markdown(
        """
        <div class="metric-card-kpi">
            <div style='text-align: center; margin: 0; padding: 4px 0;'>
                <span style='color: white; font-weight: 900; font-size: 14px; line-height: 1.1; display: inline-block; letter-spacing: 0.3px;'>
                    AUC - 2025
                </span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div class='col-tv-inner'>", unsafe_allow_html=True)

    try:
        hoje = pd.Timestamp(data_ref)
        ano_atual = hoje.year

        fallback_auc = 600_000_000.0 if ano_atual == 2025 else 0.0
        objetivo_ano_atual = obter_meta_objetivo(
            ano_meta=ano_atual, coluna="auc_objetivo_ano", fallback=fallback_auc
        )

        v_auc = arredondar_valor(float(mets["auc"]["valor"] or 0.0), 2)

        primeiro_dia_ano_auc = pd.Timestamp(ano_atual, 1, 1)
        ultimo_dia_ano_auc = pd.Timestamp(ano_atual, 12, 31)
        total_dias_ano_auc = (ultimo_dia_ano_auc - primeiro_dia_ano_auc).days + 1
        dias_decorridos = (hoje - primeiro_dia_ano_auc).days + 1
        threshold_hoje = (
            (objetivo_ano_atual * dias_decorridos) / total_dias_ano_auc
            if total_dias_ano_auc > 0
            else 0.0
        )
        threshold_hoje = min(threshold_hoje, float(objetivo_ano_atual or 0.0))
        dias_restantes_ano_auc = max(0, (ultimo_dia_ano_auc - hoje).days)
        diferenca = v_auc - threshold_hoje
        pct_diferenca = diferenca / threshold_hoje if threshold_hoje > 0 else 0
        pct_realizado = v_auc / objetivo_ano_atual * 100 if objetivo_ano_atual > 0 else 0
        restante_auc = max(0.0, float(objetivo_ano_atual or 0.0) - v_auc)

        st.markdown(
            f"""
            <div class='objetivo-card-topo'>
              <span>Objetivo Total:</span>
              <span class='valor'>{formatar_valor_curto(objetivo_ano_atual)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_custom_progress_bars(
            objetivo_hoje_val=threshold_hoje,
            realizado_val=v_auc,
            max_val=float(objetivo_ano_atual or 0.01),
            min_val=AUC_BASE_2025,
        )

        diff_style = "color: #e74c3c;" if diferenca < 0 else ""
        border_style = (
            "border-left-color: #e74c3c !important;"
            if diferenca < 0
            else "border-left-color: var(--accent) !important;"
        )
        fmt_diferenca = formatar_valor_curto(diferenca)
        fmt_pct_val = fmt_pct(pct_diferenca).replace("%", "")
        diff_text = f"{fmt_diferenca} ({fmt_pct_val}%)"

        if restante_auc >= 1_000_000:
            val_restante_auc = f"R$ {int(round(restante_auc / 1_000_000))}M"
        else:
            val_restante_auc = f"R$ {int(round(restante_auc / 1_000))}K"

        cards_auc_html = f"""
        <div class="tv-metric-grid">
          <div class="metric-pill metric-pill-top"
               style="min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
            <div class="label" style="font-size: 11px;">Dias Restantes</div>
            <div class="value" style="font-size: 0.9rem;">
              {dias_restantes_ano_auc}
            </div>
          </div>

          <div class="metric-pill metric-pill-top"
               style="{border_style} min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
            <div class="label" style="font-size: 11px;">Projetado vs Realizado</div>
            <div class="value" style="{diff_style} font-size: 0.8rem; line-height: 1.2;">
              {diff_text}
            </div>
          </div>

          <div class="metric-pill metric-pill-top"
               style="min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
            <div class="label" style="font-size: 11px; white-space: nowrap;">
              Percentual Realizado
            </div>
            <div class="value" style="font-size: 12px; font-weight: bold;">
              {pct_realizado:.1f}%
            </div>
          </div>

          <div class="metric-pill metric-pill-top"
               style="min-height: 40px; display:flex; flex-direction:column; justify-content:center;">
            <div class="label" style="font-size: 11px; white-space: nowrap;">
              Valor Restante
            </div>
            <div class="value" style="font-size: 12px; font-weight: bold;">
              <span style="color:white">{val_restante_auc}</span>
            </div>
          </div>
        </div>
        """
        st.markdown(cards_auc_html, unsafe_allow_html=True)

        st.markdown("<div style='height: 0px;'></div>", unsafe_allow_html=True)

        items_auc, _ = top3_mes_cap(df_pos_f, value_col="Net_Em_M")
        _render_top3_horizontal(items_auc, header_text="Top 3 — AUC")

    except Exception as e:
        st.error(f"Erro ao renderizar AUC: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

# COLUNA 4: Rumo a 1Bi
with col4:
    st.markdown(
        """
        <div class="metric-card-kpi">
            <div style='text-align: center; margin: 0; padding: 4px 0;'>
                <span style='color: white; font-weight: 900; font-size: 14px; line-height: 1.1; display: inline-block; letter-spacing: 0.3px;'>
                    RUMO A 1BI
                </span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div class='col-tv-inner'>", unsafe_allow_html=True)
    
    # Chama a função que renderiza o conteúdo
    # Usando AUC_BASE_2025 como valor mínimo, igual à seção AUC - 2025
    render_rumo_a_1bi(auc_base_inicial_2025=AUC_BASE_2025)
    
    # Fecha a div interna de escala
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Fecha o card principal (metric-card-kpi)
    st.markdown("</div>", unsafe_allow_html=True)

# Close the dashboard root div
st.markdown("</div>", unsafe_allow_html=True)

# A data de atualização foi movida para o painel do gráfico de crescimento AUC x Clientes Ativos

#1223