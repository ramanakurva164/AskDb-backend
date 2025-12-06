# # app/ai/planner.py
# import os
# import json
# from typing import Any, Dict
# from dotenv import load_dotenv
# from groq import Groq

# load_dotenv()

# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# SCHEMA_DESCRIPTION = """
# We have three tables:

# 1) students(
#     id,
#     first_name,
#     last_name,
#     email,
#     enrollment_date,
#     class,
#     section,
#     roll_number
# )

# 2) assignments(
#     id,
#     title,
#     description,
#     due_date,
#     subject,
#     course
# )

# 3) student_assignments(
#     id,
#     student_id,
#     assignment_id,
#     time_taken_minutes,
#     status,
#     score,
#     submitted_at
# )

# student_assignments joins students and assignments.

# IMPORTANT:
# - You must ONLY generate READ-ONLY queries.
# - No INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, etc.
# - Only SELECT-style filters and joins.
# """


# def plan_query(question: str) -> Dict[str, Any]:
#     """
#     Use Groq LLM to create a JSON query plan from a natural language question.

#     Expected JSON shape:

#     {
#       "entity": "student_assignments" | "students" | "assignments",
#       "select": ["students.first_name", "assignments.title", ...],
#       "joins": [
#         { "from": "student_assignments.student_id", "to": "students.id" },
#         { "from": "student_assignments.assignment_id", "to": "assignments.id" }
#       ],
#       "filters": [
#         { "field": "students.first_name", "operator": "=", "value": "Riya" }
#       ],
#       "limit": 50
#     }
#     """

#     prompt = f"""
# You are a query planner for a student-assignment database.

# {SCHEMA_DESCRIPTION}

# CRITICAL RULES:
# - Only use these exact table names: "students", "assignments", "student_assignments".
# - NEVER use table aliases like "s", "sa", "a", etc.
# - In "select" and "filters", ALWAYS use fully qualified column names like
#   "students.first_name", "assignments.title", "student_assignments.status".
# - In "joins", "from" and "to" MUST always be fully qualified column names,
#   e.g. "student_assignments.student_id" and "students.id".
#   Almost always, "entity" should be "student_assignments" because it joins students and assignments.

# User question:
# \"\"\"{question}\"\"\"

# Return ONLY valid JSON (no markdown, no commentary, no backticks).
# The JSON must have exactly these keys:

# - "entity": one of "student_assignments", "students", "assignments"
# - "select": array of fully qualified column names to select
# - "joins": array of objects with "from" and "to" (JOIN conditions)
# - "filters": array of objects with "field", "operator", "value"
# - "limit": integer (max rows to return, default 50)

# If the question is vague, choose a reasonable default plan over
# student_assignments joined with students and assignments.
# """


#     completion = client.chat.completions.create(
#         model="compound-beta",  # or "llama3-70b-8192" if you want
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0,
#     )

#     content = completion.choices[0].message.content.strip()

#     try:
#         plan = json.loads(content)
#     except json.JSONDecodeError:
#         # Fallback safe default plan
#         plan = {
#             "entity": "student_assignments",
#             "select": [
#                 "students.first_name",
#                 "students.last_name",
#                 "assignments.title",
#                 "assignments.due_date",
#                 "student_assignments.status",
#                 "student_assignments.score",
#             ],
#             "joins": [
#                 {"from": "student_assignments.student_id", "to": "students.id"},
#                 {"from": "student_assignments.assignment_id", "to": "assignments.id"},
#             ],
#             "filters": [],
#             "limit": 20,
#         }

#     # Safety defaults if keys missing
#     plan.setdefault("entity", "student_assignments")
#     plan.setdefault("select", ["*"])
#     plan.setdefault("joins", [])
#     plan.setdefault("filters", [])
#     plan.setdefault("limit", 20)

#     return plan


# app/ai/planner.py
# import os, json
# from dotenv import load_dotenv
# from groq import Groq
# from app.schema_loader import DB_SCHEMA

# load_dotenv()
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# def plan_query(question: str):
#     schema_text = json.dumps(DB_SCHEMA, indent=2)

#     prompt = f"""
# You are an intelligent SQL query planner.

# Here is the database schema including ALL tables, ALL columns, and ALL foreign keys:
# {schema_text}

# Your task:
# Given the user question below, produce a JSON query plan with:

# - "entity": the main table to select from (MUST be one of the tables above)
# - "select": list of fully qualified columns (table.column)
# - "filters": each filter object must have: field, operator, value
# - "limit": integer
# - DO NOT include JOINs — the server will handle them automatically.

# User question:
# \"\"\"{question}\"\"\"

# Return ONLY valid JSON with no extra text.
# """

#     resp = client.chat.completions.create(
#         model="llama-3.3-70b-versatile",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0
#     )

#     content = resp.choices[0].message.content

#     try:
#         return json.loads(content)
#     except:
#         return {
#             "entity": list(DB_SCHEMA["tables"])[0],
#             "select": ["*"],
#             "filters": [],
#             "limit": 20,
#         }

# app/ai/planner.py
import os, json
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
        temperature=0
    )

    content = resp.choices[0].message.content

    # Parse JSON safely
    try:
        plan = json.loads(content)
    except Exception:
        fallback_table = list(DB_SCHEMA["tables"])[0]
        return {
            "entity": fallback_table,
            "select": ["*"],
            "filters": [],
            "limit": 20,
        }
    tables = DB_SCHEMA.get("tables", [])
    default_entity = "student_assignments"
    if tables:
        default_entity = tables[0]

    plan.setdefault("entity", default_entity)
    plan.setdefault("select", ["*"])
    plan.setdefault("filters", [])
    plan.setdefault("limit", 20)

    return plan
  
