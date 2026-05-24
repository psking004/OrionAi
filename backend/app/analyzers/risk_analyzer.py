from typing import Dict, Any, List


def predict_failures(
    code_scan: Dict[str, Any],
    arch_analysis: Dict[str, Any],
    dependencies: Dict[str, Any],
    commit_data: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    deployment_risks = _deployment_risks(arch_analysis, dependencies)
    scalability_issues = _scalability_issues(code_scan, arch_analysis, dependencies)
    unstable_modules = _unstable_modules(code_scan, commit_data)
    security_vulns = _security_vulnerabilities(code_scan, dependencies)
    bottlenecks = _future_bottlenecks(code_scan, arch_analysis, dependencies)

    all_risks = deployment_risks + scalability_issues + security_vulns
    risk_score = _compute_risk_score(len(deployment_risks), len(security_vulns), len(all_risks))
    risk_level = _classify_risk(risk_score)
    mitigations = _mitigation_strategies(deployment_risks, scalability_issues, security_vulns)

    return {
        "deployment_risks": deployment_risks[:8],
        "scalability_issues": scalability_issues[:6],
        "unstable_modules": unstable_modules[:5],
        "security_vulnerabilities": security_vulns[:8],
        "future_bottlenecks": bottlenecks[:6],
        "overall_risk_score": risk_score,
        "risk_level": risk_level,
        "mitigation_strategies": mitigations[:10],
    }


def _deployment_risks(arch: Dict, deps: Dict) -> List[str]:
    risks = []
    if not deps.get("has_docker"):
        risks.append("No containerization — deployment environment inconsistency risk")
    if not deps.get("has_ci"):
        risks.append("No CI/CD — manual deployments increase human error risk")
    if not arch.get("deployment_readiness", {}).get("ready"):
        risks.append("Deployment infrastructure not configured")
    if not deps.get("databases"):
        risks.append("No database detected — data persistence on restart will be lost")
    return risks


def _scalability_issues(code: Dict, arch: Dict, deps: Dict) -> List[str]:
    issues = []
    arch_type = arch.get("type", "")
    if arch_type == "monolith" and code.get("files_analyzed", 0) > 30:
        issues.append("Large monolith — single point of scaling failure")
    if "Redis" not in deps.get("databases", []):
        issues.append("No caching layer — database may become bottleneck under load")
    if not deps.get("cloud"):
        issues.append("No cloud infrastructure configured — scaling requires manual intervention")
    perf_issues = code.get("performance_issues", [])
    if len(perf_issues) > 2:
        issues.append(f"{len(perf_issues)} performance anti-patterns detected — will worsen under load")
    return issues


def _unstable_modules(code: Dict, commits: Dict | None) -> List[str]:
    modules = []
    for issue in code.get("issues", []):
        if "syntax error" in issue.lower():
            modules.append(issue.split(" in ")[-1] if " in " in issue else issue)
    if commits:
        for risky in commits.get("risky_commits", []):
            modules.append(f"Risky commit pattern: {risky.get('message', '')[:60]}")
    return modules[:5]


def _security_vulnerabilities(code: Dict, deps: Dict) -> List[str]:
    vulns = list(code.get("security_issues", []))
    all_deps = list(deps.get("python", {}).keys()) + list(deps.get("node", {}).keys())

    if not any(r in all_deps for r in ["slowapi", "express-rate-limit", "flask-limiter"]):
        vulns.append("No rate limiting detected — API vulnerable to brute force")
    if not code.get("has_auth"):
        vulns.append("No authentication detected — all endpoints potentially public")

    return vulns


def _future_bottlenecks(code: Dict, arch: Dict, deps: Dict) -> List[str]:
    bottlenecks = []

    large_files = code.get("large_files", [])
    if large_files:
        bottlenecks.append(f"Large files will slow build/deployment: {', '.join(large_files[:2])}")

    if not deps.get("databases"):
        bottlenecks.append("In-memory data storage — will hit capacity limits")

    if arch.get("type") == "monolith":
        bottlenecks.append("Monolithic architecture — team velocity bottleneck at scale")

    all_deps = list(deps.get("python", {}).keys()) + list(deps.get("node", {}).keys())
    if not any(q in all_deps for q in ["celery", "rq", "bull", "agenda", "dramatiq"]):
        bottlenecks.append("No task queue — long-running operations will block API responses")

    return bottlenecks


def _compute_risk_score(deploy: int, security: int, total: int) -> float:
    score = (deploy * 8) + (security * 12) + (total * 2)
    return round(min(score, 100), 1)


def _classify_risk(score: float) -> str:
    if score >= 70:
        return "critical"
    elif score >= 45:
        return "high"
    elif score >= 20:
        return "medium"
    else:
        return "low"


def _mitigation_strategies(deploy: List, scale: List, security: List) -> List[str]:
    strategies = []
    if deploy:
        strategies.append("Add Docker + docker-compose for consistent deployments")
        strategies.append("Configure GitHub Actions for automated CI/CD")
    if security:
        strategies.append("Implement rate limiting on all public endpoints")
        strategies.append("Add security headers (HSTS, CSP, X-Frame-Options)")
        strategies.append("Rotate all secrets and store in environment variables")
    if scale:
        strategies.append("Add Redis caching for frequently-accessed data")
        strategies.append("Configure horizontal scaling with load balancer")
    strategies.append("Set up error monitoring (Sentry) for production visibility")
    strategies.append("Implement database connection pooling for concurrent requests")
    return strategies
