import pandas as pd
import os

# --- EXPORTAR ABA(S) DO ARQUIVO "DBV Capital_Objetivos.xlsx" PARA CSVs E SQLITE ---

import sqlite3
import re

excel_file_Objetivos = 'DBV Capital_Objetivos.xlsx'

# mapeamento: {nome_da_aba_no_excel: nome_do_csv}
sheets_map = {
    'Objetivos_PJ1': 'DBV Capital_Objetivo_PJ1.csv',
    'Saúde':         'DBV Capital_Saude.csv',
    'Consórcio':     'DBV Capital_Consorcio.csv',
    'Vida':          'DBV Capital_Vida.csv',
    'AutoRE':        'DBV Capital_AutoRE.csv',
    'Financiamento': 'DBV Capital_Financiamento.csv',
    'Crédito':       'DBV Capital_Credito.csv',
    'Câmbio':        'DBV Capital_Cambio.csv',
}
sqlite_db_Objetivos = 'DBV Capital_Objetivos.db'  # saída do SQLite para estas abas

def _normalize_name(name: str) -> str:
    """normaliza nomes (tabelas/colunas): minúsculo, _ e sem acentos/espaços."""
    s = str(name).strip().lower()
    # troca espaços por _
    s = re.sub(r'\s+', '_', s)
    # remove acentos/símbolos (mantém letras/números/_)
    s = (s.replace('á','a').replace('à','a').replace('ã','a').replace('â','a')
           .replace('é','e').replace('ê','e')
           .replace('í','i')
           .replace('ó','o').replace('ô','o').replace('õ','o')
           .replace('ú','u')
           .replace('ç','c'))
    s = re.sub(r'[^0-9a-z_]', '', s)
    return s or 'tabela'

def _normalize_columns(df):
    cols = []
    seen = {}
    for c in df.columns:
        c2 = _normalize_name(c)
        if c2 not in seen:
            seen[c2] = 1
            cols.append(c2)
        else:
            seen[c2] += 1
            cols.append(f'{c2}_{seen[c2]}')
    df.columns = cols
    return df



def main():
    # Caminhos dos arquivos
    excel_file_FeeBased = 'DBV Capital_FeeBased.xlsx'
    csv_file_FeeBased = 'DBV Capital_FeeBased.csv'
    
    excel_file_Receitas = 'DBV Capital_Receitas.xlsx'
    csv_file_Receitas = 'DBV Capital_Receitas.csv'

    excel_file_Positivador = 'DBV Capital_Positivador.xlsx'
    csv_file_Positivador = 'DBV Capital_Positivador.csv'

    excel_file_Positivador_MTD = 'DBV Capital_Positivador_MTD.xlsx'
    csv_file_Positivador_MTD = 'DBV Capital_Positivador_MTD.csv'

    excel_file_Habilitacoes = 'DBV Capital_Habilitacoes.xlsx'
    csv_file_Habilitacoes = 'DBV Capital_Habilitacoes.csv'

    excel_file_Transferencias = 'DBV Capital_Transferências.xlsx'
    csv_file_Transferencias = 'DBV Capital_Transferências.csv'

    excel_file_Diversificador = 'DBV Capital_Diversificador.xlsx'
    csv_file_Diversificador = 'DBV Capital_Diversificador.csv'

    excel_file_Produtos = 'DBV Capital_Produtos.xlsx'
    csv_file_Produtos = 'DBV Capital_Produtos.csv'

    excel_file_MesaRV = 'DBV Capital_AUC Mesa RV.xlsx'
    csv_file_MesaRV = 'DBV Capital_AUC Mesa RV.csv'

    excel_file_Clientes = 'DBV Capital_Clientes.xlsx'
    csv_file_Clientes = 'DBV Capital_Clientes.csv'

    
    try:
        # Ler o arquivo Excel
        print(f"Lendo o arquivo {excel_file_FeeBased}...")
        df = pd.read_excel(excel_file_FeeBased)
        
        # Salvar como CSV com codificação UTF-8
        print(f"Salvando como {csv_file_FeeBased}...")
        df.to_csv(csv_file_FeeBased, index=False, encoding='utf-8')
        
        print("Conversão concluída com sucesso!")
        print(f"Arquivo CSV criado: {os.path.abspath(csv_file_FeeBased)}")
        
    except Exception as e:
        print(f"Erro durante a conversão: {str(e)}")

    try:
        # Ler o arquivo Excel
        print(f"Lendo o arquivo {excel_file_Receitas}...")
        df = pd.read_excel(excel_file_Receitas)
        
        # Salvar como CSV com codificação UTF-8
        print(f"Salvando como {csv_file_Receitas}...")
        df.to_csv(csv_file_Receitas, index=False, encoding='utf-8')
        
        print("Conversão concluída com sucesso!")
        print(f"Arquivo CSV criado: {os.path.abspath(csv_file_Receitas)}")
        
    except Exception as e:
        print(f"Erro durante a conversão: {str(e)}")

    try:
        # Ler o arquivo Excel
        print(f"Lendo o arquivo {excel_file_Positivador}...")
        df = pd.read_excel(excel_file_Positivador)
        
        # Salvar como CSV com codificação UTF-8
        print(f"Salvando como {csv_file_Positivador}...")
        df.to_csv(csv_file_Positivador, index=False, encoding='utf-8')
        
        print("Conversão concluída com sucesso!")
        print(f"Arquivo CSV criado: {os.path.abspath(csv_file_Positivador)}")
        
    except Exception as e:
        print(f"Erro durante a conversão: {str(e)}")

    try:
        # Ler o arquivo Excel
        print(f"Lendo o arquivo {excel_file_Habilitacoes}...")
        df = pd.read_excel(excel_file_Habilitacoes)
        
        # Salvar como CSV com codificação UTF-8
        print(f"Salvando como {csv_file_Habilitacoes}...")
        df.to_csv(csv_file_Habilitacoes, index=False, encoding='utf-8')
        
        print("Conversão concluída com sucesso!")
        print(f"Arquivo CSV criado: {os.path.abspath(csv_file_Habilitacoes)}")
        
    except Exception as e:
        print(f"Erro durante a conversão: {str(e)}")

    try:
        # Ler o arquivo Excel
        print(f"Lendo o arquivo {excel_file_Transferencias}...")
        df = pd.read_excel(excel_file_Transferencias)
        
        # Salvar como CSV com codificação UTF-8
        print(f"Salvando como {csv_file_Transferencias}...")
        df.to_csv(csv_file_Transferencias, index=False, encoding='utf-8')
        
        print("Conversão concluída com sucesso!")
        print(f"Arquivo CSV criado: {os.path.abspath(csv_file_Transferencias)}")
        
    except Exception as e:
        print(f"Erro durante a conversão: {str(e)}")

    try:
        # Ler o arquivo Excel
        print(f"Lendo o arquivo {excel_file_Diversificador}...")
        df = pd.read_excel(excel_file_Diversificador)
        
        # Salvar como CSV com codificação UTF-8
        print(f"Salvando como {csv_file_Diversificador}...")
        df.to_csv(csv_file_Diversificador, index=False, encoding='utf-8')
        
        print("Conversão concluída com sucesso!")
        print(f"Arquivo CSV criado: {os.path.abspath(csv_file_Diversificador)}")
        
    except Exception as e:
        print(f"Erro durante a conversão: {str(e)}")

    try:
        # Ler o arquivo Excel
        print(f"Lendo o arquivo {excel_file_Produtos}...")
        df = pd.read_excel(excel_file_Produtos)
        
        # Salvar como CSV com codificação UTF-8
        print(f"Salvando como {csv_file_Produtos}...")
        df.to_csv(csv_file_Produtos, index=False, encoding='utf-8')
        
        print("Conversão concluída com sucesso!")
        print(f"Arquivo CSV criado: {os.path.abspath(csv_file_Produtos)}")

    except Exception as e:
        print(f"Erro durante a conversão: {str(e)}")

    try:
        # Ler o arquivo Excel
        print(f"Lendo o arquivo {excel_file_MesaRV}...")
        df = pd.read_excel(excel_file_MesaRV)
        
        # Salvar como CSV com codificação UTF-8
        print(f"Salvando como {csv_file_MesaRV}...")
        df.to_csv(csv_file_MesaRV, index=False, encoding='utf-8')
        
        print("Conversão concluída com sucesso!")
        print(f"Arquivo CSV criado: {os.path.abspath(csv_file_MesaRV)}")
        
    except Exception as e:
        print(f"Erro durante a conversão: {str(e)}")

    try:
        # Ler o arquivo Excel
        print(f"Lendo o arquivo {excel_file_Clientes}...")
        df = pd.read_excel(excel_file_Clientes)
        
        # Salvar como CSV com codificação UTF-8
        print(f"Salvando como {csv_file_Clientes}...")
        df.to_csv(csv_file_Clientes, index=False, encoding='utf-8')
        
        print("Conversão concluída com sucesso!")
        print(f"Arquivo CSV criado: {os.path.abspath(csv_file_Clientes)}")
        
    except Exception as e:
        print(f"Erro durante a conversão: {str(e)}")

    try:
        # lê todas as abas necessárias de uma vez (só as do dict)
        print(f"Lendo abas do arquivo {excel_file_Objetivos}...")
        wanted = list(sheets_map.keys())
        dfs = pd.read_excel(excel_file_Objetivos, sheet_name=wanted, dtype=object, engine='openpyxl')

        # exporta CSV por aba
        for sheet_name, csv_out in sheets_map.items():
            if sheet_name not in dfs:
                print(f"Aviso: aba '{sheet_name}' não encontrada em {excel_file_Objetivos}. Pulando.")
                continue

            df_sheet = dfs[sheet_name].copy()
            df_sheet = _normalize_columns(df_sheet)

            print(f"Salvando aba '{sheet_name}' em CSV: {csv_out}...")
            df_sheet.to_csv(csv_out, index=False, encoding='utf-8')
            print(f"CSV criado: {os.path.abspath(csv_out)}")

        # grava cada aba como tabela separada no SQLite
        print(f"Gravando tabelas no SQLite: {sqlite_db_Objetivos} ...")
        with sqlite3.connect(sqlite_db_Objetivos) as conn:
            for sheet_name, csv_out in sheets_map.items():
                if sheet_name not in dfs:
                    continue
                table_name = _normalize_name(sheet_name)          # ex.: objetivos_pj1, saude, consorcio, ...
                df_sheet = _normalize_columns(dfs[sheet_name].copy())
                df_sheet.to_sql(table_name, conn, if_exists='replace', index=False)
                print(f"- Tabela criada/atualizada: {table_name} (linhas: {len(df_sheet)})")

        print("Exportação das abas e gravação no SQLite concluídas com sucesso!")

    except Exception as e:
        print(f"Erro no processamento das abas de objetivos: {str(e)}")

    try:
        print(f"Lendo o arquivo {excel_file_Positivador_MTD}...")
        df = pd.read_excel(excel_file_Positivador_MTD)
        
        # Salvar como CSV com codificação UTF-8
        print(f"Salvando como {csv_file_Positivador_MTD}...")
        df.to_csv(csv_file_Positivador_MTD, index=False, encoding='utf-8')
        
        print("Conversão concluída com sucesso!")
        print(f"Arquivo CSV criado: {os.path.abspath(csv_file_Positivador_MTD)}")
        
    except Exception as e:
        print(f"Erro durante a conversão: {str(e)}")
        
    
    print("\nProcessamento concluído.")

if __name__ == "__main__":
    main()
