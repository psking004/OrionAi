from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


def analyze_commit_velocity(commits: List[Dict]) -> Dict[str, Any]:
    if not commits:
        return {
            "velocity_score": 0,
            "commit_frequency": "no_data",
            "avg_commits_per_week": 0,
            "recent_activity": [],
            "stalled_modules": [],
            "risky_commits": [],
            "momentum": "unknown",
        }

    total = len(commits)
    risky = _detect_risky_commits(commits)
    stalled = _detect_stalled_work(commits)
    frequency = _compute_frequency(commits, total)
    momentum = _classify_momentum(total, risky)

    return {
        "velocity_score": _compute_velocity_score(total, risky, commits),
        "commit_frequency": frequency,
        "total_commits_analyzed": total,
        "avg_commits_per_week": _avg_per_week(commits),
        "recent_activity": commits[:5],
        "stalled_modules": stalled,
        "risky_commits": risky,
        "momentum": momentum,
    }


def _detect_risky_commits(commits: List[Dict]) -> List[Dict]:
    risky = []
    risky_keywords = [
        "hotfix", "urgent", "critical", "broken", "rollback", "revert",
        "fix crash", "production bug", "emergency", "temp", "hack", "workaround",
    ]
    for c in commits:
        msg = c.get("message", "").lower()
        if any(kw in msg for kw in risky_keywords):
            risky.append({
                "sha": c.get("sha", ""),
                "message": c.get("message", ""),
                "reason": "Contains risk indicator keywords",
            })
    return risky[:10]


def _detect_stalled_work(commits: List[Dict]) -> List[str]:
    stalled = []
    wip_msgs = [c.get("message", "").lower() for c in commits]
    wip_patterns = ["wip", "in progress", "todo", "not done", "incomplete", "broken", "temp"]
    wip_count = sum(1 for m in wip_msgs if any(p in m for p in wip_patterns))
    if wip_count > 3:
        stalled.append(f"High WIP commit count ({wip_count}) — work may be stalled")
    return stalled


def _compute_frequency(commits: List[Dict], total: int) -> str:
    if total >= 20:
        return "high"
    elif total >= 10:
        return "moderate"
    elif total >= 3:
        return "low"
    else:
        return "minimal"


def _classify_momentum(total: int, risky: List) -> str:
    risky_ratio = len(risky) / max(total, 1)
    if total >= 15 and risky_ratio < 0.2:
        return "strong"
    elif total >= 5 and risky_ratio < 0.4:
        return "steady"
    elif total >= 1:
        return "slow"
    else:
        return "stalled"


def _compute_velocity_score(total: int, risky: List, commits: List[Dict]) -> float:
    base = min(total * 3, 60)
    risky_penalty = len(risky) * 5
    score = base - risky_penalty
    return round(min(max(score, 0), 100), 1)


def _avg_per_week(commits: List[Dict]) -> float:
    if len(commits) < 2:
        return float(len(commits))

    try:
        dates = []
        for c in commits:
            date_str = c.get("date", "")
            if date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                dates.append(dt)

        if len(dates) < 2:
            return float(len(commits))

        dates.sort()
        span_days = (dates[-1] - dates[0]).days or 1
        weeks = max(span_days / 7, 1)
        return round(len(commits) / weeks, 1)
    except Exception:
        return float(len(commits))
