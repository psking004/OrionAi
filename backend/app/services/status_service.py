from sqlalchemy.orm import Session
from app.db.models.message import Message
from app.db.models.project import Project
from app.db.models.status import ProjectStatus
from app.db.schemas.status import ProjectStatusResponse, NextStepsResponse
from app.services.ai_service import (
    analyze_messages,
    generate_prioritized_roadmap,
    serialize_list,
    deserialize_list,
)


def _messages_to_dicts(messages: list[Message]) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in messages]


def compute_and_save_status(
    db: Session, project: Project
) -> ProjectStatusResponse:
    messages = (
        db.query(Message)
        .filter(Message.project_id == project.id)
        .order_by(Message.timestamp.asc())
        .all()
    )

    msg_dicts = _messages_to_dicts(messages)

    progress, problems, stuck_points, next_steps, missing_features, health_score = analyze_messages(
        msg_dicts
    )

    db_status = ProjectStatus(
        project_id=project.id,
        progress=progress,
        problems=serialize_list(problems),
        stuck_points=serialize_list(stuck_points),
        next_steps=serialize_list(next_steps),
        missing_features=serialize_list(missing_features),
        health_score=health_score,
    )
    db.add(db_status)
    db.commit()
    db.refresh(db_status)

    return ProjectStatusResponse(
        id=db_status.id,
        project_id=db_status.project_id,
        progress=db_status.progress,
        problems=problems,
        stuck_points=stuck_points,
        next_steps=next_steps,
        missing_features=missing_features,
        health_score=health_score,
        created_at=db_status.created_at,
    )


def compute_next_steps(db: Session, project: Project) -> NextStepsResponse:
    messages = (
        db.query(Message)
        .filter(Message.project_id == project.id)
        .order_by(Message.timestamp.asc())
        .all()
    )

    msg_dicts = _messages_to_dicts(messages)

    roadmap, steps = generate_prioritized_roadmap(
        project_name=project.name,
        tech_stack=project.tech_stack or "",
        messages=msg_dicts,
    )

    return NextStepsResponse(
        project_id=project.id,
        roadmap=roadmap,
        steps=steps,
    )
