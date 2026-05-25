"""
Dashboard overview route — aggregates cross-project intelligence.

GET /dashboard/overview     Project summary + health + alerts + velocity
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.db.models.status import ProjectStatus
from app.db.models.upload import UploadAnalysis
from app.db.models.github import GitHubConnection
from app.db.models.billing import CreditUsageEvent, CreditLedger
from app.services.credit_service import get_credit_status, get_plan

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = current_user.id
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # ── Projects ─────────────────────────────────────────────────────────────
    projects = (
        db.query(Project)
        .filter(Project.owner_id == uid)
        .order_by(desc(Project.updated_at))
        .all()
    )
    total_projects = len(projects)
    active_projects = sum(1 for p in projects if p.status == "active")

    # ── Health Scores ─────────────────────────────────────────────────────────
    # Latest status per project
    health_scores = []
    ai_alerts = []
    risk_projects = []

    for p in projects:
        latest_status = (
            db.query(ProjectStatus)
            .filter(ProjectStatus.project_id == p.id)
            .order_by(desc(ProjectStatus.created_at))
            .first()
        )
        if latest_status:
            score = latest_status.health_score or 0
            health_scores.append(score)
            if score < 40:
                risk_projects.append({
                    "project_id": p.id,
                    "name": p.name,
                    "health_score": score,
                    "progress": latest_status.progress,
                })
            # Collect alerts from problems/stuck points
            problems = latest_status.problems or []
            stuck = latest_status.stuck_points or []
            if problems:
                ai_alerts.append({
                    "project_id": p.id,
                    "project_name": p.name,
                    "type": "problem",
                    "message": problems[0] if isinstance(problems, list) else str(problems),
                    "severity": "high" if score < 40 else "medium",
                })
            if stuck:
                ai_alerts.append({
                    "project_id": p.id,
                    "project_name": p.name,
                    "type": "blocker",
                    "message": stuck[0] if isinstance(stuck, list) else str(stuck),
                    "severity": "medium",
                })

    avg_health = round(sum(health_scores) / len(health_scores), 1) if health_scores else 0.0
    health_distribution = {
        "healthy": sum(1 for s in health_scores if s >= 70),
        "needs_attention": sum(1 for s in health_scores if 40 <= s < 70),
        "critical": sum(1 for s in health_scores if s < 40),
    }

    # ── Recent Scans ─────────────────────────────────────────────────────────
    recent_uploads = (
        db.query(UploadAnalysis)
        .filter(UploadAnalysis.user_id == uid, UploadAnalysis.created_at >= week_ago)
        .order_by(desc(UploadAnalysis.created_at))
        .limit(5)
        .all()
    )
    recent_scans = [
        {
            "id": u.id,
            "project_id": u.project_id,
            "filename": u.filename,
            "health_score": u.health_score,
            "status": u.status,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in recent_uploads
    ]

    # ── GitHub Velocity ───────────────────────────────────────────────────────
    github_connections = (
        db.query(GitHubConnection)
        .filter(GitHubConnection.user_id == uid)
        .all()
    )
    total_commits = sum(c.commit_count or 0 for c in github_connections)
    connected_repos = len(github_connections)

    velocity_data = []
    for conn in github_connections[:3]:
        proj = db.query(Project).filter(Project.id == conn.project_id).first()
        velocity_data.append({
            "project_id": conn.project_id,
            "project_name": proj.name if proj else "Unknown",
            "repo": f"{conn.repo_owner}/{conn.repo_name}",
            "commits": conn.commit_count or 0,
            "contributors": conn.contributor_count or 0,
            "last_synced": conn.last_synced.isoformat() if conn.last_synced else None,
        })

    # ── Credit Usage ─────────────────────────────────────────────────────────
    credit_info = get_credit_status(db, uid)

    # Usage by feature this month
    feature_usage = (
        db.query(CreditUsageEvent.feature, func.sum(CreditUsageEvent.credits_used).label("total"))
        .filter(CreditUsageEvent.user_id == uid, CreditUsageEvent.created_at >= month_ago)
        .group_by(CreditUsageEvent.feature)
        .all()
    )
    usage_breakdown = {row.feature: row.total for row in feature_usage}

    # ── Top AI Recommendations ────────────────────────────────────────────────
    # Pull from latest upload analyses
    top_recommendations = []
    top_risks = []

    latest_upload = (
        db.query(UploadAnalysis)
        .filter(UploadAnalysis.user_id == uid, UploadAnalysis.status == "complete")
        .order_by(desc(UploadAnalysis.created_at))
        .first()
    )
    if latest_upload:
        recs = latest_upload.recommendations or []
        issues = latest_upload.issues or []
        security = latest_upload.security_issues or []
        top_recommendations = recs[:5] if isinstance(recs, list) else []
        top_risks = (security[:3] + issues[:2]) if isinstance(issues, list) else []

    # ── Assemble Response ─────────────────────────────────────────────────────
    return {
        "user": {
            "id": uid,
            "username": current_user.username,
            "plan": credit_info["plan"],
        },
        "projects": {
            "total": total_projects,
            "active": active_projects,
            "health_distribution": health_distribution,
            "avg_health_score": avg_health,
            "at_risk": risk_projects[:5],
        },
        "ai_alerts": ai_alerts[:8],
        "top_recommendations": top_recommendations,
        "top_risks": top_risks,
        "recent_scans": recent_scans,
        "github_velocity": {
            "connected_repos": connected_repos,
            "total_commits": total_commits,
            "repos": velocity_data,
        },
        "credits": {
            "plan": credit_info["plan"],
            "daily_remaining": credit_info["daily_remaining"],
            "daily_limit": credit_info["daily_limit"],
            "monthly_remaining": credit_info["monthly_remaining"],
            "monthly_limit": credit_info["monthly_limit"],
            "usage_breakdown": usage_breakdown,
        },
        "generated_at": now.isoformat(),
    }
