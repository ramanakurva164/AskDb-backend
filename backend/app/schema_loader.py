# app/schema_loader.py
from sqlalchemy import inspect
from .db import engine

def load_schema():
    insp = inspect(engine)

    tables = insp.get_table_names()
    columns = {}
    foreign_keys = []

    for table in tables:
        # collect columns
        cols = insp.get_columns(table)
        columns[table] = [c["name"] for c in cols]

        # collect FKs
        fks = insp.get_foreign_keys(table)
        for fk in fks:
            foreign_keys.append({
                "from_table": table,
                "from_col": fk["constrained_columns"][0],
                "to_table": fk["referred_table"],
                "to_col": fk["referred_columns"][0]
            })

    return {
        "tables": tables,
        "columns": columns,
        "foreign_keys": foreign_keys
    }

# Load once at startup
DB_SCHEMA = load_schema()
