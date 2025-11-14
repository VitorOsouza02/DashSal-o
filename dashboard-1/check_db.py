#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
check_db.py
----------------------------------------
Inspeciona um banco SQLite:
- Lista tabelas com número de linhas
- Mostra schema (PRAGMA table_info)
- Lista índices (PRAGMA index_list / index_info)
- Mostra nulos por coluna
- Mostra amostra de linhas
- (Opcional) estatísticas básicas para colunas numéricas

Uso:
  python check_db.py --db caminho/do/arquivo.db
  python check_db.py --db arquivo.db --table objetivos_pj1
  python check_db.py --db arquivo.db --like obj% --limit 20
"""

import argparse
import os
import sqlite3
import sys
from textwrap import indent

import pandas as pd


def connect(db_path: str) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        print(f"Arquivo não encontrado: {db_path}", file=sys.stderr)
        sys.exit(1)
    return sqlite3.connect(db_path)


def list_tables(conn: sqlite3.Connection, like: str | None = None) -> list[str]:
    cur = conn.cursor()
    if like:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ? ORDER BY name;",
            (like,)
        )
    else:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    return [r[0] for r in cur.fetchall()]


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM [{table}]")
    return cur.fetchone()[0]


def get_schema(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    return pd.read_sql_query(f"PRAGMA table_info([{table}]);", conn)


def get_indexes(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    idx_list = pd.read_sql_query(f"PRAGMA index_list([{table}]);", conn)
    rows = []
    for _, r in idx_list.iterrows():
        idx_name = r["name"]
        info = pd.read_sql_query(f"PRAGMA index_info([{idx_name}]);", conn)
        rows.append({"index_name": idx_name, "unique": r.get("unique", None), "columns": ",".join(info["name"])})
    return pd.DataFrame(rows)


def null_counts(df: pd.DataFrame) -> pd.Series:
    return df.isna().sum().sort_values(ascending=False)


def numeric_stats(df: pd.DataFrame) -> pd.DataFrame:
    num = df.select_dtypes(include="number")
    if num.empty:
        return pd.DataFrame()
    desc = num.describe().T  # count, mean, std, min, 25%, 50%, 75%, max
    return desc


def sample_rows(conn: sqlite3.Connection, table: str, limit: int = 10) -> pd.DataFrame:
    return pd.read_sql_query(f"SELECT * FROM [{table}] LIMIT {int(limit)};", conn)


def human_size(path: str) -> str:
    b = os.path.getsize(path)
    for unit in ["B","KB","MB","GB","TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def main():
    ap = argparse.ArgumentParser(description="Inspeciona um banco SQLite rapidamente.")
    ap.add_argument("--db", required=True, help="Caminho do arquivo .db")
    ap.add_argument("--table", help="Nome exato da tabela a inspecionar (opcional)")
    ap.add_argument("--like", help="Filtro LIKE para nomes de tabela (ex.: obj%%) (opcional)")
    ap.add_argument("--limit", type=int, default=10, help="Linhas de amostra por tabela (padrão: 10)")
    args = ap.parse_args()

    print(f"Arquivo: {args.db} ({human_size(args.db)})")
    conn = connect(args.db)

    # Tabelas
    tables = list_tables(conn, like=args.like)
    if not tables:
        print("Nenhuma tabela encontrada.")
        return

    # Se foi passada uma tabela específica, prioriza ela
    if args.table:
        if args.table not in tables:
            print(f"Tabela '{args.table}' não encontrada. Disponíveis: {', '.join(tables)}")
            return
        tables = [args.table]

    # Sumário
    print("\n== Sumário de Tabelas ==")
    for t in tables:
        try:
            n = count_rows(conn, t)
        except Exception as e:
            n = f"erro: {e}"
        print(f"- {t}: {n} linhas")

    # Detalhes
    for t in tables:
        print(f"\n====================\nTabela: {t}")
        # Schema
        try:
            schema = get_schema(conn, t)
            print("\nSchema (PRAGMA table_info):")
            print(indent(schema.to_string(index=False), "  "))
        except Exception as e:
            print(f"  Erro ao obter schema: {e}")

        # Índices
        try:
            idx = get_indexes(conn, t)
            print("\nÍndices:")
            if idx.empty:
                print("  (nenhum índice)")
            else:
                print(indent(idx.to_string(index=False), "  "))
        except Exception as e:
            print(f"  Erro ao obter índices: {e}")

        # Amostra
        try:
            df_sample = sample_rows(conn, t, limit=args.limit)
            print(f"\nAmostra (primeiras {args.limit} linhas):")
            print(indent(df_sample.head(args.limit).to_string(index=False), "  "))

            # Nulos por coluna
            print("\nNulos por coluna:")
            nc = null_counts(df_sample)
            print(indent(nc.to_string(), "  "))
            
            # Estatísticas numéricas
            stats = numeric_stats(df_sample)
            if not stats.empty:
                print("\nEstatísticas numéricas (amostra):")
                print(indent(stats.to_string(), "  "))
        except Exception as e:
            print(f"  Erro ao ler amostra: {e}")

    conn.close()
    print("\nFeito.")

if __name__ == "__main__":
    main()
    #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
check_nps_db.py
----------------
Diagnóstico completo de um banco SQLite de NPS.

Uso:
  python check_nps_db.py "/caminho/para/DBV Capital_NPS.db"

Se o caminho não for passado, o script tenta:
  - ./DBV Capital_NPS.db
  - ../DBV Capital_NPS.db
  - /mnt/data/DBV Capital_NPS.db
"""

import sys
import re
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import pandas as pd
import unicodedata


# ============== UTIL ==============

def strip_accents(txt: str) -> str:
    if txt is None:
        return ""
    return "".join(ch for ch in unicodedata.normalize("NFKD", str(txt)) if not unicodedata.combining(ch))


def norm_key(txt: str) -> str:
    s = strip_accents(str(txt)).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return re.sub(r"\s+", " ", s)


def find_db_path(cli_arg: Optional[str]) -> Optional[Path]:
    if cli_arg:
        p = Path(cli_arg)
        return p if p.exists() else None
    for p in [Path("DBV Capital_NPS.db"),
              Path(__file__).parent / "DBV Capital_NPS.db",
              Path(__file__).parent.parent / "DBV Capital_NPS.db",
              Path("/mnt/data/DBV Capital_NPS.db")]:
        if p.exists():
            return p
    return None


def print_h1(t: str):
    bar = "═" * len(t)
    print(f"\n{bar}\n{t}\n{bar}")


def print_h2(t: str):
    bar = "─" * len(t)
    print(f"\n{t}\n{bar}")


# ============== DESCOBERTA DE TABELA ==============

def best_table_for_nps(conn: sqlite3.Connection) -> Optional[str]:
    """
    Escolhe a "melhor" tabela com base na presença de colunas relevantes.
    """
    q = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    tabs = pd.read_sql_query(q, conn)["name"].astype(str).tolist()
    if not tabs:
        return None

    wanted = ['pesquisa', 'relacion', 'status', 'nota', 'assessor', 'codigo',
              'data', 'notifica', 'nps', 'survey']

    best, best_score = None, -1
    for t in tabs:
        cols = pd.read_sql_query(f'PRAGMA table_info("{t}")', conn)["name"].astype(str).tolist()
        norms = [norm_key(c) for c in cols]
        # score = quantas palavras-chave aparecem nas colunas
        score = sum(any(w in c for c in norms) for w in wanted)
        if score > best_score:
            best, best_score = t, score
    return best


def rename_nps_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza nomes típicos encontrados no banco de NPS.
    """
    if df.empty:
        return df
    rename = {}
    for c in df.columns:
        k = norm_key(c)
        if ('pesquisa' in k and 'relacion' in k) and 'pesquisa_relacionamento' not in rename.values():
            rename[c] = 'pesquisa_relacionamento'
        elif 'status' in k and 'status' not in rename.values():
            rename[c] = 'status'
        elif ('nota' in k or 'score' in k or 'nps' in k) and 'nota' not in rename.values():
            rename[c] = 'nota'
        elif ('codigo' in k and 'assessor' in k) and 'codigo_assessor' not in rename.values():
            rename[c] = 'codigo_assessor'
        elif ('data' in k and 'respost' in k) and 'data_resposta' not in rename.values():
            rename[c] = 'data_resposta'
        elif ('notifica' in k) and 'notificacao' not in rename.values():
            rename[c] = 'notificacao'
    return df.rename(columns=rename)


# ============== CHECK PRINCIPAL ==============

def check_db(db_path: Path, show_samples: int = 10) -> None:
    print_h1(f"CHECK DB – {db_path}")

    with sqlite3.connect(str(db_path)) as conn:
        # 1) Listar tabelas e contagens
        print_h2("Tabelas no banco")
        tabs_df = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;", conn
        )
        if tabs_df.empty:
            print("Nenhuma tabela encontrada.")
            return

        tables: List[str] = tabs_df["name"].astype(str).tolist()
        sizes: Dict[str, int] = {}
        for t in tables:
            try:
                cnt = pd.read_sql_query(f'SELECT COUNT(*) AS n FROM "{t}"', conn).iloc[0, 0]
            except Exception:
                cnt = -1
            sizes[t] = int(cnt) if pd.notna(cnt) else -1

        for t in tables:
            print(f" - {t:40s}  linhas: {sizes[t]}")

        # 2) Melhor tabela candidata
        candidate = best_table_for_nps(conn)
        print_h2("Melhor candidata para NPS")
        print(f"Tabela sugerida: {candidate}")

        if not candidate:
            print("Não foi possível sugerir uma tabela.")
            return

        # 3) Esquema da tabela
        print_h2(f"Esquema de colunas – {candidate}")
        schema = pd.read_sql_query(f'PRAGMA table_info("{candidate}")', conn)
        if not schema.empty:
            for _, r in schema.iterrows():
                print(f" - {r['name']:35s} tipo: {str(r['type'])}")

        # 4) Amostras
        print_h2(f"Amostra de {show_samples} linhas – {candidate}")
        try:
            amostra = pd.read_sql_query(f'SELECT * FROM "{candidate}" LIMIT {show_samples};', conn)
            with pd.option_context('display.max_columns', None,
                                   'display.width', 160,
                                   'display.max_colwidth', 80):
                print(amostra)
        except Exception as e:
            print(f"Falha ao ler amostra: {e}")

        # 5) Carregar tudo da candidata
        print_h2("Carregando tabela para análise…")
        df = pd.read_sql_query(f'SELECT * FROM "{candidate}"', conn)
        print(f"Linhas: {len(df)}, Colunas: {len(df.columns)}")

    # 6) Normalizar nomes
    df = rename_nps_columns(df)

    # 7) Mostrar colunas mapeadas e valores únicos (top 10) das mais relevantes
    print_h2("Colunas relevantes (mapeadas)")
    rel_cols = ['pesquisa_relacionamento', 'status', 'notificacao', 'nota',
                'codigo_assessor', 'data_resposta']
    for c in rel_cols:
        if c in df.columns:
            uniq = (df[c].dropna().astype(str).map(strip_accents).str.strip().unique())[:10]
            print(f" - {c:25s} | exemplos: {list(uniq)}")
        else:
            print(f" - {c:25s} (NÃO ENCONTRADA)")

    # 8) Normalizações auxiliares
    df['pesq_norm'] = df.get('pesquisa_relacionamento', "").astype(str).map(strip_accents).str.lower()
    df['status_norm'] = df.get('status', "").astype(str).map(strip_accents).str.lower().str.strip()
    df['notif_norm']  = df.get('notificacao', "").astype(str).map(strip_accents).str.lower().str.strip()

    # 9) Contagens específicas NPS – XP Aniversário
    print_h2("Contagens – Filtros XP / Aniversário")
    mask_xp_aniv = df['pesq_norm'].str.contains(r'\bxp\b', na=False) & df['pesq_norm'].str.contains('aniver', na=False)
    mask_so_aniv = df['pesq_norm'].str.contains('aniver', na=False)
    total_all    = len(df)
    total_xp_aniv = int(mask_xp_aniv.sum())
    total_so_aniv = int(mask_so_aniv.sum())

    print(f"Linhas totais na tabela: {total_all}")
    print(f"Linhas com (XP + Anivers*): {total_xp_aniv}")
    print(f"Linhas com (Anivers*) qualquer: {total_so_aniv}")

    # 10) Respondidos (status OU notificacao tem 'respond')
    has_resp_all = (
        df['status_norm'].str.contains('respond', na=False) |
        df['notif_norm'].str.contains('respond', na=False)
    )

    # Respondidos só dentro de XP+Anivers e dentro de Anivers (fallback)
    resp_xp_aniv  = int(has_resp_all[mask_xp_aniv].sum())
    resp_so_aniv  = int(has_resp_all[mask_so_aniv].sum())

    print("\nRespondidos (qualquer coluna com 'respond'):")
    print(f" - Dentro de (XP + Anivers*): {resp_xp_aniv} de {total_xp_aniv}")
    print(f" - Dentro de (Anivers*):      {resp_so_aniv} de {total_so_aniv}")

    ader_xp = (resp_xp_aniv / total_xp_aniv * 100.0) if total_xp_aniv > 0 else 0.0
    ader_an = (resp_so_aniv / total_so_aniv * 100.0) if total_so_aniv > 0 else 0.0
    print(f"Aderência (XP + Anivers*): {ader_xp:.2f}%")
    print(f"Aderência (Anivers*):      {ader_an:.2f}%")

    # 11) Frequências por status / notificacao
    def top_freq(series: pd.Series, topn: int = 12) -> List[Tuple[str, int]]:
        s = series.astype(str).map(strip_accents).str.strip().str.lower()
        vc = s.value_counts(dropna=True).head(topn)
        return list(zip(vc.index.tolist(), vc.values.tolist()))

    if 'status' in df.columns:
        print_h2("Top valores – status")
        for v, n in top_freq(df['status']):
            print(f" {v:40s}  {n}")

    if 'notificacao' in df.columns:
        print_h2("Top valores – notificacao")
        for v, n in top_freq(df['notificacao']):
            print(f" {v:40s}  {n}")

    # 12) Amostra de registros que entram no filtro (até 10)
    print_h2("Exemplos que entram em (XP + Anivers*) – até 10 linhas")
    cols_show = [c for c in ['pesquisa_relacionamento', 'status', 'notificacao', 'nota',
                             'codigo_assessor', 'data_resposta'] if c in df.columns]
    try:
        ex_xp = df.loc[mask_xp_aniv, cols_show].head(10)
        with pd.option_context('display.max_columns', None,
                               'display.width', 160,
                               'display.max_colwidth', 80):
            print(ex_xp)
    except Exception:
        print("(sem colunas para exibir)")

    print_h2("Exemplos que entram em (Anivers*) – até 10 linhas")
    try:
        ex_an = df.loc[mask_so_aniv, cols_show].head(10)
        with pd.option_context('display.max_columns', None,
                               'display.width', 160,
                               'display.max_colwidth', 80):
            print(ex_an)
    except Exception:
        print("(sem colunas para exibir)")

    print_h1("FIM DO CHECK")


# ============== MAIN ==============

if __name__ == "__main__":
    arg_path = sys.argv[1] if len(sys.argv) >= 2 else None
    dbp = find_db_path(arg_path)
    if not dbp:
        print("❌ Banco não encontrado. Informe o caminho como argumento ou coloque o arquivo em ./, ../ ou /mnt/data")
        sys.exit(1)
    try:
        check_db(dbp)
    except Exception as e:
        print(f"❌ Erro durante o check: {e}")
        raise

