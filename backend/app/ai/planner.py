# app/ai/planner.py
import os
import json
from dotenv import load_dotenv
from groq import Groq
from app.schema_loader import DB_SCHEMA

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def plan_query(question: str):
    schema_text = json.dumps(DB_SCHEMA, indent=2)

    prompt = f"""
You are an AI query planner. 
Your goal is to convert natural language into a JSON query plan for a SQL engine.

Below is the entire database schema (tables, columns, foreign keys):
{schema_text}

=========================
STRICT INSTRUCTIONS
=========================

1. OUTPUT MUST BE VALID JSON ONLY.
   No commentary, no markdown, no explanations, no SQL queries.

2. JSON MUST include ALL these keys:

{{
  "entity": "<table name>",
  "select": ["table.column", ...],
  "filters": [
      {{"field": "table.column", "operator": "ILIKE", "value": "%abc%"}}
  ],
  "limit": 50
}}

3. DO NOT INCLUDE ANY "joins" FIELD.
   The server automatically builds JOINs using foreign keys.

4. "entity" MUST be one of the tables in the schema.

5. "select" MUST contain fully qualified column names: "table.column".
   Use EXACT column names from schema above.

6. For text searches (names, titles, descriptions):
   - Use "ILIKE" operator for case-insensitive matching
   - Use %...% wildcards for partial matches.

7. For exact matches (IDs, numbers, dates): Use "=" operator.

8. Allowed operators: =, !=, >, <, >=, <=, LIKE, ILIKE.

=========================

User question:
"{question}"

Return ONLY valid JSON.
"""

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = resp.choices[0].message.content

    # Try to parse JSON from the model
    try:
        plan = json.loads(content)
    except Exception:
        plan = {}

    # ---- SAFE FALLBACK (NO list()[0]) ----
    tables = DB_SCHEMA.get("tables") or []

    # Reasonable default entity
    default_entity = "student_assignments"
    if tables:
        default_entity = tables[0]

    plan.setdefault("entity", default_entity)
    plan.setdefault("select", ["*"])
    plan.setdefault("filters", [])
    plan.setdefault("limit", 20)

    return plan
