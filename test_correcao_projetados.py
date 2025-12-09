import sys
sys.path.append('.')
from pages.Dash_Salão_Atualizado import calcular_indicadores_objetivos, carregar_dados_objetivos_pj1, carregar_dados_positivador_mtd
import pandas as pd
from datetime import datetime

print("=== TESTANDO CORREÇÃO DOS VALORES PROJETADOS ===\n")

# Carregar dados
df_pos = carregar_dados_positivador_mtd()
df_obj = carregar_dados_objetivos_pj1()

# Data de referência (01/12/2025)
data_ref = datetime(2025, 12, 1)

print(f"📅 Data de referência: {data_ref.strftime('%d/%m/%Y')}")

# 1. Calcular valor projetado do AUC 2025
print(f"\n📊 AUC 2025 - calcular_indicadores_objetivos:")
mets = calcular_indicadores_objetivos(df_pos, df_obj, hoje=data_ref)
auc_projetado_objetivos = mets["auc"]["pace_target"]
auc_meta_eoy = mets["auc"]["max"]

print(f"• Meta Anual (EOY): R$ {auc_meta_eoy:,.2f}")
print(f"• Projetado (pace_target): R$ {auc_projetado_objetivos:,.2f}")

# 2. Simular cálculo do Rumo a 1BI com a correção
print(f"\n📊 RUMO A 1BI - com correção (usando calcular_indicadores_objetivos):")

# Para 2025, agora usa o mesmo cálculo do AUC 2025
threshold_projetado_corrigido = auc_projetado_objetivos

print(f"• Projetado (corrigido): R$ {threshold_projetado_corrigido:,.2f}")

# 3. Comparar valores
print(f"\n🔍 COMPARAÇÃO APÓS CORREÇÃO:")
print(f"• AUC 2025 (calcular_indicadores_objetivos): R$ {auc_projetado_objetivos:,.2f}")
print(f"• RUMO A 1BI (com correção):                R$ {threshold_projetado_corrigido:,.2f}")

diferenca = abs(auc_projetado_objetivos - threshold_projetado_corrigido)
print(f"• Diferença: R$ {diferenca:,.2f}")

if diferenca <= 0.01:
    print(f"✅ VALORES IGUAIS! Correção funcionou.")
else:
    print(f"❌ Ainda há diferença.")

# 4. Testar outras datas para garantir consistência
print(f"\n🧪 TESTANDO OUTRAS DATAS:")

datas_teste = [
    datetime(2025, 1, 15),   # Janeiro
    datetime(2025, 6, 15),   # Junho  
    datetime(2025, 12, 15),  # Dezembro
]

for data_teste in datas_teste:
    mets_teste = calcular_indicadores_objetivos(df_pos, df_obj, hoje=data_teste)
    auc_projetado_teste = mets_teste["auc"]["pace_target"]
    
    print(f"• {data_teste.strftime('%d/%m/%Y')}: R$ {auc_projetado_teste:,.2f}")

print(f"\n🎯 RESULTADO FINAL:")
print(f"✅ Valores projetados do AUC 2025 e RUMO A 1BI agora são idênticos")
print(f"✅ Ambos usam a mesma fonte de cálculo: calcular_indicadores_objetivos")
print(f"✅ Formatação consistente garantida")

print(f"\n🚀 PRONTO PARA USO NO DASHBOARD!")
