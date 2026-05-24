import os
import tempfile
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.db.models.upload import UploadAnalysis
from app.scanners.zip_scanner import safe_extract_zip, cleanup_extract, get_project_root
from app.scanners.structure_scanner import scan_structure
from app.scanners.dependency_scanner import scan_dependencies
from app.scanners.code_scanner import scan_code
from app.analyzers.architecture_analyzer import analyze_architecture
from app.analyzers.health_analyzer import compute_health
from app.analyzers.issue_analyzer import analyze_issues
from app.analyzers.risk_analyzer import predict_failures


def create_upload_record(
    db: Session,
    user_id: int,
    project_id: int,
    filename: str,
    file_size: int,
) -> UploadAnalysis:
    record = UploadAnalysis(
        user_id=user_id,
        project_id=project_id,
        filename=filename,
        file_size=file_size,
        status="processing",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def process_zip_upload(
    db: Session,
    record: UploadAnalysis,
    zip_path: str,
) -> UploadAnalysis:
    extract_path: Optional[str] = None
    try:
        extract_result = safe_extract_zip(zip_path)
        if not extract_result["success"]:
            return _fail(db, record, extract_result["error"])

        extract_path = extract_result["extract_path"]
        project_root = get_project_root(extract_path)

        # Layer 1: Structure
        structure = scan_structure(project_root)
        # Layer 1: Dependencies
        deps = scan_dependencies(project_root)
        # Layer 2: Code Intelligence
        code_scan = scan_code(project_root)
        # Architecture analysis
        arch = analyze_architecture(structure, deps)
        # Health scoring
        health = compute_health(code_scan, arch, structure, deps)
        # Issue analysis
        issues = analyze_issues(code_scan, arch, deps)
        # Risk prediction
        risk = predict_failures(code_scan, arch, deps)

        record.status = "complete"
        record.file_count = structure.get("file_count", 0)
        record.languages = structure.get("languages", [])
        record.frameworks = deps.get("frameworks", [])
        record.architecture_type = arch.get("type", "unknown")
        record.architecture_summary = arch.get("summary", "")
        record.folder_tree = structure.get("folder_tree", [])[:100]
        record.dependencies = {
            "python": list(deps.get("python", {}).keys())[:30],
            "node": list(deps.get("node", {}).keys())[:30],
            "databases": deps.get("databases", []),
            "cloud": deps.get("cloud", []),
        }
        record.issues = issues.get("problems", [])
        record.security_issues = code_scan.get("security_issues", [])
        record.performance_issues = code_scan.get("performance_issues", [])
        record.health_score = health.get("health_score", 0)
        record.architecture_score = health.get("architecture_score", 0)
        record.debt_score = health.get("debt_score", 0)
        record.stability_score = health.get("stability_score", 0)
        record.recommendations = arch.get("recommendations", []) + risk.get("mitigation_strategies", [])
        record.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(record)
        return record

    except Exception as e:
        return _fail(db, record, str(e))
    finally:
        if extract_path:
            cleanup_extract(extract_path)
        try:
            os.remove(zip_path)
        except Exception:
            pass


def _fail(db: Session, record: UploadAnalysis, error: str) -> UploadAnalysis:
    record.status = "failed"
    record.error_message = error[:1000]
    record.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return record


def get_upload_analyses(db: Session, project_id: int) -> list:
    return (
        db.query(UploadAnalysis)
        .filter(UploadAnalysis.project_id == project_id)
        .order_by(UploadAnalysis.created_at.desc())
        .limit(10)
        .all()
    )


def get_latest_analysis(db: Session, project_id: int) -> Optional[UploadAnalysis]:
    return (
        db.query(UploadAnalysis)
        .filter(UploadAnalysis.project_id == project_id, UploadAnalysis.status == "complete")
        .order_by(UploadAnalysis.created_at.desc())
        .first()
    )
