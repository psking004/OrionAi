from typing import Dict, Any, List


def run(
    issues: Dict[str, Any],
    health: Dict[str, Any],
    structure: Dict[str, Any],
    commit_data: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    momentum = (commit_data or {}).get("momentum", "unknown")
    problems = issues.get("problems", [])
    missing = issues.get("missing_features", [])
    health_score = health.get("health_score", 50)

    recommendations = _recommendations(momentum, problems, missing, health_score)
    risks = _risks(momentum, health, issues)
    priorities = _priorities(problems, missing, health_score)
    actions = _actions(momentum, missing)

    score = _pm_score(health_score, momentum, problems)

    return {
        "agent": "PM Agent",
        "role": "Product Manager",
        "recommendations": recommendations[:6],
        "risks": risks[:5],
        "priorities": priorities[:5],
        "actions": actions[:5],
        "score": score,
    }


def _recommendations(momentum: str, problems: List, missing: List, hs: float) -> List[str]:
    recs = []
    if momentum in ("slow", "stalled"):
        recs.append("Velocity is low — run a team retrospective to identify blockers")
    if len(missing) > 4:
        recs.append(f"{len(missing)} missing features detected — prioritize ruthlessly using MoSCoW method")
    if len(problems) > 5:
        recs.append("High problem count — allocate 20% of sprint capacity to technical debt")
    recs.append("Define a clear MVP scope and ensure all features map to user stories")
    recs.append("Implement feature flags for risky deployments")
    recs.append("Track DORA metrics: deployment frequency, lead time, MTTR, change failure rate")
    if hs < 50:
        recs.append("Health score is low — negotiate tech debt sprint with engineering")
    return recs


def _risks(momentum: str, health: Dict, issues: Dict) -> List[str]:
    risks = []
    if momentum == "stalled":
        risks.append("Project velocity has stalled — delivery timeline at risk")
    stuck = issues.get("stuck_points", [])
    for s in stuck[:2]:
        risks.append(f"Blocker: {s}")
    if health.get("health_score", 50) < 40:
        risks.append("Critical technical debt may block feature development")
    risks.append("Scope creep risk if architectural issues are not addressed first")
    return risks


def _priorities(problems: List, missing: List, hs: float) -> List[str]:
    priorities = []
    if hs < 40:
        priorities.append("P0: Address critical health issues before new features")
    for p in problems[:2]:
        priorities.append(f"P1: {p[:80]}")
    if missing:
        priorities.append(f"P2: Ship missing features: {missing[0][:60]}")
    priorities.append("P3: Improve developer experience to increase velocity")
    return priorities


def _actions(momentum: str, missing: List) -> List[str]:
    actions = []
    actions.append("Create and groom product backlog in priority order")
    actions.append("Define acceptance criteria for all in-flight features")
    if missing:
        actions.append(f"Add to next sprint: {missing[0][:60]}")
    actions.append("Set up weekly stakeholder demo cadence")
    actions.append("Document user personas and key jobs-to-be-done")
    return actions


def _pm_score(hs: float, momentum: str, problems: List) -> float:
    score = hs * 0.5
    momentum_map = {"strong": 40, "steady": 30, "slow": 15, "stalled": 5, "unknown": 20}
    score += momentum_map.get(momentum, 20)
    score -= min(len(problems) * 2, 20)
    return round(min(max(score, 0), 100), 1)
