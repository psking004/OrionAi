from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.status import ProjectStatus
from app.db.models.message import Message


def get_recurring_issues(db: Session, project_id: int) -> List[str]:
    statuses = (
        db.query(ProjectStatus)
        .filter(ProjectStatus.project_id == project_id)
        .order_by(ProjectStatus.created_at.desc())
        .limit(10)
        .all()
    )

    issue_counts: Dict[str, int] = {}
    for s in statuses:
        for p in (s.problems or []):
            key = p[:80]
            issue_counts[key] = issue_counts.get(key, 0) + 1

    return [
        issue for issue, count in
        sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        if count >= 2
    ][:5]


def get_project_evolution(db: Session, project_id: int) -> List[Dict[str, Any]]:
    statuses = (
        db.query(ProjectStatus)
        .filter(ProjectStatus.project_id == project_id)
        .order_by(ProjectStatus.created_at.asc())
        .limit(20)
        .all()
    )

    return [
        {
            "date": s.created_at.isoformat() if s.created_at else "",
            "health_score": s.health_score,
            "progress": s.progress,
            "problem_count": len(s.problems or []),
        }
        for s in statuses
    ]


def get_unresolved_problems(db: Session, project_id: int) -> List[str]:
    recent = (
        db.query(ProjectStatus)
        .filter(ProjectStatus.project_id == project_id)
        .order_by(ProjectStatus.created_at.desc())
        .first()
    )
    if not recent:
        return []

    older = (
        db.query(ProjectStatus)
        .filter(ProjectStatus.project_id == project_id)
        .order_by(ProjectStatus.created_at.desc())
        .offset(1)
        .limit(5)
        .all()
    )
    if not older:
        return recent.problems or []

    older_problems = set()
    for s in older:
        for p in (s.problems or []):
            older_problems.add(p[:80])

    return [
        p for p in (recent.problems or [])
        if p[:80] in older_problems
    ][:5]
