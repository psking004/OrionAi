import ast
import os
import re
from typing import Dict, List, Any

MAX_FILE_SIZE = 500_000  # 500KB
LARGE_FILE_THRESHOLD = 300  # lines
MAX_FUNCTION_LINES = 80
SCAN_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb"}


def scan_code(root_path: str) -> Dict[str, Any]:
    issues: List[str] = []
    security_issues: List[str] = []
    performance_issues: List[str] = []
    large_files: List[str] = []
    files_analyzed = 0
    total_lines = 0
    has_auth = False
    has_tests = False
    has_logging = False
    missing_validation = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in {
            "node_modules", "venv", ".venv", "build", "dist", "__pycache__"
        }]

        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in SCAN_EXTENSIONS:
                continue

            fpath = os.path.join(dirpath, fname)
            rel = os.path.relpath(fpath, root_path)

            try:
                size = os.path.getsize(fpath)
                if size > MAX_FILE_SIZE:
                    large_files.append(f"{rel} ({size // 1024}KB - too large to analyze)")
                    continue

                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                lines = content.splitlines()
                line_count = len(lines)
                total_lines += line_count
                files_analyzed += 1

                if line_count > LARGE_FILE_THRESHOLD:
                    large_files.append(f"{rel} ({line_count} lines)")

                # Auth detection
                if any(kw in content for kw in ["jwt", "JWT", "bearer", "Bearer", "auth_token", "access_token"]):
                    has_auth = True

                # Test detection
                if "test_" in fname or fname.startswith("test") or "_spec" in fname:
                    has_tests = True
                if any(kw in content for kw in ["def test_", "it(", "describe(", "pytest", "unittest"]):
                    has_tests = True

                # Logging
                if any(kw in content for kw in ["logging", "logger", "console.log", "winston", "pino"]):
                    has_logging = True

                # Security issues
                _detect_security(content, rel, security_issues)

                # Performance issues
                _detect_performance(content, rel, performance_issues)

                # Python-specific AST analysis
                if ext == ".py":
                    py_issues = _analyze_python(content, rel)
                    issues.extend(py_issues)

                # General code quality
                _detect_quality_issues(content, rel, issues, line_count)

            except Exception:
                continue

    if not has_auth:
        issues.append("No authentication mechanism detected — add JWT or session-based auth")
    if not has_tests:
        issues.append("No test files detected — add unit and integration tests")
    if not has_logging:
        issues.append("No logging framework detected — add structured logging")

    if large_files:
        issues.insert(0, f"Large files detected (consider splitting): {', '.join(large_files[:5])}")

    return {
        "issues": list(dict.fromkeys(issues))[:30],
        "security_issues": list(dict.fromkeys(security_issues))[:20],
        "performance_issues": list(dict.fromkeys(performance_issues))[:20],
        "files_analyzed": files_analyzed,
        "total_lines": total_lines,
        "has_auth": has_auth,
        "has_tests": has_tests,
        "has_logging": has_logging,
        "large_files": large_files[:10],
    }


def _detect_security(content: str, rel: str, issues: List[str]) -> None:
    checks = [
        (r"password\s*=\s*['\"][^'\"]+['\"]", f"Hardcoded password in {rel}"),
        (r"secret\s*=\s*['\"][^'\"]+['\"]", f"Hardcoded secret in {rel}"),
        (r"api_key\s*=\s*['\"][^'\"]+['\"]", f"Hardcoded API key in {rel}"),
        (r"eval\s*\(", f"Use of eval() in {rel} — potential code injection"),
        (r"exec\s*\(", f"Use of exec() in {rel} — potential code execution risk"),
        (r"os\.system\(", f"os.system() in {rel} — use subprocess instead"),
        (r"shell=True", f"shell=True in subprocess call in {rel} — injection risk"),
        (r"\.format\(.*(?:request|user|input)", f"Potential SQL/template injection via format() in {rel}"),
        (r"SELECT\s+\*\s+FROM", f"SELECT * query in {rel} — specify columns explicitly"),
        (r"innerHTML\s*=", f"innerHTML assignment in {rel} — XSS risk"),
        (r"dangerouslySetInnerHTML", f"dangerouslySetInnerHTML in {rel} — XSS risk if unescaped"),
    ]
    for pattern, msg in checks:
        if re.search(pattern, content, re.IGNORECASE):
            if msg not in issues:
                issues.append(msg)


def _detect_performance(content: str, rel: str, issues: List[str]) -> None:
    checks = [
        (r"for\s+\w+\s+in\s+range\s*\(len\(", f"Anti-pattern: for i in range(len()) in {rel} — use enumerate()"),
        (r"\+\s*=\s*['\"]", f"String concatenation in loop detected in {rel} — use join() or builder"),
        (r"SELECT.*WHERE.*LIKE\s+['\"]%", f"Leading wildcard LIKE query in {rel} — performance issue"),
        (r"time\.sleep\(\d+\)", f"Blocking sleep() in {rel} — use async alternatives"),
        (r"\.all\(\).*for.*in", f"Potential N+1 query pattern in {rel}"),
    ]
    for pattern, msg in checks:
        if re.search(pattern, content, re.IGNORECASE):
            if msg not in issues:
                issues.append(msg)


def _analyze_python(content: str, rel: str) -> List[str]:
    issues = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = (node.end_lineno or 0) - node.lineno
                if func_lines > MAX_FUNCTION_LINES:
                    issues.append(f"Long function '{node.name}' ({func_lines} lines) in {rel} — consider splitting")
                # Check for missing return type hints
                if not node.returns and node.name not in ("__init__", "__str__", "__repr__"):
                    pass  # Too noisy to report every missing hint
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    if handler.type is None:
                        issues.append(f"Bare except clause in {rel} — catch specific exceptions")
    except SyntaxError:
        issues.append(f"Python syntax error in {rel}")
    except Exception:
        pass
    return issues


def _detect_quality_issues(content: str, rel: str, issues: List[str], line_count: int) -> None:
    # TODO comments indicate incomplete work
    todo_count = len(re.findall(r"\bTODO\b|\bFIXME\b|\bHACK\b|\bXXX\b", content, re.IGNORECASE))
    if todo_count > 5:
        issues.append(f"High TODO/FIXME count ({todo_count}) in {rel} — unfinished implementation")

    # Duplicate logic detection (simplified)
    if content.count("copy-paste") > 0 or content.count("duplicate") > 0:
        pass  # Placeholder for semantic duplicate detection

    # Console.log in production code
    if "console.log(" in content and "test" not in rel.lower() and "debug" not in rel.lower():
        issues.append(f"console.log() found in {rel} — remove before production")
