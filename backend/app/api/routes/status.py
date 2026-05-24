from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.db.schemas.status import ProjectStatusResponse, NextStepsResponse
from app.api.deps import get_current_user
from app.services.project_service import get_project
from app.services.status_service import compute_and_save_status, compute_next_steps

router = APIRouter(prefix="/projects", tags=["status"])


@router.post("/{project_id}/status", response_model=ProjectStatusResponse)
def project_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project(db, project_id=project_id, owner_id=current_user.id)
    return compute_and_save_status(db, project)


@router.post("/{project_id}/next-steps", response_model=NextStepsResponse)
def next_steps(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project(db, project_id=project_id, owner_id=current_user.id)
    return compute_next_steps(db, project)
