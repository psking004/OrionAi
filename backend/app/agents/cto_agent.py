from typing import Dict, Any, List


def run(
    arch_analysis: Dict[str, Any],
    health: Dict[str, Any],
    risk: Dict[str, Any],
    dependencies: Dict[str, Any],
    structure: Dict[str, Any],
) -> Dict[str, Any]:
    arch_type = arch_analysis.get("type", "unknown")
    frameworks = dependencies.get("frameworks", [])
    health_score = health.get("health_score", 50)
    arch_score = health.get("architecture_score", 50)

    recommendations = _build_recommendations(arch_type, frameworks, health, dependencies)
    risks = _build_risks(arch_analysis, health, risk)
    priorities = _build_priorities(health, arch_analysis, dependencies)
    actions = _build_actions(arch_type, dependencies, health)

    score = round((health_score * 0.4 + arch_score * 0.6), 1)

    return {
        "agent": "CTO Agent",
        "role": "Chief Technology Officer",
        "recommendations": recommendations[:6],
        "risks": risks[:5],
        "priorities": priorities[:5],
        "actions": actions[:5],
        "score": score,
    }


def _build_recommendations(arch: str, frameworks: List, health: Dict, deps: Dict) -> List[str]:
    recs = []
    if not deps.get("has_docker"):
        recs.append("Containerize the application with Docker — required for consistent production deployments")
    if not deps.get("has_ci"):
        recs.append("Implement CI/CD with GitHub Actions — automate testing and deployment pipelines")
    if arch == "monolith" and health.get("health_score", 50) > 60:
        recs.append("Monolith is healthy — delay microservices migration until team exceeds 10 engineers")
    if "PostgreSQL" in deps.get("databases", []):
        recs.append("PostgreSQL is a solid choice — implement connection pooling (PgBouncer) before scaling")
    if not deps.get("has_tests"):
        recs.append("Establish testing pyramid: unit (70%) + integration (20%) + e2e (10%)")
    recs.append("Implement semantic versioning and maintain a CHANGELOG for all releases")
    recs.append("Define SLOs: 99.9% uptime, <200ms p95 response time, <1% error rate")
    return recs


def _build_risks(arch: Dict, health: Dict, risk: Dict) -> List[str]:
    risks = []
    risk_level = risk.get("risk_level", "medium")
    if risk_level in ("high", "critical"):
        risks.append(f"Overall risk level: {risk_level.upper()} — immediate action required")
    for r in risk.get("deployment_risks", [])[:2]:
        risks.append(r)
    for r in risk.get("scalability_issues", [])[:2]:
        risks.append(r)
    if health.get("health_score", 50) < 40:
        risks.append("Critical health score — technical debt is blocking velocity")
    return risks


def _build_priorities(health: Dict, arch: Dict, deps: Dict) -> List[str]:
    priorities = []
    hs = health.get("health_score", 50)
    if hs < 40:
        priorities.append("P0: Stabilize existing codebase before adding features")
    if not deps.get("has_tests"):
        priorities.append("P1: Add test coverage — minimum 60% before next sprint")
    if not deps.get("has_docker"):
        priorities.append("P1: Containerize application")
    priorities.append("P2: Document architecture decisions (ADRs)")
    priorities.append("P2: Set up observability stack (metrics, logs, traces)")
    return priorities


def _build_actions(arch: str, deps: Dict, health: Dict) -> List[str]:
    actions = []
    if not deps.get("has_docker"):
        actions.append("Write Dockerfile and docker-compose.yml this sprint")
    if not deps.get("has_ci"):
        actions.append("Create .github/workflows/ci.yml with lint + test + build steps")
    actions.append("Schedule architecture review with team — document current state")
    actions.append("Set up Sentry for error monitoring in production")
    actions.append("Create runbook for common production incidents")
    return actions
