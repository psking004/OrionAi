from typing import Dict, Any, List


def run(
    code_scan: Dict[str, Any],
    dependencies: Dict[str, Any],
    arch_analysis: Dict[str, Any],
    risk: Dict[str, Any],
) -> Dict[str, Any]:
    security_issues = code_scan.get("security_issues", [])
    has_auth = code_scan.get("has_auth", False)
    all_deps = list(dependencies.get("python", {}).keys()) + list(dependencies.get("node", {}).keys())

    recommendations = _recommendations(security_issues, has_auth, all_deps)
    risks = _risks(security_issues, has_auth, risk)
    priorities = _priorities(security_issues, has_auth)
    actions = _actions(security_issues, has_auth, all_deps)
    score = _security_score(security_issues, has_auth, all_deps)

    return {
        "agent": "Security Agent",
        "role": "Security Engineer",
        "recommendations": recommendations[:6],
        "risks": risks[:5],
        "priorities": priorities[:5],
        "actions": actions[:5],
        "score": score,
    }


def _recommendations(security_issues: List, has_auth: bool, deps: List) -> List[str]:
    recs = []
    if not has_auth:
        recs.append("CRITICAL: No authentication detected — all endpoints are publicly accessible")
    if security_issues:
        recs.append(f"Fix {len(security_issues)} security vulnerabilities before production deployment")
    if not any(r in deps for r in ["slowapi", "express-rate-limit", "flask-limiter"]):
        recs.append("Add rate limiting to prevent brute force and DDoS attacks")
    recs.append("Implement HTTPS-only with HSTS headers in production")
    recs.append("Set security headers: CSP, X-Frame-Options, X-Content-Type-Options")
    recs.append("Run dependency audit regularly: pip-audit / npm audit")
    recs.append("Implement secrets rotation policy — rotate all keys every 90 days")
    return recs


def _risks(security_issues: List, has_auth: bool, risk: Dict) -> List[str]:
    risks = []
    if not has_auth:
        risks.append("CRITICAL: No authentication — unauthorized access to all resources")
    for issue in security_issues[:3]:
        risks.append(f"VULNERABILITY: {issue[:100]}")
    for vuln in risk.get("security_vulnerabilities", [])[:2]:
        risks.append(vuln[:100])
    return risks


def _priorities(security_issues: List, has_auth: bool) -> List[str]:
    priorities = []
    if not has_auth:
        priorities.append("P0: Implement authentication immediately")
    if security_issues:
        priorities.append(f"P0: Fix {len(security_issues)} security vulnerabilities")
    priorities.append("P1: Add input validation and sanitization")
    priorities.append("P1: Implement RBAC (Role-Based Access Control)")
    priorities.append("P2: Add security scanning to CI/CD pipeline")
    return priorities


def _actions(security_issues: List, has_auth: bool, deps: List) -> List[str]:
    actions = []
    if not has_auth:
        actions.append("Implement JWT authentication with refresh token rotation")
    if security_issues:
        actions.append("Run: bandit -r . (Python) or npm audit fix (Node.js)")
    actions.append("Add OWASP dependency check to CI pipeline")
    actions.append("Enable GitHub security advisories and Dependabot alerts")
    actions.append("Conduct threat modeling session — identify trust boundaries")
    return actions


def _security_score(security_issues: List, has_auth: bool, deps: List) -> float:
    score = 60.0
    if not has_auth:
        score -= 30
    score -= min(len(security_issues) * 8, 40)
    has_rate_limit = any(r in deps for r in ["slowapi", "express-rate-limit"])
    if has_rate_limit:
        score += 10
    return round(min(max(score, 0), 100), 1)
