import re
from typing import Dict, Any, List


ERROR_PATTERNS = [
    (r"ModuleNotFoundError|ImportError|No module named", "missing_dependency", "Python package not installed"),
    (r"AttributeError:\s+['\"]\w+['\"]\s+object has no attribute", "attribute_error", "Object missing expected attribute"),
    (r"KeyError:\s+['\"]?\w+['\"]?", "key_error", "Dictionary key not found"),
    (r"TypeError:\s+.+\(\)", "type_error", "Wrong type passed to function"),
    (r"ValueError:\s+.+", "value_error", "Invalid value"),
    (r"ConnectionRefusedError|ECONNREFUSED", "connection_refused", "Service not running or port blocked"),
    (r"OperationalError|psycopg2|sqlalchemy", "database_error", "Database connection or query error"),
    (r"CORS|Access-Control-Allow-Origin", "cors_error", "CORS misconfiguration"),
    (r"401|Unauthorized|Invalid token|expired", "auth_error", "Authentication failure"),
    (r"403|Forbidden|Permission denied", "authz_error", "Authorization failure"),
    (r"404|Not Found|no such file", "not_found", "Resource or file not found"),
    (r"500|Internal Server Error|unhandled exception", "server_error", "Unhandled server exception"),
    (r"SyntaxError|IndentationError|unexpected token", "syntax_error", "Code syntax error"),
    (r"RecursionError|maximum recursion depth", "recursion_error", "Infinite recursion detected"),
    (r"MemoryError|OOMKilled|out of memory", "memory_error", "Memory exhaustion"),
    (r"TimeoutError|ETIMEDOUT|Request timeout", "timeout_error", "Operation timed out"),
    (r"SSL|certificate|handshake failed", "ssl_error", "SSL/TLS configuration issue"),
    (r"docker|container|pod|kubernetes", "container_error", "Container/orchestration issue"),
    (r"npm ERR|yarn error|pnpm", "npm_error", "Node.js package manager error"),
    (r"ENOMEM|ENOSPC|disk", "system_resource", "System resource exhaustion"),
]

ERROR_FIXES: Dict[str, Dict[str, Any]] = {
    "missing_dependency": {
        "fixes": [
            "Run: pip install -r requirements.txt (Python) or npm install (Node.js)",
            "Check if the package name is correct in requirements.txt/package.json",
            "Verify you are in the correct virtual environment",
        ],
        "prevention": ["Pin all dependencies with exact versions", "Use lockfiles (poetry.lock, package-lock.json)"],
        "severity": "high",
    },
    "database_error": {
        "fixes": [
            "Verify DATABASE_URL environment variable is set correctly",
            "Check if PostgreSQL is running: pg_isready or docker ps",
            "Verify network connectivity to database host",
            "Check database user permissions",
        ],
        "prevention": ["Add database health checks on startup", "Implement connection pooling (PgBouncer)"],
        "severity": "critical",
    },
    "cors_error": {
        "fixes": [
            "Add the frontend origin to CORS allow_origins list",
            "Ensure allow_credentials=False when using wildcard origins",
            "Check that CORS middleware is registered before route handlers",
        ],
        "prevention": ["Use environment-specific CORS configs", "Test CORS in CI pipeline"],
        "severity": "medium",
    },
    "auth_error": {
        "fixes": [
            "Check that JWT token is included in Authorization header: 'Bearer <token>'",
            "Verify the token has not expired",
            "Confirm SECRET_KEY environment variable matches the one used to sign the token",
        ],
        "prevention": ["Implement token refresh flow", "Log auth failures with context (not secrets)"],
        "severity": "high",
    },
    "connection_refused": {
        "fixes": [
            "Verify the target service is running on the expected port",
            "Check firewall/security group rules",
            "Confirm the hostname/IP is correct in configuration",
        ],
        "prevention": ["Add health checks and readiness probes", "Use service discovery instead of hardcoded IPs"],
        "severity": "high",
    },
    "syntax_error": {
        "fixes": [
            "Run linter: flake8/ruff (Python) or eslint (JS/TS)",
            "Check the file and line number in the stack trace",
            "Use an IDE with real-time error highlighting",
        ],
        "prevention": ["Add pre-commit hooks for linting", "Configure editor formatting on save"],
        "severity": "high",
    },
}


def analyze_debug(logs: str, error_trace: str | None, context: str | None, project_id: int) -> Dict[str, Any]:
    combined = f"{logs}\n{error_trace or ''}\n{context or ''}"

    error_type, error_description = _detect_error_type(combined)
    affected_modules = _extract_affected_modules(combined)
    fix_data = ERROR_FIXES.get(error_type, {})

    suggested_fixes = fix_data.get("fixes", _generic_fixes(error_type))
    prevention = fix_data.get("prevention", [])
    severity = fix_data.get("severity", _estimate_severity(combined))

    root_cause = _extract_root_cause(combined, error_type, error_description)
    similar_patterns = _find_similar_patterns(error_type)

    return {
        "project_id": project_id,
        "error_type": error_type,
        "root_cause": root_cause,
        "affected_modules": affected_modules,
        "severity": severity,
        "suggested_fixes": (suggested_fixes + prevention)[:8],
        "prevention_strategies": prevention[:4],
        "similar_patterns": similar_patterns[:3],
    }


def _detect_error_type(text: str) -> tuple[str | None, str]:
    for pattern, err_type, description in ERROR_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return err_type, description
    return "unknown_error", "Unrecognized error pattern"


def _extract_affected_modules(text: str) -> List[str]:
    modules = []
    file_patterns = [
        r'File "([^"]+\.py)"',
        r'at ([A-Za-z0-9_/]+\.[jt]sx?):',
        r'in (\w+\.py)',
        r'Module: ([A-Za-z0-9._]+)',
    ]
    for pattern in file_patterns:
        matches = re.findall(pattern, text)
        for m in matches[:3]:
            clean = m.split("/")[-1] if "/" in m else m
            if clean and clean not in modules:
                modules.append(clean)
    return modules[:5]


def _extract_root_cause(text: str, error_type: str | None, description: str) -> str:
    lines = text.strip().splitlines()
    for line in reversed(lines):
        line = line.strip()
        if line and any(kw in line.lower() for kw in ["error", "exception", "failed", "cannot", "not found"]):
            return f"{description}: {line[:200]}"
    return f"{description}. Review the full stack trace for the exact origin."


def _estimate_severity(text: str) -> str:
    text_lower = text.lower()
    if any(kw in text_lower for kw in ["critical", "fatal", "crash", "oom", "data loss"]):
        return "critical"
    if any(kw in text_lower for kw in ["error", "exception", "failed", "refused"]):
        return "high"
    if any(kw in text_lower for kw in ["warning", "warn", "deprecated"]):
        return "medium"
    return "low"


def _generic_fixes(error_type: str | None) -> List[str]:
    return [
        "Review the full stack trace starting from the bottom",
        "Add detailed logging around the failing code section",
        "Reproduce the issue in a local environment with debug mode enabled",
        "Check recent git commits for changes that may have introduced the issue",
    ]


def _find_similar_patterns(error_type: str | None) -> List[str]:
    patterns = {
        "database_error": ["Connection pool exhaustion under load", "Schema migration not applied", "Timeout on slow queries"],
        "auth_error": ["Token signed with wrong secret", "Clock skew causing expiry", "Missing auth header"],
        "cors_error": ["Preflight OPTIONS request blocked", "Credentials not allowed with wildcard", "Missing CORS on error responses"],
        "missing_dependency": ["Dependency in requirements but not installed", "Wrong Python/Node version", "Missing system library"],
    }
    return patterns.get(error_type or "", ["Check application logs for more context", "Review recent code changes"])
