import sqlite3
import pandas as pd
from pathlib import Path

def check_objetivos():
    caminho_db = Path(__file__).parent / "DBV Capital_Objetivos.db"
    conn = sqlite3.connect(str(caminho_db))
    
    # Check available tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Available tables:", [t[0] for t in tables])
    
    # Check objetivos table structure and data
    try:
        # Get column info
        cursor.execute("PRAGMA table_info(objetivos);")
        columns = cursor.fetchall()
        print("\nobjetivos table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Get all data from objetivos table
        df = pd.read_sql_query("SELECT * FROM objetivos", conn)
        print("\nobjetivos table data:")
        print(df)
        
        # Get distinct years and their max auc_total
        df_years = pd.read_sql_query("""
            SELECT 
                strftime('%Y', data) as year,
                MAX(auc_total) as max_auc_total
            FROM objetivos 
            GROUP BY strftime('%Y', data)
            ORDER BY year
        """, conn)
        
        print("\nAUC totals by year:")
        print(df_years)
        
    except Exception as e:
        print(f"Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_objetivos()
