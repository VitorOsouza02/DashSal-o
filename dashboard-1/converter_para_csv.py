import sqlite3
import pandas as pd
import os

def converter_para_csv(banco_dados, pasta_saida='csv_export'):
    """
    Converte todas as tabelas de um banco de dados SQLite para arquivos CSV.
    
    Args:
        banco_dados (str): Caminho para o arquivo do banco de dados SQLite
        pasta_saida (str): Nome da pasta onde os arquivos CSV serão salvos
    """
    # Cria o diretório de saída se não existir
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
    
    # Conecta ao banco de dados
    conn = sqlite3.connect(banco_dados)
    cursor = conn.cursor()
    
    # Obtém a lista de tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = cursor.fetchall()
    
    if not tabelas:
        print("Nenhuma tabela encontrada no banco de dados.")
        return
    
    print(f"\nIniciando conversão de {len(tabelas)} tabelas para CSV...\n")
    
    # Para cada tabela, exporta para CSV
    for tabela in tabelas:
        tabela_nome = tabela[0]
        arquivo_saida = os.path.join(pasta_saida, f"{tabela_nome}.csv")
        
        try:
            # Lê a tabela para um DataFrame do pandas
            df = pd.read_sql_query(f"SELECT * FROM \"{tabela_nome}\"", conn)
            
            # Salva como CSV
            df.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')
            print(f"✓ Tabela '{tabela_nome}' exportada para '{arquivo_saida}'")
            
        except Exception as e:
            print(f"❌ Erro ao exportar tabela '{tabela_nome}': {str(e)}")
    
    conn.close()
    print("\nConversão concluída!")

if __name__ == "__main__":
    banco_dados = "DBV Capital_Objetivos.db"
    converter_para_csv(banco_dados)
