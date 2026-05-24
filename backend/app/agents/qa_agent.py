from typing import Dict, Any, List


def run(
    code_scan: Dict[str, Any],
    arch_analysis: Dict[str, Any],
    health: Dict[str, Any],
) -> Dict[str, Any]:
    has_tests = code_scan.get("has_tests", False)
    has_logging = code_scan.get("has_logging", False)
    issues = code_scan.get("issues", [])
    security_issues = code_scan.get("security_issues", [])
    perf_issues = code_scan.get("performance_issues", [])

    recommendations = _recommendations(has_tests, issues, security_issues, perf_issues)
    risks = _risks(has_tests, issues, security_issues)
    priorities = _priorities(has_tests, security_issues, issues)
    actions = _actions(has_tests, has_logging)
    score = _qa_score(has_tests, has_logging, len(issues), len(security_issues))

    return {
        "agent": "QA Agent",
        "role": "Quality Assurance Engineer",
        "recommendations": recommendations[:6],
        "risks": risks[:5],
        "priorities": priorities[:5],
        "actions": actions[:5],
        "score": score,
    }


def _recommendations(has_tests: bool, issues: List, security: List, perf: List) -> List[str]:
    recs = []
    if not has_tests:
        recs.append("CRITICAL: No tests detected — establish testing pyramid immediately")
        recs.append("Start with integration tests for all API endpoints (highest ROI)")
        recs.append("Add pytest + pytest-cov for Python, Vitest for TypeScript")
    else:
        recs.append("Tests detected — ensure coverage reports are tracked (target >70%)")
        recs.append("Add mutation testing to validate test quality")
    if security:
        recs.append(f"Fix {len(security)} security issues before next deployment")
    if perf:
        recs.append(f"Address {len(perf)} performance anti-patterns")
    recs.append("Implement load testing (k6/Locust) before production launch")
    recs.append("Add end-to-end tests for critical user journeys (Playwright/Cypress)")
    return recs


def _risks(has_tests: bool, issues: List, security: List) -> List[str]:
    risks = []
    if not has_tests:
        risks.append("No test coverage — regressions will reach production undetected")
    if security:
        risks.append(f"{len(security)} security vulnerabilities in code — immediate fix required")
    for i in issues[:2]:
        risks.append(i[:100])
    risks.append("No QA gate in deployment pipeline — broken code can reach production")
    return risks


def _priorities(has_tests: bool, security: List, issues: List) -> List[str]:
    priorities = []
    if security:
        priorities.append("P0: Fix all security vulnerabilities")
    if not has_tests:
        priorities.append("P0: Add test suite — no release without tests")
    priorities.append("P1: Add API contract tests")
    priorities.append("P2: Implement automated regression suite")
    priorities.append("P3: Add chaos engineering tests")
    return priorities


def _actions(has_tests: bool, has_logging: bool) -> List[str]:
    actions = []
    if not has_tests:
        actions.append("Create tests/ directory and write first 10 unit tests")
        actions.append("Configure coverage reporting in CI pipeline")
    if not has_logging:
        actions.append("Add structured logging to all service functions")
    actions.append("Write test plan document covering happy paths and edge cases")
    actions.append("Set up automated security scanning (Bandit for Python, npm audit)")
    return actions


def _qa_score(has_tests: bool, has_logging: bool, issue_count: int, security_count: int) -> float:
    score = 30.0
    if has_tests:
        score += 35
    if has_logging:
        score += 15
    score -= min(issue_count * 2, 20)
    score -= min(security_count * 5, 30)
    return round(min(max(score, 0), 100), 1)
