import os
import json
from typing import Any, Dict, List
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def detect_key_fields(rows: List[Dict[str, Any]]) -> List[str]:
    """
    Extracts the most important keys dynamically from rows.
    Helps summarizer understand what's relevant.
    """
    if not rows:
        return []

    # Count key frequency across rows
    key_freq = {}
    for row in rows:
        for k in row.keys():
            key_freq[k] = key_freq.get(k, 0) + 1

    # Return keys sorted by frequency (most important first)
    return sorted(key_freq.keys(), key=lambda k: -key_freq[k])


def summarize_results(question: str, sql: str, rows: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Fully dynamic summarizer which adapts to ANY database schema.
    It analyzes the returned rows and writes human-friendly summaries
    regardless of table type.
    """

    # Empty results → clean natural answer
    if not rows:
        return {
            "answer_text": f"No data was found for your query: '{question}'.",
            "query_text": "A lookup was performed but no matching results were found."
        }

    # Dynamically detect key fields (VERY IMPORTANT)
    key_fields = detect_key_fields(rows)

    prompt = f"""
You are a universal database result summarizer.

Your job: Given the user's question, SQL executed, and dynamic row data,
generate a natural-language explanation. The database may contain ANY tables.
Never assume specific fields like "students" or "assignments".

User question:
\"\"\"{question}\"\"\"

SQL executed:
{sql}

Returned rows (JSON):
{json.dumps(rows)[:7000]}

Detected key fields in the result:
{key_fields}

======================
SUMMARY REQUIREMENTS
======================

1. "answer_text":
   - Summarize the rows in 1–3 sentences.
   - Use the detected key fields to understand the data.
   - If multiple rows, describe patterns (counts, common fields).
   - If single row, summarize key details.
   - DO NOT assume domain knowledge (students, assignments, etc.).
   - Let the content of rows guide the summary.

2. "query_text":
   - Describe what the SQL query achieved conceptually.
   - Mention the table(s) represented by row fields.
   - Stay generic: “I looked up records matching your criteria.”

3. OUTPUT RULES:
   - Return ONLY valid JSON (no markdown, no commentary).
   - JSON must be exactly:

{{
  "answer_text": "...",
  "query_text": "..."
}}

======================
GENERATE OUTPUT NOW
======================
"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25,
    )

    content = completion.choices[0].message.content.strip()

    # Parse JSON
    try:
        data = json.loads(content)
    except Exception:
        # Fully dynamic fallback (no hardcoding!)
        row_count = len(rows)
        fields = detect_key_fields(rows)
        answer = f"{row_count} record(s) were found. Important fields detected include: {fields}."
        query_desc = "A general lookup was executed and results were summarized based on returned fields."

        return {"answer_text": answer, "query_text": query_desc}

    # Guarantee fields exist
    return {
        "answer_text": data.get(
            "answer_text",
            f"{len(rows)} record(s) found containing fields: {detect_key_fields(rows)}."
        ),
        "query_text": data.get(
            "query_text",
            "A general lookup was performed and summarized."
        )
    }
