"""
AI Teammate logic — rule-based analysis engine.
Detects problems, progress, stuck points; generates health score and next steps.
Optionally uses OpenAI when OPENAI_API_KEY is configured.
"""
import json
import re
from typing import List, Tuple
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── keyword banks ─────────────────────────────────────────────────────────────
_PROBLEM_PATTERNS = [
    r"\berror\b", r"\bbug\b", r"\bfail(ed|ing|ure)?\b", r"\bcrash(ed|ing)?\b",
    r"\bbroken?\b", r"\bissue\b", r"\bproblem\b", r"\bstuck\b", r"\bcan'?t\b",
    r"\bcannot\b", r"\bexception\b", r"\bundefined\b", r"\bnull pointer\b",
    r"\btimeout\b", r"\bnot working\b", r"\bdoesn'?t work\b", r"\bblocked?\b",
]

_PROGRESS_PATTERNS = [
    r"\bdone\b", r"\bfixed?\b", r"\bcompleted?\b", r"\bdeployed?\b",
    r"\bshipped?\b", r"\bworking\b", r"\bresolved?\b", r"\bfinished?\b",
    r"\bmerged?\b", r"\blaunched?\b", r"\bpassed?\b", r"\bsuccess(ful)?\b",
    r"\bimplemented?\b",
]

_PROB_RE = re.compile("|".join(_PROBLEM_PATTERNS), re.IGNORECASE)
_PROG_RE = re.compile("|".join(_PROGRESS_PATTERNS), re.IGNORECASE)


def _extract_sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"[.!?\n]", text) if s.strip()]


def analyze_messages(messages: List[dict]) -> Tuple[
    str, List[str], List[str], List[str], List[str], float
]:
    """
    Returns (progress, problems, stuck_points, next_steps, missing_features, health_score).
    Each message dict must have keys: role, content.
    """
    problem_sentences: List[str] = []
    progress_sentences: List[str] = []
    problem_topics: dict[str, int] = {}  # topic → count, for stuck detection

    for msg in messages:
        if msg["role"] not in ("user", "assistant"):
            continue
        content = msg["content"]
        sentences = _extract_sentences(content)

        for sentence in sentences:
            if _PROB_RE.search(sentence):
                short = sentence[:200]
                problem_sentences.append(short)
                # extract first keyword as topic
                m = _PROB_RE.search(sentence)
                if m:
                    topic = m.group(0).lower()
                    problem_topics[topic] = problem_topics.get(topic, 0) + 1

            if _PROG_RE.search(sentence):
                progress_sentences.append(sentence[:200])

    # ── stuck points: topics mentioned 2+ times ────────────────────────────
    stuck_points = [
        f"Recurring issue with '{topic}' (mentioned {count} times)"
        for topic, count in problem_topics.items()
        if count >= 2
    ]

    # ── health score ───────────────────────────────────────────────────────
    total = len(problem_sentences) + len(progress_sentences)
    if total == 0:
        health_score = 70.0
    else:
        progress_ratio = len(progress_sentences) / total
        problem_ratio = len(problem_sentences) / total
        health_score = round(
            max(10.0, min(100.0, 100 * progress_ratio - 50 * problem_ratio + 50)),
            1,
        )

    # ── progress label ─────────────────────────────────────────────────────
    if health_score >= 80:
        progress_label = "on_track"
    elif health_score >= 55:
        progress_label = "needs_attention"
    elif health_score >= 30:
        progress_label = "at_risk"
    else:
        progress_label = "critical"

    # ── deduplicate and cap lists ──────────────────────────────────────────
    seen: set[str] = set()
    unique_problems: List[str] = []
    for p in problem_sentences:
        key = p[:60].lower()
        if key not in seen:
            seen.add(key)
            unique_problems.append(p)
        if len(unique_problems) == 10:
            break

    # ── next steps (rule-based from problems + progress) ──────────────────
    next_steps = _generate_next_steps(unique_problems, progress_sentences, stuck_points)

    # ── missing features ──────────────────────────────────────────────────
    missing_features = _detect_missing_features(messages)

    return (
        progress_label,
        unique_problems[:10],
        stuck_points[:5],
        next_steps[:5],
        missing_features[:5],
        health_score,
    )


def _generate_next_steps(
    problems: List[str],
    progress: List[str],
    stuck: List[str],
) -> List[str]:
    steps: List[str] = []

    if stuck:
        steps.append(
            f"Resolve recurring blocker: {stuck[0].replace('Recurring issue with ', '').split('(')[0].strip()}"
        )

    if problems:
        steps.append("Fix highest-priority bug or error preventing progress")
        if len(problems) > 3:
            steps.append("Write unit tests to prevent regression of identified bugs")

    if progress:
        steps.append("Document recent wins and update project changelog")

    steps.extend([
        "Review open TODOs and prioritize next sprint tasks",
        "Update README / docs to reflect current project state",
        "Set up CI/CD pipeline if not already in place",
        "Add error monitoring (e.g., Sentry) for production visibility",
    ])

    return steps[:5]


_FEATURE_HINTS = [
    (r"\bauth(entication|orization)?\b", "Authentication / authorization"),
    (r"\btest(ing|s)?\b", "Automated tests"),
    (r"\bdeploy(ment|ed)?\b", "Deployment pipeline"),
    (r"\bdocument(ation|s)?\b", "Documentation"),
    (r"\bmonitor(ing)?\b", "Error monitoring"),
    (r"\bci[/ -]?cd\b", "CI/CD pipeline"),
    (r"\bapi\b", "API design / versioning"),
    (r"\bdatabase?\b", "Database migrations"),
    (r"\bcaching?\b", "Caching layer"),
    (r"\bsecurity\b", "Security audit"),
]


def _detect_missing_features(messages: List[dict]) -> List[str]:
    """Identify features discussed but not yet marked as completed."""
    mentioned: set[str] = set()
    completed: set[str] = set()

    for msg in messages:
        content = msg["content"].lower()
        for pattern, label in _FEATURE_HINTS:
            if re.search(pattern, content, re.IGNORECASE):
                if _PROG_RE.search(content):
                    completed.add(label)
                else:
                    mentioned.add(label)

    return sorted(mentioned - completed)


def generate_prioritized_roadmap(
    project_name: str,
    tech_stack: str,
    messages: List[dict],
) -> Tuple[List[str], List[str]]:
    """Returns (roadmap, actionable_steps)."""
    _, problems, stuck_points, next_steps, missing_features, health_score = analyze_messages(messages)

    roadmap: List[str] = []
    if health_score < 50:
        roadmap.append("Phase 1 — Stabilization: fix critical bugs and unblock stuck points")
    else:
        roadmap.append("Phase 1 — Consolidation: clean up tech debt and improve test coverage")

    if missing_features:
        roadmap.append(f"Phase 2 — Feature completion: {', '.join(missing_features[:3])}")
    else:
        roadmap.append("Phase 2 — Feature polish: improve UX and edge-case handling")

    roadmap.append(f"Phase 3 — Hardening: security review, monitoring, and CI/CD for {project_name}")
    roadmap.append("Phase 4 — Launch preparation: documentation, beta testing, and deployment")
    roadmap.append("Phase 5 — Growth: user feedback loop, analytics, and iterative improvements")

    actionable = next_steps if next_steps else _generate_next_steps(problems, [], stuck_points)
    return roadmap[:5], actionable[:5]


def serialize_list(items: List[str]) -> str:
    return json.dumps(items, ensure_ascii=False)


def deserialize_list(raw: str | None) -> List[str]:
    if not raw:
        return []
    try:
        result = json.loads(raw)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
