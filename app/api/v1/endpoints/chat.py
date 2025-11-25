# app/api/v1/endpoints/chat.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_db, get_current_user, require_role
from app.models.chat import Conversation, Message
from app.models.user import User, UserRole
from app.schemas.chat import ConversationBase, MessageOut, MessageCreate

router = APIRouter()

# 👉 1) Obtener o crear conversación OWNER ↔ STUDENT
@router.post("/conversations/by-users", response_model=ConversationBase)
def get_or_create_conversation(
    owner_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current = Depends(get_current_user),
):
    # Seguridad básica: solo owner, student o superadmin pueden abrir esta conversación
    if current.role != UserRole.SUPERADMIN and current.id not in [owner_id, student_id]:
        raise HTTPException(status_code=403, detail="No autorizado")

    convo = (
        db.query(Conversation)
        .filter(
            Conversation.owner_id == owner_id,
            Conversation.student_id == student_id,
        )
        .first()
    )
    if not convo:
        convo = Conversation(owner_id=owner_id, student_id=student_id)
        db.add(convo)
        db.commit()
        db.refresh(convo)

    # datos extra (nombres + último mensaje)
    owner = db.query(User).get(convo.owner_id)
    student = db.query(User).get(convo.student_id)
    last_msg = (
        db.query(Message)
        .filter(Message.conversation_id == convo.id)
        .order_by(desc(Message.created_at))
        .first()
    )

    return ConversationBase(
        id=convo.id,
        owner_id=convo.owner_id,
        student_id=convo.student_id,
        created_at=convo.created_at,
        owner_name=owner.full_name if owner else None,
        student_name=student.full_name if student else None,
        last_message=last_msg.content if last_msg else None,
        last_message_at=last_msg.created_at if last_msg else None,
    )


# 👉 2) Listar conversaciones del usuario actual
@router.get("/conversations", response_model=List[ConversationBase])
def list_my_conversations(
    db: Session = Depends(get_db),
    current = Depends(get_current_user),
):
    q = db.query(Conversation)

    if current.role == UserRole.OWNER:
        q = q.filter(Conversation.owner_id == current.id)
    elif current.role == UserRole.STUDENT:
        q = q.filter(Conversation.student_id == current.id)
    elif current.role == UserRole.SUPERADMIN:
        # ve todos los chats
        pass
    else:
        return []

    convos = q.order_by(desc(Conversation.created_at)).all()

    results: List[ConversationBase] = []
    for c in convos:
        owner = db.query(User).get(c.owner_id)
        student = db.query(User).get(c.student_id)
        last_msg = (
            db.query(Message)
            .filter(Message.conversation_id == c.id)
            .order_by(desc(Message.created_at))
            .first()
        )
        results.append(
            ConversationBase(
                id=c.id,
                owner_id=c.owner_id,
                student_id=c.student_id,
                created_at=c.created_at,
                owner_name=owner.full_name if owner else None,
                student_name=student.full_name if student else None,
                last_message=last_msg.content if last_msg else None,
                last_message_at=last_msg.created_at if last_msg else None,
            )
        )
    return results


# 👉 3) Listar mensajes de una conversación
@router.get("/messages/{conversation_id}", response_model=List[MessageOut])
def list_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current = Depends(get_current_user),
):
    convo = db.query(Conversation).get(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    if current.role != UserRole.SUPERADMIN and current.id not in [convo.owner_id, convo.student_id]:
        raise HTTPException(status_code=403, detail="No autorizado")

    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    result: List[MessageOut] = []
    for m in msgs:
        sender = db.query(User).get(m.sender_id)
        result.append(
            MessageOut(
                id=m.id,
                conversation_id=m.conversation_id,
                sender_id=m.sender_id,
                content=m.content,
                created_at=m.created_at,
                sender_name=sender.full_name if sender else None,
            )
        )
    return result


# 👉 4) Enviar mensaje
@router.post("/messages", response_model=MessageOut)
def send_message(
    data: MessageCreate,
    db: Session = Depends(get_db),
    current = Depends(get_current_user),
):
    convo = db.query(Conversation).get(data.conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    if current.role != UserRole.SUPERADMIN and current.id not in [convo.owner_id, convo.student_id]:
        raise HTTPException(status_code=403, detail="No autorizado")

    msg = Message(
        conversation_id=data.conversation_id,
        sender_id=current.id,
        content=data.content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    sender = db.query(User).get(msg.sender_id)

    return MessageOut(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        content=msg.content,
        created_at=msg.created_at,
        sender_name=sender.full_name if sender else None,
    )
