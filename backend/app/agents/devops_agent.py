from typing import Dict, Any, List


def run(
    dependencies: Dict[str, Any],
    arch_analysis: Dict[str, Any],
    health: Dict[str, Any],
    risk: Dict[str, Any],
) -> Dict[str, Any]:
    has_docker = dependencies.get("has_docker", False)
    has_ci = dependencies.get("has_ci", False)
    cloud = dependencies.get("cloud", [])
    devops_tools = dependencies.get("devops", [])

    recommendations = _recommendations(has_docker, has_ci, cloud, devops_tools)
    risks = _risks(has_docker, has_ci, risk)
    priorities = _priorities(has_docker, has_ci, cloud)
    actions = _actions(has_docker, has_ci)
    score = _devops_score(has_docker, has_ci, cloud, devops_tools)

    return {
        "agent": "DevOps Agent",
        "role": "DevOps Engineer",
        "recommendations": recommendations[:6],
        "risks": risks[:5],
        "priorities": priorities[:5],
        "actions": actions[:5],
        "score": score,
    }


def _recommendations(has_docker: bool, has_ci: bool, cloud: List, tools: List) -> List[str]:
    recs = []
    if not has_docker:
        recs.append("Containerize with Docker — create multi-stage Dockerfile for lean production images")
    if not has_ci:
        recs.append("Set up GitHub Actions: lint → test → build → deploy pipeline")
    if not cloud:
        recs.append("Choose a cloud provider: Railway/Render (simple), AWS/GCP (advanced)")
    recs.append("Implement environment parity: dev = staging = prod (same Docker image)")
    recs.append("Store secrets in environment variables, never in code or docker-compose")
    recs.append("Set up infrastructure monitoring: uptime alerts, CPU/memory dashboards")
    if has_docker and not has_ci:
        recs.append("Docker ready — now automate deployments with CI/CD")
    return recs


def _risks(has_docker: bool, has_ci: bool, risk: Dict) -> List[str]:
    risks = []
    if not has_docker:
        risks.append("No containerization — environment drift between dev and prod")
    if not has_ci:
        risks.append("Manual deployments — high risk of human error and downtime")
    for r in risk.get("deployment_risks", [])[:2]:
        risks.append(r)
    risks.append("No zero-downtime deployment strategy configured")
    return risks


def _priorities(has_docker: bool, has_ci: bool, cloud: List) -> List[str]:
    priorities = []
    if not has_docker:
        priorities.append("P0: Write Dockerfile and docker-compose.yml")
    if not has_ci:
        priorities.append("P0: Create CI/CD pipeline")
    if not cloud:
        priorities.append("P1: Select and configure cloud hosting")
    priorities.append("P2: Configure auto-scaling policy")
    priorities.append("P3: Implement blue-green deployment")
    return priorities


def _actions(has_docker: bool, has_ci: bool) -> List[str]:
    actions = []
    if not has_docker:
        actions.append("Write Dockerfile with multi-stage build (builder + runtime stages)")
        actions.append("Write docker-compose.yml with app + postgres + redis services")
    if not has_ci:
        actions.append("Create .github/workflows/deploy.yml")
    actions.append("Configure health check endpoint for load balancer probes")
    actions.append("Set up centralized logging aggregation (Loki, CloudWatch, or Papertrail)")
    return actions


def _devops_score(has_docker: bool, has_ci: bool, cloud: List, tools: List) -> float:
    score = 20.0
    if has_docker:
        score += 30
    if has_ci:
        score += 25
    if cloud:
        score += 15
    score += min(len(tools) * 5, 10)
    return round(min(score, 100), 1)
