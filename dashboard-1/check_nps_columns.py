import sqlite3
import pandas as pd

try:
    # Connect to the SQLite database
    conn = sqlite3.connect('DBV Capital_NPS.db')
    
    # Get table information
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
    print("Tables in the database:")
    print(tables)
    
    # Check columns in the nps table
    for table in tables['name']:
        print(f"\nColumns in table '{table}':")
        columns = pd.read_sql_query(f"PRAGMA table_info({table});", conn)
        print(columns)
        
        # Show sample data for the first 5 rows
        print(f"\nSample data from '{table}':")
        sample = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 5;", conn)
        print(sample)
        
except Exception as e:
    print(f"Error: {e}")
    
finally:
    if 'conn' in locals():
        conn.close()
