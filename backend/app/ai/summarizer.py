# app/ai/summarizer.py
import os
import json
from typing import Any, Dict, List
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def summarize_results(
    question: str,
    sql: str,
    rows: List[Dict[str, Any]],
) -> Dict[str, str]:
    """
    Use Groq to turn raw SQL results into a user-friendly answer.

    Returns:
      {
        "answer_text": "...",  # what user sees as the chat reply
        "query_text": "..."    # short conceptual description of the query
      }
    """

    prompt = f"""
You are an assistant summarizing query results from a student-assignment database.

User question:
\"\"\"{question}\"\"\"

SQL query that was executed (read-only):
{sql}

Rows returned (JSON array):
{json.dumps(rows)[:6000]}

1. Write a short, clear answer for the user (1–3 sentences).
   Focus on students, assignments, due dates, status, and scores
   if present.

2. Write a short conceptual description of the query in plain language
   (1–2 lines), without using SQL keywords. Example:
   "I looked up all assignments for Riya that are due this week."

Return ONLY valid JSON, no markdown or commentary, like:

{{
  "answer_text": "natural language answer here",
  "query_text": "conceptual description of the query here"
}}
"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = completion.choices[0].message.content.strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = {
            "answer_text": "Here are the results based on your question.",
            "query_text": "A read-only query over the student assignments joined with students and assignments.",
        }

    answer_text = data.get(
        "answer_text",
        "Here are the results based on your question.",
    )
    query_text = data.get(
        "query_text",
        "A read-only query over the student assignments joined with students and assignments.",
    )

    return {"answer_text": answer_text, "query_text": query_text}
