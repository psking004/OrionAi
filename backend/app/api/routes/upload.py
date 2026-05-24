import os
import tempfile
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.db.schemas.upload import (
    UploadAnalysisResponse, AgentTeamResponse, AgentReport,
    DebugRequest, DebugResponse, TaskInput, TaskBreakdownResponse,
    FailurePrediction,
)
from app.services import upload_service, debug_service as debug_svc, roadmap_service
from app.scanners.structure_scanner import scan_structure
from app.scanners.dependency_scanner import scan_dependencies
from app.scanners.code_scanner import scan_code
from app.analyzers.architecture_analyzer import analyze_architecture
from app.analyzers.health_analyzer import compute_health
from app.analyzers.issue_analyzer import analyze_issues
from app.analyzers.risk_analyzer import predict_failures
from app.agents import cto_agent, pm_agent, qa_agent, devops_agent, security_agent

router = APIRouter()

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB


def _get_project(db: Session, project_id: int, user: User) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == user.id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/projects/{project_id}/upload", response_model=UploadAnalysisResponse)
async def upload_project_zip(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(db, project_id, current_user)

    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")

    content = await file.read()
    file_size = len(content)

    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Max size: 100MB")
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Write to temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp.write(content)
    tmp.close()

    record = upload_service.create_upload_record(
        db, current_user.id, project_id, file.filename, file_size
    )

    background_tasks.add_task(upload_service.process_zip_upload, db, record, tmp.name)

    return record


@router.get("/projects/{project_id}/uploads", response_model=List[UploadAnalysisResponse])
def list_uploads(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(db, project_id, current_user)
    return upload_service.get_upload_analyses(db, project_id)


@router.get("/projects/{project_id}/uploads/latest", response_model=UploadAnalysisResponse)
def get_latest_upload(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(db, project_id, current_user)
    analysis = upload_service.get_latest_analysis(db, project_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No completed analysis found")
    return analysis


@router.get("/projects/{project_id}/agents", response_model=AgentTeamResponse)
def get_agent_team(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project(db, project_id, current_user)
    analysis = upload_service.get_latest_analysis(db, project_id)

    # Build context from whatever we have
    if analysis:
        structure = {"file_count": analysis.file_count, "languages": analysis.languages, "folder_tree": analysis.folder_tree}
        deps = {"frameworks": analysis.frameworks, "databases": analysis.dependencies.get("databases", []), "cloud": analysis.dependencies.get("cloud", []), "has_docker": False, "has_ci": False, "has_tests": False, "python": {}, "node": {}}
        code_scan = {"issues": analysis.issues, "security_issues": analysis.security_issues, "performance_issues": analysis.performance_issues, "has_auth": True, "has_tests": False, "has_logging": True, "large_files": []}
        arch = {"type": analysis.architecture_type or "unknown", "quality_score": analysis.architecture_score, "summary": analysis.architecture_summary or "", "recommendations": analysis.recommendations, "deployment_readiness": {"ready": False}, "separation_of_concerns": {}}
        health = {"health_score": analysis.health_score, "architecture_score": analysis.architecture_score, "debt_score": analysis.debt_score, "stability_score": analysis.stability_score}
        issues = {"problems": analysis.issues, "stuck_points": [], "missing_features": []}
        risk = predict_failures(code_scan, arch, deps)
        commit_data = None
    else:
        # Synthesize from project info
        tech = project.tech_stack or ""
        deps = _tech_to_deps(tech)
        code_scan = {"issues": [], "security_issues": [], "performance_issues": [], "has_auth": False, "has_tests": False, "has_logging": False, "large_files": []}
        arch = {"type": "unknown", "quality_score": 50, "summary": "Connect GitHub or upload ZIP for detailed analysis", "recommendations": [], "deployment_readiness": {"ready": False}, "separation_of_concerns": {}}
        health = {"health_score": 50, "architecture_score": 50, "debt_score": 50, "stability_score": 50}
        issues = {"problems": [], "stuck_points": [], "missing_features": []}
        risk = {"deployment_risks": [], "scalability_issues": [], "unstable_modules": [], "security_vulnerabilities": [], "future_bottlenecks": [], "overall_risk_score": 30, "risk_level": "medium", "mitigation_strategies": []}
        commit_data = None
        structure = {"file_count": 0, "languages": [], "folder_tree": []}

    cto = cto_agent.run(arch, health, risk, deps, structure)
    pm = pm_agent.run(issues, health, structure, commit_data)
    qa = qa_agent.run(code_scan, arch, health)
    devops = devops_agent.run(deps, arch, health, risk)
    security = security_agent.run(code_scan, deps, arch, risk)

    consensus = _consensus_priorities([cto, pm, qa, devops, security])
    overall_risk = risk.get("risk_level", "medium")

    return {
        "project_id": project_id,
        "cto": cto,
        "pm": pm,
        "qa": qa,
        "devops": devops,
        "security": security,
        "consensus_priorities": consensus,
        "overall_risk_level": overall_risk,
    }


@router.post("/projects/{project_id}/debug", response_model=DebugResponse)
def debug_project(
    project_id: int,
    payload: DebugRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(db, project_id, current_user)
    result = debug_svc.analyze_debug(payload.logs, payload.error_trace, payload.context, project_id)
    return result


@router.post("/projects/{project_id}/tasks", response_model=TaskBreakdownResponse)
def generate_tasks(
    project_id: int,
    payload: TaskInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project(db, project_id, current_user)
    result = roadmap_service.generate_task_breakdown(payload.prompt, project, payload.context)
    result["project_id"] = project_id
    return result


@router.get("/projects/{project_id}/predict", response_model=FailurePrediction)
def predict_project_failures(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(db, project_id, current_user)
    analysis = upload_service.get_latest_analysis(db, project_id)

    if analysis:
        code_scan = {"issues": analysis.issues, "security_issues": analysis.security_issues, "performance_issues": analysis.performance_issues, "has_auth": True, "has_tests": False, "has_logging": True, "large_files": []}
        deps = {"frameworks": analysis.frameworks, "databases": analysis.dependencies.get("databases", []), "cloud": [], "has_docker": False, "has_ci": False, "python": {}, "node": {}}
        arch = {"type": analysis.architecture_type or "unknown", "quality_score": analysis.architecture_score, "deployment_readiness": {"ready": False}, "separation_of_concerns": {}}
    else:
        code_scan = {"issues": [], "security_issues": [], "performance_issues": [], "has_auth": False, "has_tests": False, "has_logging": False, "large_files": []}
        deps = {"frameworks": [], "databases": [], "cloud": [], "has_docker": False, "has_ci": False, "python": {}, "node": {}}
        arch = {"type": "unknown", "quality_score": 50, "deployment_readiness": {"ready": False}, "separation_of_concerns": {}}

    result = predict_failures(code_scan, arch, deps)
    result["project_id"] = project_id
    return result


def _tech_to_deps(tech_stack: str) -> dict:
    tech = tech_stack.lower()
    return {
        "frameworks": [t.strip() for t in tech_stack.split(",") if t.strip()][:5],
        "databases": ["PostgreSQL"] if "postgres" in tech or "pg" in tech else [],
        "cloud": [],
        "has_docker": "docker" in tech,
        "has_ci": False,
        "has_tests": False,
        "python": {"fastapi": ""} if "fastapi" in tech else {},
        "node": {"react": ""} if "react" in tech else {},
        "devops": [],
    }


def _consensus_priorities(agents: list) -> list:
    all_priorities = []
    for agent in agents:
        all_priorities.extend(agent.get("priorities", [])[:2])
    seen = []
    for p in all_priorities:
        if p not in seen:
            seen.append(p)
    return seen[:6]
