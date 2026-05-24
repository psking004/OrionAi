from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class GitHubConnectRequest(BaseModel):
    github_token: str
    repo_owner: str
    repo_name: str


class GitHubConnectionResponse(BaseModel):
    id: int
    project_id: int
    repo_owner: str
    repo_name: str
    repo_url: Optional[str] = None
    default_branch: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int
    forks: int
    open_issues: int
    commit_count: int
    contributor_count: int
    last_synced: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class GitHubSyncResponse(BaseModel):
    connection: GitHubConnectionResponse
    commit_analysis: dict
    contributor_analysis: dict
    branch_analysis: dict
    velocity_score: float
    risk_score: float
    momentum_score: float
    recent_activity: list
    stalled_modules: list
    risky_commits: list
    recommendations: list


class GitHubRepoTree(BaseModel):
    path: str
    type: str
    size: Optional[int] = None
