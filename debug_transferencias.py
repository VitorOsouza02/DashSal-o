import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Caminho do banco
db_path = Path(__file__).parent / 'DBV Capital_Transferências.db'

print("=== DEBUG TRANSFERÊNCIAS ===\n")

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    
    # 1. Total com status='Concluído' e cliente='Externo'
    print("1. Total com status='Concluído' e cliente='Externo':")
    df1 = pd.read_sql_query("""
        SELECT COUNT(*) as total FROM dados
        WHERE cliente = 'Externo' AND status = 'Concluído'
    """, conn)
    print(f"   {df1['total'].values[0]}\n")
    
    # 2. Verificar datas - qual é a data mais recente?
    print("2. Data mais recente no banco:")
    df2 = pd.read_sql_query("""
        SELECT 
            MAX(CASE WHEN data_solicitacao IS NOT NULL AND data_solicitacao != '' THEN data_solicitacao END) as max_data_solicitacao,
            MAX(CASE WHEN data_transferencia IS NOT NULL AND data_transferencia != '' THEN data_transferencia END) as max_data_transferencia
        FROM dados
        WHERE cliente = 'Externo' AND status = 'Concluído'
    """, conn)
    print(f"   data_solicitacao: {df2['max_data_solicitacao'].values[0]}")
    print(f"   data_transferencia: {df2['max_data_transferencia'].values[0]}\n")
    
    # 3. Contar por mês (data_solicitacao)
    print("3. Contagem por mês (data_solicitacao):")
    df3 = pd.read_sql_query("""
        SELECT 
            substr(data_solicitacao, 1, 7) as mes,
            COUNT(*) as qtd
        FROM dados
        WHERE cliente = 'Externo' AND status = 'Concluído' 
          AND data_solicitacao IS NOT NULL AND data_solicitacao != ''
        GROUP BY substr(data_solicitacao, 1, 7)
        ORDER BY mes DESC
    """, conn)
    print(df3.to_string(index=False))
    print()
    
    # 4. Contar por mês (data_transferencia) - fallback
    print("4. Contagem por mês (data_transferencia - fallback):")
    df4 = pd.read_sql_query("""
        SELECT 
            substr(data_transferencia, 1, 7) as mes,
            COUNT(*) as qtd
        FROM dados
        WHERE cliente = 'Externo' AND status = 'Concluído' 
          AND (data_solicitacao IS NULL OR data_solicitacao = '')
          AND data_transferencia IS NOT NULL AND data_transferencia != ''
        GROUP BY substr(data_transferencia, 1, 7)
        ORDER BY mes DESC
    """, conn)
    print(df4.to_string(index=False))
    print()
    
    # 5. Simular o filtro do dashboard (últimas datas do Positivador)
    print("5. Simulando filtro de data do dashboard:")
    
    # Pega a data mais recente do Positivador
    db_positivador = Path(__file__).parent / 'DBV Capital_Positivador.db'
    if db_positivador.exists():
        conn_pos = sqlite3.connect(str(db_positivador))
        df_pos_date = pd.read_sql_query("""
            SELECT MAX(Data_Posicao) as ultima_data FROM positivador
        """, conn_pos)
        ultima_data_pos = df_pos_date['ultima_data'].values[0]
        conn_pos.close()
        
        print(f"   Última data do Positivador: {ultima_data_pos}")
        
        if ultima_data_pos:
            # Simular o mesmo filtro que o dashboard usa
            from datetime import datetime as dt
            ultima_data = dt.strptime(ultima_data_pos[:10], '%Y-%m-%d')
            primeiro_dia_mes = ultima_data.replace(day=1).strftime('%Y-%m-%d')
            if ultima_data.month == 12:
                ultimo_dia_mes = ultima_data.replace(year=ultima_data.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                ultimo_dia_mes = ultima_data.replace(month=ultima_data.month + 1, day=1) - timedelta(days=1)
            
            print(f"   Intervalo de filtro: {primeiro_dia_mes} a {ultimo_dia_mes.strftime('%Y-%m-%d')}\n")
            
            # Contar com esse filtro
            df5 = pd.read_sql_query(f"""
                WITH t AS (
                    SELECT 
                        data_solicitacao,
                        data_transferencia,
                        CASE
                            WHEN data_solicitacao IS NOT NULL AND data_solicitacao != '' THEN
                                CASE
                                    WHEN instr(data_solicitacao, '/') > 0 THEN 
                                        substr(data_solicitacao, 7, 4) || '-' || substr(data_solicitacao, 4, 2) || '-' || substr(data_solicitacao, 1, 2)
                                    ELSE 
                                        substr(data_solicitacao, 1, 10)
                                END
                            WHEN data_transferencia IS NOT NULL AND data_transferencia != '' THEN
                                CASE
                                    WHEN instr(data_transferencia, '/') > 0 THEN 
                                        substr(data_transferencia, 7, 4) || '-' || substr(data_transferencia, 4, 2) || '-' || substr(data_transferencia, 1, 2)
                                    ELSE 
                                        substr(data_transferencia, 1, 10)
                                END
                            ELSE NULL
                        END AS data_efetiva_conv
                    FROM dados
                    WHERE cliente = 'Externo' 
                      AND pl IS NOT NULL 
                      AND pl != ''
                      AND status = 'Concluído'
                )
                SELECT COUNT(*) as total FROM t
                WHERE data_efetiva_conv IS NOT NULL
                  AND date(data_efetiva_conv) BETWEEN '{primeiro_dia_mes}' AND '{ultimo_dia_mes.strftime('%Y-%m-%d')}'
            """, conn)
            print(f"   Registros com filtro de data do dashboard: {df5['total'].values[0]}\n")
    
    # 6. Amostra de registros que deveriam aparecer
    print("6. Amostra de registros (status='Concluído' e cliente='Externo'):")
    df6 = pd.read_sql_query("""
        SELECT 
            codigo_assessor_origem,
            codigo_assessor_destino,
            data_solicitacao,
            data_transferencia,
            pl
        FROM dados
        WHERE cliente = 'Externo' AND status = 'Concluído'
        LIMIT 15
    """, conn)
    print(df6.to_string(index=False))
    
    conn.close()
else:
    print("Banco de dados não encontrado!")
