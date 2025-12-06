from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..db import SessionLocal
from .. import models, schemas
from ..ai import plan_query, summarize_results
from ..query.builder import build_sql_from_plan


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=schemas.MessageOut)
def chat_endpoint(payload: schemas.MessageCreate, db: Session = Depends(get_db)):
    """
    Main chat endpoint using built-in planner and summarizer (no external AI).
    """
    question = payload.message
    conv_id = payload.conversation_id

    # Ensure conversation
    if conv_id:
        conversation = (
            db.query(models.Conversation)
            .filter(models.Conversation.id == conv_id)
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = models.Conversation()
        db.add(conversation)
        db.flush()
        conv_id = conversation.id

    # Store user message
    user_msg = models.Message(
        conversation_id=conv_id,
        role="user",
        text=question,
    )
    db.add(user_msg)
    db.flush()

    # Build plan & SQL
    plan = plan_query(question)
    sql, params = build_sql_from_plan(plan)

    # Execute read-only query
    result = db.execute(text(sql), params)
    rows = [dict(r._mapping) for r in result]

    # Summarize
    summary = summarize_results(question, sql, rows)
    answer_text = summary["answer_text"]
    query_text = summary["query_text"]

    # Store assistant message
    assistant_msg = models.Message(
        conversation_id=conv_id,
        role="assistant",
        text=answer_text,
        query_text=query_text,
        rows_json=rows,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg
