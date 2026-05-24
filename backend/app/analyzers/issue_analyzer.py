from typing import Dict, Any, List


def analyze_issues(
    code_scan: Dict[str, Any],
    arch_analysis: Dict[str, Any],
    dependencies: Dict[str, Any],
) -> Dict[str, Any]:
    problems = _extract_problems(code_scan, arch_analysis)
    stuck_points = _extract_stuck_points(code_scan, dependencies)
    missing_features = _extract_missing_features(code_scan, dependencies, arch_analysis)

    return {
        "problems": problems[:15],
        "stuck_points": stuck_points[:10],
        "missing_features": missing_features[:10],
    }


def _extract_problems(code: Dict, arch: Dict) -> List[str]:
    problems = []

    # From code scan
    for issue in code.get("security_issues", []):
        problems.append(f"[SECURITY] {issue}")
    for issue in code.get("issues", [])[:8]:
        problems.append(f"[CODE] {issue}")

    # From architecture
    if not arch.get("deployment_readiness", {}).get("ready"):
        problems.append("[DEPLOY] No deployment infrastructure detected")

    separation = arch.get("separation_of_concerns", {})
    if not separation.get("has_tests_dir"):
        problems.append("[QUALITY] No test directory — automated testing missing")
    if not separation.get("has_config_dir"):
        problems.append("[CONFIG] No configuration management detected")

    return problems


def _extract_stuck_points(code: Dict, deps: Dict) -> List[str]:
    stuck = []

    if not code.get("has_auth"):
        stuck.append("Authentication not implemented — blocking user management features")
    if not code.get("has_tests"):
        stuck.append("No tests — makes refactoring risky and slows velocity")
    if not code.get("has_logging"):
        stuck.append("No logging — debugging production issues is difficult")
    if not deps.get("has_docker"):
        stuck.append("No Docker — deployment and environment inconsistency risk")
    if not deps.get("has_ci"):
        stuck.append("No CI/CD — manual deployments slow down iteration speed")
    if not deps.get("databases"):
        stuck.append("No database detected — data persistence not implemented")

    perf_issues = code.get("performance_issues", [])
    if len(perf_issues) > 3:
        stuck.append(f"Multiple performance anti-patterns ({len(perf_issues)}) — may cause production slowdowns")

    return stuck


def _extract_missing_features(code: Dict, deps: Dict, arch: Dict) -> List[str]:
    missing = []

    if not code.get("has_auth"):
        missing.append("Authentication & authorization system")
    if not code.get("has_tests"):
        missing.append("Test suite (unit + integration tests)")
    if not code.get("has_logging"):
        missing.append("Structured logging and observability")
    if not deps.get("has_docker"):
        missing.append("Docker containerization")
    if not deps.get("has_ci"):
        missing.append("CI/CD pipeline automation")

    # Check for monitoring
    all_deps = list(deps.get("python", {}).keys()) + list(deps.get("node", {}).keys())
    if not any(m in all_deps for m in ["sentry-sdk", "prometheus-client", "datadog", "newrelic"]):
        missing.append("Error monitoring and alerting (Sentry, Datadog, etc.)")

    # Rate limiting
    if not any(r in all_deps for r in ["slowapi", "express-rate-limit", "rate-limiter-flexible"]):
        missing.append("API rate limiting")

    # Documentation
    if not any(d in all_deps for d in ["sphinx", "mkdocs", "jsdoc"]):
        missing.append("API documentation generation")

    return missing
