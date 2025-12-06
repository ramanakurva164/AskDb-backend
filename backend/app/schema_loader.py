# app/schema_loader.py
from sqlalchemy import inspect
from .db import engine, Base
from . import models  # noqa: F401  make sure models are imported so tables exist


def load_schema():
    # Ensure all tables defined in models.py are created
    Base.metadata.create_all(bind=engine)

    insp = inspect(engine)

    tables = insp.get_table_names()
    columns = {}
    foreign_keys = []

    for table in tables:
        cols = insp.get_columns(table)
        columns[table] = [c["name"] for c in cols]

        fks = insp.get_foreign_keys(table)
        for fk in fks:
            foreign_keys.append(
                {
                    "from_table": table,
                    "from_col": fk["constrained_columns"][0],
                    "to_table": fk["referred_table"],
                    "to_col": fk["referred_columns"][0],
                }
            )

    return {
        "tables": tables,
        "columns": columns,
        "foreign_keys": foreign_keys,
    }


DB_SCHEMA = load_schema()
