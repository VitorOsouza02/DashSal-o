import pandas as pd
import sqlite3
import os

# File paths
excel_file = 'DBV Capital_NPS.xlsm'
db_file = 'DBV Capital_NPS.db'
csv_file = 'temp_nps.csv'

print("Lendo o arquivo Excel...")
# Read the Excel file - specify engine='openpyxl' for .xlsm files
df = pd.read_excel(excel_file, engine='openpyxl')

print(f"Salvando como CSV temporário: {csv_file}")
# Save as CSV first to handle any potential Excel formatting issues
df.to_csv(csv_file, index=False, encoding='utf-8')

print(f"Criando banco de dados SQLite: {db_file}")
# Create SQLite database and insert data
conn = sqlite3.connect(db_file)

# Read the CSV file with the same parameters as Excel export
df_csv = pd.read_csv(csv_file, encoding='utf-8')

# Save to SQLite
table_name = 'nps_data'  # Nome da tabela no banco de dados
df_csv.to_sql(table_name, conn, if_exists='replace', index=False)

# Get column information for verification
cursor = conn.cursor()

# Get row count
cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
count = cursor.fetchone()[0]

# Get column names
cursor.execute(f"PRAGMA table_info({table_name})")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print("\nConversão concluída com sucesso!")
print(f"Arquivo de saída: {os.path.abspath(db_file)}")
print(f"Tabela criada: {table_name}")
print(f"Total de registros: {count:,}")
print(f"Colunas: {', '.join(column_names)}")

# Clean up temporary CSV file
os.remove(csv_file)

# Close the connection
conn.close()
