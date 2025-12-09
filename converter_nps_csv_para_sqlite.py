import sqlite3
import pandas as pd
import os
from pathlib import Path

print("=== CONVERSÃO DE NPS DE CSV PARA SQLITE ===\n")

# Configurações
arquivo_csv = "DBV Capital_NPS.csv"
arquivo_db = "DBV Capital_NPS.db"
nome_tabela = "nps"

# Verificar se o arquivo CSV existe
if not os.path.exists(arquivo_csv):
    print(f"❌ Arquivo {arquivo_csv} não encontrado!")
    exit(1)

print(f"📁 Arquivo CSV encontrado: {arquivo_csv}")

try:
    # Ler o arquivo CSV
    print("📖 Lendo arquivo CSV...")
    df = pd.read_csv(arquivo_csv, encoding='utf-8-sig')
    
    print(f"📊 Informações do DataFrame:")
    print(f"   • Total de linhas: {len(df)}")
    print(f"   • Total de colunas: {len(df.columns)}")
    print(f"   • Colunas: {list(df.columns)}")
    
    # Remover arquivo DB existente se houver
    if os.path.exists(arquivo_db):
        os.remove(arquivo_db)
        print(f"🗑️  Arquivo DB existente removido")
    
    # Conectar ao banco de dados
    print("🔧 Criando banco de dados SQLite...")
    conn = sqlite3.connect(arquivo_db)
    cursor = conn.cursor()
    
    # Preparar colunas para SQL
    colunas_sql = []
    for coluna in df.columns:
        # Limpar nome da coluna para SQL
        coluna_limpa = str(coluna).replace(' ', '_').replace('-', '_').replace('.', '_').replace(',', '_')
        coluna_limpa = coluna_limpa.replace('(', '').replace(')', '').replace('/', '_')
        coluna_limpa = coluna_limpa.replace('Unnamed', 'Col')
        coluna_limpa = coluna_limpa.replace('Id_do_Usuario', 'Id_Usuario')
        coluna_limpa = coluna_limpa.replace('Survey_ID', 'SurveyID')
        coluna_limpa = coluna_limpa.replace('Customer_ID', 'CustomerID')
        coluna_limpa = coluna_limpa.replace('Codigo_Assessor', 'CodigoAssessor')
        
        # Remover caracteres especiais problemáticos
        coluna_limpa = ''.join(c for c in coluna_limpa if c.isalnum() or c == '_')
        
        # Remover underscores múltiplos
        while '__' in coluna_limpa:
            coluna_limpa = coluna_limpa.replace('__', '_')
        
        # Remover underscore no início ou fim
        coluna_limpa = coluna_limpa.strip('_')
        
        # Se estiver vazio ou começar com número, prefixar
        if not coluna_limpa or coluna_limpa[0].isdigit():
            coluna_limpa = f"col_{coluna_limpa}" if coluna_limpa else f"col_{len(colunas_sql)}"
        
        # Garantir que não comece com número
        if coluna_limpa[0].isdigit():
            coluna_limpa = f"_{coluna_limpa}"
        
        colunas_sql.append(coluna_limpa)
    
    # Mapear nomes originais para nomes limpos
    mapeamento_colunas = dict(zip(df.columns, colunas_sql))
    
    # Renomear colunas no DataFrame
    df_renomeado = df.rename(columns=mapeamento_colunas)
    
    # Criar tabela SQL
    print("📋 Criando tabela SQL...")
    
    # Determinar tipos de dados SQL
    tipos_sql = []
    for coluna in df_renomeado.columns:
        # Verificar o tipo de dados
        serie = df_renomeado[coluna]
        
        # Se for mostly numérica
        if pd.api.types.is_numeric_dtype(serie):
            if pd.api.types.is_integer_dtype(serie):
                tipos_sql.append(f"{coluna} INTEGER")
            else:
                tipos_sql.append(f"{coluna} REAL")
        # Se for data/hora
        elif pd.api.types.is_datetime64_any_dtype(serie):
            tipos_sql.append(f"{coluna} TEXT")
        # Senão, tratar como TEXT
        else:
            tipos_sql.append(f"{coluna} TEXT")
    
    # Comando CREATE TABLE
    create_table_sql = f"""
    CREATE TABLE {nome_tabela} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {', '.join(tipos_sql)}
    )
    """
    
    cursor.execute(create_table_sql)
    print(f"✅ Tabela '{nome_tabela}' criada com {len(tipos_sql)} colunas")
    
    # Inserir dados em chunks para otimizar memória
    chunk_size = 1000
    total_inserido = 0
    
    print("💾 Inserindo dados na tabela...")
    
    for i in range(0, len(df_renomeado), chunk_size):
        chunk = df_renomeado.iloc[i:i+chunk_size]
        
        # Preparar dados para inserção
        dados_para_inserir = []
        for _, row in chunk.iterrows():
            # Converter NaN para None
            dados = [None if pd.isna(val) else val for val in row]
            dados_para_inserir.append(dados)
        
        # Inserir chunk
        placeholders = ', '.join(['?' for _ in df_renomeado.columns])
        insert_sql = f"INSERT INTO {nome_tabela} ({', '.join(df_renomeado.columns)}) VALUES ({placeholders})"
        
        cursor.executemany(insert_sql, dados_para_inserir)
        total_inserido += len(dados_para_inserir)
        
        # Progresso
        progresso = (total_inserido / len(df_renomeado)) * 100
        print(f"   Progresso: {total_inserido}/{len(df_renomeado)} ({progresso:.1f}%)")
    
    # Commit das alterações
    conn.commit()
    
    # Criar índices para otimizar consultas
    print("🔍 Criando índices...")
    
    # Índices principais
    indices_criar = [
        "idx_survey_id",
        "idx_id_usuario", 
        "idx_customer_id",
        "idx_codigo_assessor",
        "idx_status",
        "idx_planilha_origem"
    ]
    
    colunas_index = [
        "SurveyID",
        "Id_Usuario",
        "CustomerID", 
        "CodigoAssessor",
        "Status",
        "planilha_origem"
    ]
    
    for nome_idx, coluna_idx in zip(indices_criar, colunas_index):
        if coluna_idx in df_renomeado.columns:
            try:
                cursor.execute(f"CREATE INDEX {nome_idx} ON {nome_tabela} ({coluna_idx})")
                print(f"   ✅ Índice criado: {nome_idx}")
            except Exception as e:
                print(f"   ⚠️  Índice {nome_idx} não criado: {e}")
    
    # Verificar dados inseridos
    cursor.execute(f"SELECT COUNT(*) FROM {nome_tabela}")
    count_inserido = cursor.fetchone()[0]
    
    print(f"\n✅ Conversão concluída com sucesso!")
    print(f"📄 Arquivo DB criado: {arquivo_db}")
    print(f"📊 Tabela: {nome_tabela}")
    print(f"📊 Registros inseridos: {count_inserido}")
    
    # Verificar integridade
    print(f"\n🔍 Verificação de integridade:")
    
    # Tamanho do arquivo
    tamanho_db = os.path.getsize(arquivo_db) / (1024 * 1024)  # MB
    print(f"• Tamanho do DB: {tamanho_db:.2f} MB")
    
    # Primeiros registros
    cursor.execute(f"SELECT * FROM {nome_tabela} LIMIT 3")
    primeiros_registros = cursor.fetchall()
    
    print(f"• Primeiros 3 registros:")
    for i, registro in enumerate(primeiros_registros, 1):
        print(f"   {i}. ID: {registro[0]} | Survey ID: {registro[1]} | Assessor: {registro[8]}")
    
    # Verificar quantidade de índices criados
    try:
        cursor.execute(f"PRAGMA index_list({nome_tabela})")
        indices_db = cursor.fetchall()
        qtd_indices = len(indices_db)
    except:
        qtd_indices = 0
    
    # Salvar informações do processo
    with open("log_conversao_nps_sqlite.txt", "w", encoding="utf-8") as f:
        f.write(f"CONVERSÃO NPS - CSV PARA SQLITE\n")
        f.write(f"{'='*50}\n")
        f.write(f"Arquivo CSV: {arquivo_csv}\n")
        f.write(f"Arquivo DB: {arquivo_db}\n")
        f.write(f"Tabela: {nome_tabela}\n")
        f.write(f"Registros no CSV: {len(df)}\n")
        f.write(f"Registros inseridos: {count_inserido}\n")
        f.write(f"Colunas: {list(df_renomeado.columns)}\n")
        f.write(f"Tamanho DB: {tamanho_db:.2f} MB\n")
        f.write(f"Índices criados: {qtd_indices}\n")
        f.write(f"{'='*50}\n")
        f.write(f"CONVERSÃO CONCLUÍDA COM SUCESSO!\n")
    
    print(f"\n📝 Log salvo: log_conversao_nps_sqlite.txt")
    
    # Fechar conexão
    conn.close()
    
except Exception as e:
    print(f"❌ Erro durante a conversão: {e}")
    if 'conn' in locals():
        conn.close()

print(f"\n🚀 Processo concluído!")
