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
   For student names, use "students.first_name" and "students.last_name", NOT "students.name"

6. For text searches (names, titles, descriptions):
   - Use "ILIKE" operator for case-insensitive matching
   - For partial name matching, use: {{"field": "students.first_name", "operator": "ILIKE", "value": "%riya%"}}
   - For full name search, search BOTH first_name and last_name separately
   
7. For exact matches (IDs, numbers, dates): Use "=" operator

8. Allowed operators: =, !=, >, <, >=, <=, LIKE, ILIKE

9. When searching for a person by name:
   - Always use ILIKE with % wildcards
   - Search first_name OR last_name (create separate filters)
   - Example: searching "riya" should create filter for first_name ILIKE '%riya%'

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
    tables = list(DB_SCHEMA["tables"])[0] 

    # Reasonable default entity
   
    
    default_entity = list(DB_SCHEMA["tables"])[0]

    plan.setdefault("entity", default_entity)
    plan.setdefault("select", ["*"])
    plan.setdefault("filters", [])
    plan.setdefault("limit", 20)

    return plan
