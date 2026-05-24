from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.message import Message
from app.db.models.status import ProjectStatus


def get_project_context(db: Session, project_id: int, limit: int = 20) -> Dict[str, Any]:
    messages = (
        db.query(Message)
        .filter(Message.project_id == project_id)
        .order_by(Message.timestamp.desc())
        .limit(limit)
        .all()
    )
    messages = list(reversed(messages))

    latest_status = (
        db.query(ProjectStatus)
        .filter(ProjectStatus.project_id == project_id)
        .order_by(ProjectStatus.created_at.desc())
        .first()
    )

    return {
        "recent_messages": [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat() if m.timestamp else "",
            }
            for m in messages
        ],
        "latest_status": {
            "health_score": latest_status.health_score if latest_status else None,
            "progress": latest_status.progress if latest_status else None,
            "problems": latest_status.problems if latest_status else [],
            "next_steps": latest_status.next_steps if latest_status else [],
        } if latest_status else None,
        "message_count": len(messages),
    }


def build_chat_context(messages: List[Dict], max_tokens: int = 4000) -> str:
    lines = []
    char_budget = max_tokens * 4
    for msg in messages[-15:]:
        role = msg.get("role", "user").upper()
        content = msg.get("content", "")[:500]
        line = f"[{role}]: {content}"
        char_budget -= len(line)
        if char_budget < 0:
            break
        lines.append(line)
    return "\n".join(lines)
