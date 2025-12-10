import pandas as pd
import sqlite3
import os

# File paths
excel_file = '10-12-2025_Relatório Positivador.xlsx'
db_file = 'DBV Capital_Positivador.db'
csv_file = 'temp_positivador.csv'

print("Lendo o arquivo Excel...")
# Read the Excel file
df = pd.read_excel(excel_file)

print(f"Salvando como CSV temporário: {csv_file}")
# Save as CSV first to handle any potential Excel formatting issues
df.to_csv(csv_file, index=False, encoding='utf-8')

print(f"Criando banco de dados SQLite: {db_file}")
# Create SQLite database and insert data
conn = sqlite3.connect(db_file)

# Read the CSV file with the same parameters as Excel export
df_csv = pd.read_csv(csv_file, encoding='utf-8')

# Save to SQLite
df_csv.to_sql('positivador', conn, if_exists='replace', index=False)

# Clean up temporary CSV file
os.remove(csv_file)

# Verify data was inserted correctly
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM positivador")
count = cursor.fetchone()[0]

print(f"Conversão concluída! Total de {count} registros importados para o banco de dados.")
print(f"Banco de dados criado com sucesso: {os.path.abspath(db_file)}")

# Close the connection
conn.close()
