from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.db.models.project import Project
from app.db.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, owner_id: int, data: ProjectCreate) -> Project:
    project = Project(
        owner_id=owner_id,
        name=data.name,
        description=data.description,
        tech_stack=data.tech_stack,
        status=data.status,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: int, owner_id: int) -> Project:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == owner_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def list_projects(db: Session, owner_id: int) -> List[Project]:
    return (
        db.query(Project)
        .filter(Project.owner_id == owner_id)
        .order_by(Project.updated_at.desc())
        .all()
    )


def update_project(db: Session, project_id: int, owner_id: int, data: ProjectUpdate) -> Project:
    project = get_project(db, project_id, owner_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int, owner_id: int) -> None:
    project = get_project(db, project_id, owner_id)
    db.delete(project)
    db.commit()
