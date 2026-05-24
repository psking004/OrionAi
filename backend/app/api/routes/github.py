from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.db.schemas.github import (
    GitHubConnectRequest, GitHubConnectionResponse, GitHubSyncResponse,
)
from app.services import github_service

router = APIRouter()


def _get_project(db: Session, project_id: int, user: User) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == user.id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _get_connection(db, project_id):
    conn = github_service.get_connection(db, project_id)
    if not conn:
        raise HTTPException(status_code=404, detail="No GitHub connection for this project")
    return conn


@router.post("/projects/{project_id}/github/connect", response_model=GitHubConnectionResponse)
def connect_github(
    project_id: int,
    payload: GitHubConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(db, project_id, current_user)

    result = github_service.connect_github(
        db,
        user_id=current_user.id,
        project_id=project_id,
        token=payload.github_token,
        owner=payload.repo_owner,
        repo=payload.repo_name,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result["connection"]


@router.get("/projects/{project_id}/github", response_model=GitHubConnectionResponse)
def get_github_connection(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(db, project_id, current_user)
    return _get_connection(db, project_id)


@router.post("/projects/{project_id}/github/sync", response_model=GitHubSyncResponse)
def sync_github(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(db, project_id, current_user)
    conn = _get_connection(db, project_id)

    try:
        result = github_service.sync_github(db, conn)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GitHub sync failed: {str(e)}")

    return result


@router.delete("/projects/{project_id}/github", status_code=204)
def disconnect_github(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(db, project_id, current_user)
    removed = github_service.disconnect_github(db, project_id)
    if not removed:
        raise HTTPException(status_code=404, detail="No GitHub connection found")
