from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import SessionLocal
from .. import models, schemas


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/{conversation_id}", response_model=schemas.ConversationOut)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conversation = (
        db.query(models.Conversation)
        .filter(models.Conversation.id == conversation_id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.messages.sort(key=lambda m: m.created_at)
    return conversation
