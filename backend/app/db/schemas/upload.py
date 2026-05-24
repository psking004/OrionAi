from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class UploadAnalysisResponse(BaseModel):
    id: int
    project_id: int
    filename: str
    file_size: int
    status: str
    file_count: int
    languages: List[str]
    frameworks: List[str]
    architecture_type: Optional[str] = None
    architecture_summary: Optional[str] = None
    folder_tree: List[Any]
    dependencies: Dict[str, Any]
    issues: List[str]
    security_issues: List[str]
    performance_issues: List[str]
    health_score: float
    architecture_score: float
    debt_score: float
    stability_score: float
    recommendations: List[str]
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentReport(BaseModel):
    agent: str
    role: str
    recommendations: List[str]
    risks: List[str]
    priorities: List[str]
    actions: List[str]
    score: float


class AgentTeamResponse(BaseModel):
    project_id: int
    cto: AgentReport
    pm: AgentReport
    qa: AgentReport
    devops: AgentReport
    security: AgentReport
    consensus_priorities: List[str]
    overall_risk_level: str


class DebugRequest(BaseModel):
    logs: str
    error_trace: Optional[str] = None
    context: Optional[str] = None


class DebugResponse(BaseModel):
    project_id: int
    error_type: Optional[str] = None
    root_cause: str
    affected_modules: List[str]
    severity: str
    suggested_fixes: List[str]
    prevention_strategies: List[str]
    similar_patterns: List[str]


class TaskInput(BaseModel):
    prompt: str
    context: Optional[str] = None


class TaskItem(BaseModel):
    id: str
    title: str
    description: str
    type: str
    priority: str
    estimated_hours: float
    dependencies: List[str]
    milestone: str


class TaskBreakdownResponse(BaseModel):
    project_id: int
    prompt: str
    backend_tasks: List[TaskItem]
    frontend_tasks: List[TaskItem]
    testing_tasks: List[TaskItem]
    deployment_tasks: List[TaskItem]
    milestones: List[str]
    total_estimated_hours: float
    recommended_sprint_weeks: int


class FailurePrediction(BaseModel):
    project_id: int
    deployment_risks: List[str]
    scalability_issues: List[str]
    unstable_modules: List[str]
    security_vulnerabilities: List[str]
    future_bottlenecks: List[str]
    overall_risk_score: float
    risk_level: str
    mitigation_strategies: List[str]
