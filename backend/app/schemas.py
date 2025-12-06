from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel


class MessageCreate(BaseModel):
    """Payload from frontend when user sends a new message."""
    conversation_id: Optional[str] = None
    message: str


class MessageBase(BaseModel):
    role: str
    text: str
    query_text: Optional[str] = None
    rows_json: Optional[Any] = None


class MessageOut(MessageBase):
    """Returned to frontend for display."""
    id: str
    conversation_id: str
    created_at: datetime

    class Config:
        orm_mode = True


class ConversationOut(BaseModel):
    """Full conversation with messages."""
    id: str
    created_at: datetime
    messages: List[MessageOut] = []

    class Config:
        orm_mode = True
