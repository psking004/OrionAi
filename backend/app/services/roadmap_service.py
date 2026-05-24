from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.db.models.project import Project
from app.db.models.status import ProjectStatus


def generate_roadmap(
    db: Session,
    project: Project,
    issues: Dict[str, Any],
    health: Dict[str, Any],
    arch: Dict[str, Any],
    deps: Dict[str, Any],
) -> Dict[str, Any]:
    problems = issues.get("problems", [])
    missing = issues.get("missing_features", [])
    stuck = issues.get("stuck_points", [])
    health_score = health.get("health_score", 50)
    arch_recs = arch.get("recommendations", [])

    roadmap = _build_roadmap(health_score, problems, missing, arch_recs, deps)
    steps = _build_action_steps(problems, missing, stuck, deps)
    phase_plan = _build_phase_plan(health_score, missing, deps)

    return {
        "roadmap": roadmap,
        "steps": steps,
        "phase_plan": phase_plan,
        "estimated_weeks": _estimate_weeks(health_score, len(missing), len(problems)),
    }


def generate_task_breakdown(
    prompt: str,
    project: Project,
    context: str | None = None,
) -> Dict[str, Any]:
    prompt_lower = prompt.lower()
    category = _classify_prompt(prompt_lower)

    backend_tasks = _generate_backend_tasks(prompt, category)
    frontend_tasks = _generate_frontend_tasks(prompt, category)
    testing_tasks = _generate_testing_tasks(prompt, category)
    deployment_tasks = _generate_deployment_tasks(prompt, category)
    milestones = _generate_milestones(category)

    total_hours = (
        sum(t["estimated_hours"] for t in backend_tasks) +
        sum(t["estimated_hours"] for t in frontend_tasks) +
        sum(t["estimated_hours"] for t in testing_tasks) +
        sum(t["estimated_hours"] for t in deployment_tasks)
    )
    sprint_weeks = max(1, round(total_hours / 40))

    return {
        "prompt": prompt,
        "backend_tasks": backend_tasks,
        "frontend_tasks": frontend_tasks,
        "testing_tasks": testing_tasks,
        "deployment_tasks": deployment_tasks,
        "milestones": milestones,
        "total_estimated_hours": total_hours,
        "recommended_sprint_weeks": sprint_weeks,
    }


def _classify_prompt(prompt: str) -> str:
    if any(w in prompt for w in ["dashboard", "ui", "interface", "page", "screen"]):
        return "ui_feature"
    if any(w in prompt for w in ["api", "endpoint", "backend", "service", "crud"]):
        return "api_feature"
    if any(w in prompt for w in ["auth", "login", "user", "account", "permission"]):
        return "auth_feature"
    if any(w in prompt for w in ["database", "db", "schema", "migration", "model"]):
        return "data_feature"
    if any(w in prompt for w in ["deploy", "docker", "ci", "pipeline", "infra"]):
        return "devops_feature"
    if any(w in prompt for w in ["notification", "email", "sms", "webhook", "alert"]):
        return "notification_feature"
    return "general_feature"


def _generate_backend_tasks(prompt: str, category: str) -> List[Dict]:
    base = [
        {"id": "BE-001", "title": f"Design data model for: {prompt[:40]}", "description": "Define schema, relationships, constraints", "type": "backend", "priority": "high", "estimated_hours": 2.0, "dependencies": [], "milestone": "M1"},
        {"id": "BE-002", "title": "Create database migration", "description": "Write and test schema migration scripts", "type": "backend", "priority": "high", "estimated_hours": 1.5, "dependencies": ["BE-001"], "milestone": "M1"},
        {"id": "BE-003", "title": "Implement service layer", "description": "Business logic, validation, error handling", "type": "backend", "priority": "high", "estimated_hours": 4.0, "dependencies": ["BE-002"], "milestone": "M2"},
        {"id": "BE-004", "title": "Create API endpoints", "description": "REST endpoints with request/response schemas", "type": "backend", "priority": "high", "estimated_hours": 3.0, "dependencies": ["BE-003"], "milestone": "M2"},
        {"id": "BE-005", "title": "Add input validation", "description": "Schema validation, sanitization, error responses", "type": "backend", "priority": "medium", "estimated_hours": 1.5, "dependencies": ["BE-004"], "milestone": "M2"},
    ]
    if category == "auth_feature":
        base.append({"id": "BE-006", "title": "Implement JWT auth middleware", "description": "Token generation, validation, refresh", "type": "backend", "priority": "critical", "estimated_hours": 3.0, "dependencies": ["BE-001"], "milestone": "M1"})
    return base


def _generate_frontend_tasks(prompt: str, category: str) -> List[Dict]:
    return [
        {"id": "FE-001", "title": f"Design UI wireframes for: {prompt[:40]}", "description": "Low-fidelity layout and user flow", "type": "frontend", "priority": "high", "estimated_hours": 2.0, "dependencies": [], "milestone": "M1"},
        {"id": "FE-002", "title": "Create page/component structure", "description": "Component hierarchy, state management plan", "type": "frontend", "priority": "high", "estimated_hours": 2.0, "dependencies": ["FE-001"], "milestone": "M2"},
        {"id": "FE-003", "title": "Implement UI components", "description": "Build all required UI components with Tailwind", "type": "frontend", "priority": "high", "estimated_hours": 5.0, "dependencies": ["FE-002", "BE-004"], "milestone": "M2"},
        {"id": "FE-004", "title": "Wire API integration", "description": "Connect components to API, handle loading/error states", "type": "frontend", "priority": "high", "estimated_hours": 3.0, "dependencies": ["FE-003"], "milestone": "M3"},
        {"id": "FE-005", "title": "Responsive design + accessibility", "description": "Mobile-first responsive layout, a11y audit", "type": "frontend", "priority": "medium", "estimated_hours": 2.0, "dependencies": ["FE-004"], "milestone": "M3"},
    ]


def _generate_testing_tasks(prompt: str, category: str) -> List[Dict]:
    return [
        {"id": "TEST-001", "title": "Unit tests — service layer", "description": "Test all business logic functions", "type": "testing", "priority": "high", "estimated_hours": 3.0, "dependencies": ["BE-003"], "milestone": "M2"},
        {"id": "TEST-002", "title": "Integration tests — API endpoints", "description": "Test all endpoints with real database", "type": "testing", "priority": "high", "estimated_hours": 2.5, "dependencies": ["BE-004"], "milestone": "M3"},
        {"id": "TEST-003", "title": "E2E test — critical user journey", "description": "Playwright test for happy path", "type": "testing", "priority": "medium", "estimated_hours": 2.0, "dependencies": ["FE-004"], "milestone": "M3"},
        {"id": "TEST-004", "title": "Load test", "description": "k6 load test for target throughput", "type": "testing", "priority": "low", "estimated_hours": 1.5, "dependencies": ["TEST-002"], "milestone": "M4"},
    ]


def _generate_deployment_tasks(prompt: str, category: str) -> List[Dict]:
    return [
        {"id": "DEPLOY-001", "title": "Update Docker configuration", "description": "Add new service dependencies to Dockerfile", "type": "deployment", "priority": "medium", "estimated_hours": 1.0, "dependencies": ["BE-002"], "milestone": "M3"},
        {"id": "DEPLOY-002", "title": "Update CI/CD pipeline", "description": "Add new test jobs and deployment steps", "type": "deployment", "priority": "medium", "estimated_hours": 1.0, "dependencies": ["TEST-002"], "milestone": "M3"},
        {"id": "DEPLOY-003", "title": "Staging deployment + smoke test", "description": "Deploy to staging, run manual verification", "type": "deployment", "priority": "high", "estimated_hours": 1.0, "dependencies": ["DEPLOY-001", "DEPLOY-002"], "milestone": "M4"},
        {"id": "DEPLOY-004", "title": "Production deployment", "description": "Deploy with feature flag, monitor for 24h", "type": "deployment", "priority": "high", "estimated_hours": 0.5, "dependencies": ["DEPLOY-003"], "milestone": "M4"},
    ]


def _generate_milestones(category: str) -> List[str]:
    return [
        "M1: Foundation — data model and core backend complete",
        "M2: Core functionality — API and UI components working",
        "M3: Integration — frontend connected to backend, tests passing",
        "M4: Production — deployed to staging and production",
    ]


def _build_roadmap(hs: float, problems: List, missing: List, arch_recs: List, deps: Dict) -> List[str]:
    roadmap = []
    if hs < 40:
        roadmap.append("Phase 0 (Week 1): Stabilize — fix critical health issues before new features")
    if not deps.get("has_tests"):
        roadmap.append("Phase 1 (Week 1-2): Testing — establish test suite and coverage baseline")
    if not deps.get("has_docker"):
        roadmap.append("Phase 1 (Week 1-2): Infrastructure — Docker + CI/CD pipeline")
    for m in missing[:3]:
        roadmap.append(f"Feature: {m}")
    for r in arch_recs[:2]:
        roadmap.append(f"Architecture: {r}")
    roadmap.append("Final: Performance optimization and security hardening")
    roadmap.append("Launch: Production deployment with monitoring and alerting")
    return roadmap[:8]


def _build_action_steps(problems: List, missing: List, stuck: List, deps: Dict) -> List[str]:
    steps = []
    for p in problems[:3]:
        steps.append(f"Fix: {p[:80]}")
    for s in stuck[:2]:
        steps.append(f"Unblock: {s[:80]}")
    for m in missing[:2]:
        steps.append(f"Implement: {m[:80]}")
    if not deps.get("has_docker"):
        steps.append("Containerize: Add Dockerfile and docker-compose.yml")
    if not deps.get("has_ci"):
        steps.append("Automate: Set up CI/CD pipeline with GitHub Actions")
    return steps[:10]


def _build_phase_plan(hs: float, missing: List, deps: Dict) -> List[Dict]:
    return [
        {"phase": "Foundation", "week": "1-2", "focus": "Infrastructure, testing, and stability"},
        {"phase": "Core Features", "week": "3-6", "focus": "Build and ship primary feature set"},
        {"phase": "Integration", "week": "7-8", "focus": "Connect components, end-to-end testing"},
        {"phase": "Launch", "week": "9-10", "focus": "Production deployment, monitoring, feedback loop"},
    ]


def _estimate_weeks(hs: float, missing_count: int, problem_count: int) -> int:
    base = 4
    if hs < 40:
        base += 2
    base += missing_count // 2
    return min(base, 16)
