import sys
sys.path.append('.')
from pages.Dash_Salão_Atualizado import calcular_indicadores_objetivos, carregar_dados_objetivos_pj1, carregar_dados_positivador_mtd, obter_meta_objetivo
import pandas as pd
from datetime import datetime

print("=== VERIFICANDO DIFERENÇA ENTRE PROJETADOS ===\n")

# Carregar dados
df_pos = carregar_dados_positivador_mtd()
df_obj = carregar_dados_objetivos_pj1()

# Data de referência (01/12/2025)
data_ref = datetime(2025, 12, 1)

print(f"📅 Data de referência: {data_ref.strftime('%d/%m/%Y')}")

# 1. Calcular valor projetado do AUC 2025 (função calcular_indicadores_objetivos)
print(f"\n📊 AUC 2025 - calcular_indicadores_objetivos:")
mets = calcular_indicadores_objetivos(df_pos, df_obj, hoje=data_ref)
auc_projetado_objetivos = mets["auc"]["pace_target"]
auc_meta_eoy = mets["auc"]["max"]

print(f"• Meta Anual (EOY): R$ {auc_meta_eoy:,.2f}")
print(f"• Projetado (pace_target): R$ {auc_projetado_objetivos:,.2f}")

# Mostrar cálculo
ano_atual = data_ref.year
dias_decorridos = (data_ref - pd.Timestamp(ano_atual, 1, 1)).days + 1
total_dias_ano = 365
proporcao_ano = dias_decorridos / total_dias_ano

print(f"• Cálculo: R$ {auc_meta_eoy:,.2f} × {proporcao_ano:.4f} = R$ {auc_projetado_objetivos:,.2f}")

# 2. Calcular valor projetado do Rumo a 1BI (função render_rumo_a_1bi)
print(f"\n📊 RUMO A 1BI - render_rumo_a_1bi:")

# Obter metas por ano
meta_2025 = obter_meta_objetivo(2025, "auc_objetivo_ano", 600_000_000.0)
meta_2026 = obter_meta_objetivo(2026, "auc_objetivo_ano", 800_000_000.0)
meta_2027 = obter_meta_objetivo(2027, "auc_objetivo_ano", 1_000_000_000.0)

print(f"• Meta 2025: R$ {meta_2025:,.2f}")
print(f"• Meta 2026: R$ {meta_2026:,.2f}")
print(f"• Meta 2027: R$ {meta_2027:,.2f}")

# Marcos de datas
d0 = pd.Timestamp(2025, 1, 1)
d1 = pd.Timestamp(2025, 12, 31)

# Cálculo de interpolação linear para 2025
def _interp_linear(data, di, df, vi, vf) -> float:
    if data <= di:
        return float(vi)
    if data >= df:
        return float(vf)
    total = (df - di).days
    if total <= 0:
        return float(vf)
    decorrido = (data - di).days
    return float(vi + (vf - vi) * (decorrido / total))

threshold_projetado = _interp_linear(data_ref, d0, d1, 0.0, meta_2025)

print(f"• Projetado (interpolação): R$ {threshold_projetado:,.2f}")

# Mostrar cálculo
dias_ano_2025 = (d1 - d0).days + 1
dias_corridos_2025 = (data_ref - d0).days + 1
proporcao_2025 = dias_corridos_2025 / dias_ano_2025

print(f"• Cálculo: R$ {meta_2025:,.2f} × {proporcao_2025:.4f} = R$ {threshold_projetado:,.2f}")

# 3. Comparar valores
print(f"\n🔍 COMPARAÇÃO DOS VALORES:")
print(f"• AUC 2025 (calcular_indicadores_objetivos): R$ {auc_projetado_objetivos:,.2f}")
print(f"• RUMO A 1BI (render_rumo_a_1bi):           R$ {threshold_projetado:,.2f}")

diferenca = abs(auc_projetado_objetivos - threshold_projetado)
print(f"• Diferença: R$ {diferenca:,.2f}")

if diferenca > 0.01:
    print(f"❌ VALORES DIFERENTES!")
    print(f"   Diferença de R$ {diferenca:,.2f}")
    
    print(f"\n🔧 ANÁLISE DA CAUSA:")
    print(f"• AUC 2025 usa meta: R$ {auc_meta_eoy:,.2f}")
    print(f"• RUMO A 1BI usa meta: R$ {meta_2025:,.2f}")
    
    if auc_meta_eoy != meta_2025:
        print(f"❌ CAUSA ENCONTRADA: Metas anuais diferentes!")
        print(f"   → calcular_indicadores_objetivos usa: {auc_meta_eoy:,.2f}")
        print(f"   → render_rumo_a_1bi usa: {meta_2025:,.2f}")
    else:
        print(f"⚠️  Outra causa possível: arredondamento ou cálculo")
else:
    print(f"✅ VALORES IGUAIS!")

print(f"\n🎯 RECOMENDAÇÃO:")
print(f"Unificar o cálculo para usar a mesma fonte de meta anual")
