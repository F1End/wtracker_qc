#!/usr/bin/env python3

import sys
import sqlite3

# Exit codes
EXIT_OK = 0
EXIT_EMPTY_CELLS_FOUND = 42
EXIT_RUNTIME_ERROR = 1


def table_has_empty_cells_strict(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()

    conditions = []
    for _, name, col_type, *_ in columns_info:
        conditions.append(f"{name} IS NULL")
        if col_type and ("CHAR" in col_type.upper() or "TEXT" in col_type.upper()):
            conditions.append(f"{name} = ''")

    if not conditions:
        return False  # no columns to check

    where_clause = " OR ".join(conditions)

    query = f"""
        SELECT EXISTS(
            SELECT 1 FROM {table_name}
            WHERE {where_clause}
            LIMIT 1
        )
    """

    cursor.execute(query)
    return bool(cursor.fetchone()[0])


def main():
    if len(sys.argv) != 2:
        print("Usage: check_empty_cells.py <database_file>")
        sys.exit(EXIT_RUNTIME_ERROR)

    db_path = sys.argv[1]

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%';
        """)
        tables = [row[0] for row in cursor.fetchall()]

        tables_with_issues = []

        for table in tables:
            try:
                if table_has_empty_cells_strict(cursor, table):
                    tables_with_issues.append(table)
            except Exception as e:
                print(f"Error checking table '{table}': {e}", file=sys.stderr)
                sys.exit(EXIT_RUNTIME_ERROR)

        if tables_with_issues:
            print("Empty cells found in the following tables:")
            for t in tables_with_issues:
                print(f" - {t}")
            sys.exit(EXIT_EMPTY_CELLS_FOUND)

        sys.exit(EXIT_OK)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(EXIT_RUNTIME_ERROR)

    finally:
        try:
            conn.close()
        except:
            pass


if __name__ == "__main__":
    main()