from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.models.github import GitHubConnection
from app.scanners.github_scanner import (
    validate_token, fetch_repo_info, fetch_commits, fetch_contributors,
    fetch_branches, fetch_repo_tree, fetch_languages, fetch_pull_requests,
)
from app.analyzers.progress_analyzer import analyze_commit_velocity
from app.analyzers.risk_analyzer import predict_failures
from app.scanners.structure_scanner import scan_structure


def connect_github(
    db: Session,
    user_id: int,
    project_id: int,
    token: str,
    owner: str,
    repo: str,
) -> Dict[str, Any]:
    token_check = validate_token(token)
    if not token_check["valid"]:
        return {"success": False, "error": "Invalid GitHub token"}

    repo_info = fetch_repo_info(token, owner, repo)
    if not repo_info:
        return {"success": False, "error": f"Repository {owner}/{repo} not found or not accessible"}

    existing = db.query(GitHubConnection).filter(
        GitHubConnection.project_id == project_id
    ).first()

    if existing:
        existing.github_token = token
        existing.repo_owner = owner
        existing.repo_name = repo
        existing.repo_url = repo_info.get("html_url", "")
        existing.default_branch = repo_info.get("default_branch", "main")
        existing.description = repo_info.get("description", "")
        existing.language = repo_info.get("language", "")
        existing.stars = repo_info.get("stars", 0)
        existing.forks = repo_info.get("forks", 0)
        existing.open_issues = repo_info.get("open_issues", 0)
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        conn = existing
    else:
        conn = GitHubConnection(
            user_id=user_id,
            project_id=project_id,
            github_token=token,
            repo_owner=owner,
            repo_name=repo,
            repo_url=repo_info.get("html_url", ""),
            default_branch=repo_info.get("default_branch", "main"),
            description=repo_info.get("description", ""),
            language=repo_info.get("language", ""),
            stars=repo_info.get("stars", 0),
            forks=repo_info.get("forks", 0),
            open_issues=repo_info.get("open_issues", 0),
        )
        db.add(conn)
        db.commit()
        db.refresh(conn)

    return {"success": True, "connection": conn}


def sync_github(db: Session, connection: GitHubConnection) -> Dict[str, Any]:
    token = connection.github_token
    owner = connection.repo_owner
    repo = connection.repo_name
    branch = connection.default_branch

    commits = fetch_commits(token, owner, repo, branch)
    contributors = fetch_contributors(token, owner, repo)
    branches = fetch_branches(token, owner, repo)
    languages = fetch_languages(token, owner, repo)
    prs = fetch_pull_requests(token, owner, repo)
    tree = fetch_repo_tree(token, owner, repo, branch)

    commit_analysis = analyze_commit_velocity(commits)

    # Update connection stats
    connection.commit_count = len(commits)
    connection.contributor_count = len(contributors)
    connection.last_synced = datetime.now(timezone.utc)
    db.commit()
    db.refresh(connection)

    velocity_score = commit_analysis.get("velocity_score", 0)
    risk_score = _compute_repo_risk(commit_analysis, prs)
    momentum_score = _momentum_to_score(commit_analysis.get("momentum", "unknown"))

    return {
        "connection": connection,
        "commit_analysis": {
            "total": len(commits),
            "frequency": commit_analysis.get("commit_frequency", "unknown"),
            "avg_per_week": commit_analysis.get("avg_commits_per_week", 0),
            "momentum": commit_analysis.get("momentum", "unknown"),
        },
        "contributor_analysis": {
            "total": len(contributors),
            "top": contributors[:5],
        },
        "branch_analysis": {
            "total": len(branches),
            "branches": branches[:10],
        },
        "language_breakdown": languages,
        "open_prs": len(prs),
        "velocity_score": velocity_score,
        "risk_score": risk_score,
        "momentum_score": momentum_score,
        "recent_activity": commits[:5],
        "stalled_modules": commit_analysis.get("stalled_modules", []),
        "risky_commits": commit_analysis.get("risky_commits", [])[:5],
        "recommendations": _generate_github_recommendations(commit_analysis, prs, contributors),
    }


def get_connection(db: Session, project_id: int) -> Optional[GitHubConnection]:
    return db.query(GitHubConnection).filter(
        GitHubConnection.project_id == project_id
    ).first()


def disconnect_github(db: Session, project_id: int) -> bool:
    conn = get_connection(db, project_id)
    if not conn:
        return False
    db.delete(conn)
    db.commit()
    return True


def _compute_repo_risk(commit_analysis: Dict, prs: list) -> float:
    risky = len(commit_analysis.get("risky_commits", []))
    stalled = len(commit_analysis.get("stalled_modules", []))
    open_prs = len(prs)
    score = (risky * 10) + (stalled * 8) + min(open_prs * 2, 20)
    return round(min(score, 100), 1)


def _momentum_to_score(momentum: str) -> float:
    return {"strong": 90, "steady": 70, "slow": 40, "stalled": 10, "unknown": 50}.get(momentum, 50)


def _generate_github_recommendations(commit_analysis: Dict, prs: list, contributors: list) -> list:
    recs = []
    if commit_analysis.get("momentum") == "stalled":
        recs.append("Commit activity is stalled — unblock the team or re-evaluate scope")
    if len(prs) > 10:
        recs.append(f"{len(prs)} open PRs — review and merge or close stale PRs")
    if commit_analysis.get("risky_commits"):
        recs.append("Risky commits detected — add mandatory code review before merge")
    if len(contributors) == 1:
        recs.append("Single contributor — consider bus factor risk and documentation")
    recs.append("Enable branch protection rules on main/master branch")
    recs.append("Set up CODEOWNERS file for automatic review assignments")
    return recs[:6]
