from typing import Dict, Any, List, Tuple


def compute_health(
    code_scan: Dict[str, Any],
    arch_analysis: Dict[str, Any],
    structure: Dict[str, Any],
    dependencies: Dict[str, Any],
    commit_data: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    health_score, breakdown = _compute_health_score(code_scan, arch_analysis, structure, dependencies, commit_data)
    debt_score = _compute_debt_score(code_scan)
    stability_score = _compute_stability_score(code_scan, commit_data)
    progress = _classify_progress(health_score)

    return {
        "health_score": health_score,
        "architecture_score": arch_analysis.get("quality_score", 50.0),
        "debt_score": debt_score,
        "stability_score": stability_score,
        "progress": progress,
        "breakdown": breakdown,
    }


def _compute_health_score(
    code: Dict, arch: Dict, structure: Dict, deps: Dict, commits: Dict | None
) -> Tuple[float, Dict[str, float]]:
    # Weighted scoring across dimensions
    test_score = 85.0 if code.get("has_tests") else 20.0
    auth_score = 90.0 if code.get("has_auth") else 30.0
    log_score = 80.0 if code.get("has_logging") else 40.0
    arch_score = arch.get("quality_score", 50.0)

    security_penalty = min(len(code.get("security_issues", [])) * 8, 40)
    issue_penalty = min(len(code.get("issues", [])) * 3, 25)
    perf_penalty = min(len(code.get("performance_issues", [])) * 5, 20)

    base_score = (
        test_score * 0.20 +
        auth_score * 0.15 +
        log_score * 0.10 +
        arch_score * 0.25 +
        80.0 * 0.30  # base code quality
    )

    final = base_score - security_penalty - issue_penalty - perf_penalty

    # Bonus for good practices
    if deps.get("has_docker"):
        final += 3
    if deps.get("has_ci"):
        final += 3
    if deps.get("has_tests"):
        final += 2

    breakdown = {
        "testing": round(test_score, 1),
        "security": round(max(0, 100 - security_penalty * 2.5), 1),
        "architecture": round(arch_score, 1),
        "logging": round(log_score, 1),
        "devops": round(60 + (10 if deps.get("has_docker") else 0) + (10 if deps.get("has_ci") else 0), 1),
    }

    return round(min(max(final, 0), 100), 1), breakdown


def _compute_debt_score(code: Dict) -> float:
    # Lower is better debt score (0 = no debt, 100 = maximum debt)
    issues = len(code.get("issues", []))
    security = len(code.get("security_issues", []))
    perf = len(code.get("performance_issues", []))
    large_files = len(code.get("large_files", []))

    debt = (issues * 3) + (security * 8) + (perf * 5) + (large_files * 4)
    # Return as inverse (higher = less debt)
    return round(max(0, 100 - min(debt, 100)), 1)


def _compute_stability_score(code: Dict, commits: Dict | None) -> float:
    score = 70.0

    if code.get("has_tests"):
        score += 15
    if code.get("has_logging"):
        score += 5

    security_count = len(code.get("security_issues", []))
    score -= min(security_count * 5, 30)

    if commits:
        velocity = commits.get("velocity_score", 50)
        score = score * 0.7 + velocity * 0.3

    return round(min(max(score, 0), 100), 1)


def _classify_progress(health_score: float) -> str:
    if health_score >= 75:
        return "on_track"
    elif health_score >= 55:
        return "needs_attention"
    elif health_score >= 35:
        return "at_risk"
    else:
        return "critical"
