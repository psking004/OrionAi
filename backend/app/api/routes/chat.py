from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.message import Message
from app.db.schemas.message import MessageCreate, MessageResponse
from app.api.deps import get_current_user
from app.services.project_service import get_project

router = APIRouter(prefix="/projects", tags=["chat"])


@router.post("/{project_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def add_message(
    project_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project(db, project_id=project_id, owner_id=current_user.id)

    msg = Message(
        project_id=project_id,
        role=payload.role,
        content=payload.content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@router.get("/{project_id}/messages", response_model=List[MessageResponse])
def get_messages(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project(db, project_id=project_id, owner_id=current_user.id)

    messages = (
        db.query(Message)
        .filter(Message.project_id == project_id)
        .order_by(Message.timestamp.desc())
        .limit(10)
        .all()
    )
    return list(reversed(messages))
