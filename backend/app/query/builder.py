# # from typing import Any, Dict, List, Tuple


# # ALLOWED_TABLES = {"students", "assignments", "student_assignments"}


# # def _default_plan() -> Dict[str, Any]:
# #     return {
# #         "entity": "student_assignments",
# #         "select": [
# #             "students.first_name",
# #             "students.last_name",
# #             "assignments.title",
# #             "assignments.due_date",
# #             "student_assignments.status",
# #             "student_assignments.score",
# #         ],
# #         "joins": [
# #             {"from": "student_assignments.student_id", "to": "students.id"},
# #             {"from": "student_assignments.assignment_id", "to": "assignments.id"},
# #         ],
# #         "filters": [],
# #         "limit": 20,
# #     }


# # def _is_valid_qualified(col: str) -> bool:
# #     """
# #     Ensure column is like 'table.column' and table is allowed.
# #     """
# #     if "." not in col:
# #         return False
# #     table, _ = col.split(".", 1)
# #     return table in ALLOWED_TABLES


# # def _sanitize_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
# #     """
# #     Ensure the plan only uses allowed tables and fully-qualified column names.
# #     If something looks wrong (aliases, unknown tables, unqualified names),
# #     fall back to a safe default plan.
# #     """
# #     try:
# #         entity = plan.get("entity", "student_assignments")
# #         if entity not in ALLOWED_TABLES:
# #             return _default_plan()

# #         selects = plan.get("select") or ["*"]
# #         joins = plan.get("joins", [])
# #         filters = plan.get("filters", [])

# #         # Validate SELECT
# #         for col in selects:
# #             if col != "*" and not _is_valid_qualified(col):
# #                 return _default_plan()

# #         # Validate JOINs
# #         for j in joins:
# #             from_col = j.get("from")
# #             to_col = j.get("to")
# #             if not from_col or not to_col:
# #                 return _default_plan()
# #             if not _is_valid_qualified(from_col) or not _is_valid_qualified(to_col):
# #                 return _default_plan()

# #         # Validate filters
# #         for f in filters:
# #             field = f.get("field")
# #             if field and not _is_valid_qualified(field):
# #                 return _default_plan()

# #         # Clamp limit
# #         limit = int(plan.get("limit", 20))
# #         if limit <= 0 or limit > 500:
# #             plan["limit"] = 20

# #         return plan
# #     except Exception:
# #         return _default_plan()


# # def build_sql_from_plan(plan: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
# #     """
# #     Convert a query plan dict into a parameterized SQL SELECT statement.

# #     Returns:
# #       sql:   "SELECT ... FROM ... JOIN ... WHERE ... LIMIT ..."
# #       params: dict of {name: value} for SQLAlchemy text() binding.
# #     """
# #     plan = _sanitize_plan(plan)

# #     base = plan.get("entity", "student_assignments")
# #     select_cols = plan.get("select") or ["*"]
# #     joins = plan.get("joins", [])
# #     filters = plan.get("filters", [])
# #     limit = int(plan.get("limit", 20))

# #     select_clause = ", ".join(select_cols)
# #     sql = f"SELECT {select_clause} FROM {base}"

# #     for j in joins:
# #         from_col = j.get("from")
# #         to_col = j.get("to")
# #         to_table = to_col.split(".")[0]
# #         sql += f" INNER JOIN {to_table} ON {from_col} = {to_col}"

# #     params: Dict[str, Any] = {}
# #     conditions: List[str] = []

# #     for idx, f in enumerate(filters):
# #         field = f.get("field")
# #         operator = (f.get("operator") or "=").upper().strip()
# #         value = f.get("value")

# #         if not field:
# #             continue

# #         if operator not in ("=", ">", "<", ">=", "<=", "!=", "LIKE", "ILIKE"):
# #             operator = "="

# #         name = f"p{idx}"
# #         conditions.append(f"{field} {operator} :{name}")
# #         params[name] = value

# #     if conditions:
# #         sql += " WHERE " + " AND ".join(conditions)

# #     if limit <= 0 or limit > 500:
# #         limit = 20
# #     sql += f" LIMIT {limit}"

# #     return sql, params


# # app/query/builder.py
# from typing import Dict, Any, List, Tuple
# from app.schema_loader import DB_SCHEMA


# def build_sql_from_plan(plan: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
#     entity = plan["entity"]
#     selects = plan.get("select", ["*"])
#     filters = plan.get("filters", [])
#     limit = plan.get("limit", 20)

#     # Validate columns
#     valid_tables = DB_SCHEMA["columns"].keys()

#     for col in selects:
#         if col != "*":
#             t, c = col.split(".")
#             if t not in valid_tables or c not in DB_SCHEMA["columns"][t]:
#                 raise ValueError(f"Invalid column: {col}")

#     # Build SELECT
#     select_sql = ", ".join(selects)
#     sql = f"SELECT {select_sql} FROM {entity}"

#     # AUTO-JOIN based on FK graph
#     # Breadth-first FK traversal
#     joined = {entity}
#     fk_edges = DB_SCHEMA["foreign_keys"]

#     added = True
#     while added:
#         added = False
#         for fk in fk_edges:
#             # Join from entity → other tables automatically
#             if fk["from_table"] in joined and fk["to_table"] not in joined:
#                 sql += (
#                     f" LEFT JOIN {fk['to_table']}"
#                     f" ON {fk['from_table']}.{fk['from_col']} = "
#                     f"{fk['to_table']}.{fk['to_col']}"
#                 )
#                 joined.add(fk["to_table"])
#                 added = True

#             elif fk["to_table"] in joined and fk["from_table"] not in joined:
#                 sql += (
#                     f" LEFT JOIN {fk['from_table']}"
#                     f" ON {fk['from_table']}.{fk['from_col']} = "
#                     f"{fk['to_table']}.{fk['to_col']}"
#                 )
#                 joined.add(fk["from_table"])
#                 added = True

#     # WHERE clause
#     params = {}
#     where_clauses = []

#     for idx, f in enumerate(filters):
#         field = f["field"]
#         op = f.get("operator", "=")
#         val = f["value"]

#         t, c = field.split(".")
#         if c not in DB_SCHEMA["columns"][t]:
#             raise ValueError(f"Invalid filter field {field}")

#         pname = f"p{idx}"
#         params[pname] = val
#         where_clauses.append(f"{field} {op} :{pname}")

#     if where_clauses:
#         sql += " WHERE " + " AND ".join(where_clauses)

#     sql += f" LIMIT {limit}"

#     return sql, params

# app/query/builder.py

from typing import Dict, Any, Tuple, List
from app.schema_loader import DB_SCHEMA


def validate_column(col: str) -> bool:
    """Check table.column exists in schema."""
    if "." not in col:
        return False

    table, column = col.split(".", 1)
    return table in DB_SCHEMA["columns"] and column in DB_SCHEMA["columns"][table]


def validate_table(table: str) -> bool:
    """Check table exists in schema."""
    return table in DB_SCHEMA["tables"]


def build_sql_from_plan(plan: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Convert a normalized plan dictionary into a safe SQL SELECT query.

    Plan format:
    {
        "entity": "<table>",
        "select": ["table.column", ...],
        "filters": [{ "field": "table.column", "operator": "=", "value": "abc" }],
        "limit": 50
    }
    """

    entity = plan.get("entity")
    selects = plan.get("select", ["*"])
    filters = plan.get("filters", [])
    limit = plan.get("limit", 50)

    # Validate base table
    if not validate_table(entity):
        raise ValueError(f"Invalid entity/table in plan: {entity}")

    # Validate SELECT columns
    for col in selects:
        if col != "*" and not validate_column(col):
            raise ValueError(f"Invalid SELECT column: {col}")

    # Base SELECT clause
    select_sql = ", ".join(selects)
    sql = f"SELECT {select_sql} FROM {entity}"

    # Prepare auto join graph from schema loader foreign keys
    fks = DB_SCHEMA["foreign_keys"]

    # Automatically connect related tables
    joined_tables = {entity}
    added = True

    while added:
        added = False

        for fk in fks:
            ft, fc = fk["from_table"], fk["from_col"]
            tt, tc = fk["to_table"], fk["to_col"]

            # CASE 1 — join from -> to
            if ft in joined_tables and tt not in joined_tables:
                sql += f" LEFT JOIN {tt} ON {ft}.{fc} = {tt}.{tc}"
                joined_tables.add(tt)
                added = True

            # CASE 2 — join to -> from
            elif tt in joined_tables and ft not in joined_tables:
                sql += f" LEFT JOIN {ft} ON {ft}.{fc} = {tt}.{tc}"
                joined_tables.add(ft)
                added = True

    # Prepare WHERE clause
    params = {}
    where_clauses: List[str] = []

    for idx, f in enumerate(filters):
        field = f.get("field")
        operator = f.get("operator", "=").upper()
        value = f.get("value")

        if not validate_column(field):
            raise ValueError(f"Invalid filter column: {field}")

        # Validate allowed operators
        if operator not in ["=", "!=", ">", "<", ">=", "<=", "LIKE", "ILIKE", "IN", "NOT IN", "IS NULL", "IS NOT NULL"]:
            operator = "="

        param_name = f"p{idx}"
        
        # Handle NULL operators (no value needed)
        if operator in ["IS NULL", "IS NOT NULL"]:
            where_clauses.append(f"{field} {operator}")
        # Handle IN/NOT IN (value should be a list)
        elif operator in ["IN", "NOT IN"]:
            params[param_name] = tuple(value) if isinstance(value, list) else (value,)
            where_clauses.append(f"{field} {operator} :{param_name}")
        else:
            # Special handling for ILIKE because SQLite doesn't support it natively
            if operator == "ILIKE":
                # Case-insensitive match using LOWER(...)
                params[param_name] = str(value).lower()
                where_clauses.append(f"LOWER({field}) LIKE :{param_name}")
            else:
                params[param_name] = value
                where_clauses.append(f"{field} {operator} :{param_name}")

    # Apply WHERE if needed
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    # LIMIT safety
    try:
        limit = int(limit)
    except:
        limit = 50

    if not (1 <= limit <= 500):
        limit = 50

    sql += f" LIMIT {limit}"

    return sql, params


def apply_filters(query, filters, model_map):
    """Apply WHERE conditions."""
    for flt in filters:
        field = flt.get("field", "")
        operator = flt.get("operator", "=").upper()
        value = flt.get("value")

        if "." not in field:
            continue

        table_name, col_name = field.split(".", 1)
        model_cls = model_map.get(table_name)
        if not model_cls or not hasattr(model_cls, col_name):
            continue

        column = getattr(model_cls, col_name)

        # Apply operator
        if operator == "=":
            query = query.filter(column == value)
        elif operator == "!=":
            query = query.filter(column != value)
        elif operator == ">":
            query = query.filter(column > value)
        elif operator == "<":
            query = query.filter(column < value)
        elif operator == ">=":
            query = query.filter(column >= value)
        elif operator == "<=":
            query = query.filter(column <= value)
        elif operator == "LIKE":
            query = query.filter(column.like(value))
        elif operator == "ILIKE":
    # SQLite-safe case-insensitive filtering
            query = query.filter(column.like(value.lower())).filter(column != None)
        else:
            # Default to equality
            query = query.filter(column == value)
    print(query)
    return query
