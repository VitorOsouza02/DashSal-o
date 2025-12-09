import pandas as pd
import os
from pathlib import Path

print("=== CONVERSÃO DE NPS DE .XLSM PARA CSV ===\n")

# Configurações
arquivo_xlsm = "DBV Capital_NPS.xlsm"
arquivo_csv = "DBV Capital_NPS.csv"

# Verificar se o arquivo existe
if not os.path.exists(arquivo_xlsm):
    print(f"❌ Arquivo {arquivo_xlsm} não encontrado!")
    exit(1)

print(f"📁 Arquivo encontrado: {arquivo_xlsm}")

try:
    # Tentar ler o arquivo .xlsm
    print("📖 Lendo arquivo .xlsm...")
    
    # Primeiro, verificar as planilhas disponíveis
    xl_file = pd.ExcelFile(arquivo_xlsm)
    planilhas = xl_file.sheet_names
    print(f"📋 Planilhas encontradas: {planilhas}")
    
    # Ler cada planilha e salvar como CSV separado ou combinado
    dados_combinados = []
    
    for planilha in planilhas:
        print(f"\n📊 Processando planilha: {planilha}")
        
        try:
            # Ler a planilha
            df = pd.read_excel(arquivo_xlsm, sheet_name=planilha, engine='openpyxl')
            
            print(f"   • Linhas: {len(df)}")
            print(f"   • Colunas: {len(df.columns)}")
            print(f"   • Colunas: {list(df.columns)}")
            
            # Adicionar coluna para identificar a planilha de origem
            df['planilha_origem'] = planilha
            
            dados_combinados.append(df)
            
            # Também salvar planilha individual se houver mais de uma
            if len(planilhas) > 1:
                nome_csv_individual = f"DBV Capital_NPS_{planilha.replace(' ', '_')}.csv"
                df.to_csv(nome_csv_individual, index=False, encoding='utf-8-sig')
                print(f"   ✅ Salvo individualmente: {nome_csv_individual}")
            
        except Exception as e:
            print(f"   ❌ Erro ao ler planilha {planilha}: {e}")
            continue
    
    if dados_combinados:
        # Combinar todos os dados
        df_final = pd.concat(dados_combinados, ignore_index=True)
        
        # Salvar como CSV único
        df_final.to_csv(arquivo_csv, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ Conversão concluída com sucesso!")
        print(f"📄 Arquivo CSV criado: {arquivo_csv}")
        print(f"📊 Total de linhas combinadas: {len(df_final)}")
        print(f"📊 Total de colunas: {len(df_final.columns)}")
        
        # Verificar integridade dos dados
        print(f"\n🔍 Verificação de integridade:")
        print(f"• Valores nulos por coluna:")
        nulos = df_final.isnull().sum()
        for coluna, qtd_nulos in nulos.items():
            if qtd_nulos > 0:
                print(f"   - {coluna}: {qtd_nulos} nulos ({qtd_nulos/len(df_final):.1%})")
        
        # Mostrar primeiras linhas
        print(f"\n📋 Primeiras 3 linhas do CSV:")
        print(df_final.head(3).to_string())
        
        # Salvar informações do processo
        with open("log_conversao_nps.txt", "w", encoding="utf-8") as f:
            f.write(f"CONVERSÃO NPS - .XLSM PARA CSV\n")
            f.write(f"{'='*50}\n")
            f.write(f"Arquivo original: {arquivo_xlsm}\n")
            f.write(f"Arquivo final: {arquivo_csv}\n")
            f.write(f"Planilhas processadas: {planilhas}\n")
            f.write(f"Total de linhas: {len(df_final)}\n")
            f.write(f"Total de colunas: {len(df_final.columns)}\n")
            f.write(f"Colunas: {list(df_final.columns)}\n")
            f.write(f"{'='*50}\n")
            f.write(f"CONVERSÃO CONCLUÍDA COM SUCESSO!\n")
        
        print(f"\n📝 Log salvo: log_conversao_nps.txt")
        
    else:
        print("❌ Nenhum dado foi processado!")
        
except Exception as e:
    print(f"❌ Erro durante a conversão: {e}")
    print(f"💡 Verifique se o arquivo não está aberto ou corrompido")

print(f"\n🚀 Processo concluído!")
