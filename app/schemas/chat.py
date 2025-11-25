# app/schemas/chat.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ConversationBase(BaseModel):
    id: int
    owner_id: int
    student_id: int
    created_at: datetime

    owner_name: Optional[str] = None
    student_name: Optional[str] = None
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    content: str
    created_at: datetime

    sender_name: Optional[str] = None

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    conversation_id: int
    content: str
