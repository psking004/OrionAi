from typing import Dict, Any, List, Optional
import requests


GITHUB_API = "https://api.github.com"
TIMEOUT = 15


def _headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get(url: str, token: str, params: Optional[Dict] = None) -> Optional[Any]:
    try:
        r = requests.get(url, headers=_headers(token), params=params or {}, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def validate_token(token: str) -> Dict[str, Any]:
    result = _get(f"{GITHUB_API}/user", token)
    if result:
        return {"valid": True, "login": result.get("login", ""), "name": result.get("name", "")}
    return {"valid": False, "login": "", "name": ""}


def fetch_repo_info(token: str, owner: str, repo: str) -> Optional[Dict[str, Any]]:
    data = _get(f"{GITHUB_API}/repos/{owner}/{repo}", token)
    if not data:
        return None
    return {
        "full_name": data.get("full_name", ""),
        "description": data.get("description", ""),
        "html_url": data.get("html_url", ""),
        "default_branch": data.get("default_branch", "main"),
        "language": data.get("language", ""),
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "size": data.get("size", 0),
        "private": data.get("private", False),
        "created_at": data.get("created_at", ""),
        "updated_at": data.get("updated_at", ""),
        "pushed_at": data.get("pushed_at", ""),
        "topics": data.get("topics", []),
    }


def fetch_commits(token: str, owner: str, repo: str, branch: str = "main", per_page: int = 50) -> List[Dict]:
    data = _get(
        f"{GITHUB_API}/repos/{owner}/{repo}/commits",
        token,
        {"sha": branch, "per_page": per_page},
    )
    if not data:
        return []

    commits = []
    for c in data:
        commit_info = c.get("commit", {})
        commits.append({
            "sha": c.get("sha", "")[:8],
            "message": commit_info.get("message", "").split("\n")[0][:120],
            "author": commit_info.get("author", {}).get("name", "unknown"),
            "date": commit_info.get("author", {}).get("date", ""),
            "url": c.get("html_url", ""),
        })
    return commits


def fetch_contributors(token: str, owner: str, repo: str) -> List[Dict]:
    data = _get(f"{GITHUB_API}/repos/{owner}/{repo}/contributors", token, {"per_page": 20})
    if not data:
        return []
    return [
        {"login": c.get("login", ""), "contributions": c.get("contributions", 0)}
        for c in data
    ]


def fetch_branches(token: str, owner: str, repo: str) -> List[str]:
    data = _get(f"{GITHUB_API}/repos/{owner}/{repo}/branches", token, {"per_page": 30})
    if not data:
        return []
    return [b.get("name", "") for b in data]


def fetch_repo_tree(token: str, owner: str, repo: str, branch: str = "main") -> List[Dict]:
    data = _get(
        f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}",
        token,
        {"recursive": "1"},
    )
    if not data:
        return []
    tree = data.get("tree", [])
    return [
        {"path": item.get("path", ""), "type": item.get("type", ""), "size": item.get("size", 0)}
        for item in tree
        if item.get("type") in ("blob", "tree")
    ][:500]


def fetch_languages(token: str, owner: str, repo: str) -> Dict[str, int]:
    data = _get(f"{GITHUB_API}/repos/{owner}/{repo}/languages", token)
    return data or {}


def fetch_pull_requests(token: str, owner: str, repo: str, state: str = "open") -> List[Dict]:
    data = _get(
        f"{GITHUB_API}/repos/{owner}/{repo}/pulls",
        token,
        {"state": state, "per_page": 20},
    )
    if not data:
        return []
    return [
        {
            "number": pr.get("number"),
            "title": pr.get("title", ""),
            "state": pr.get("state", ""),
            "created_at": pr.get("created_at", ""),
            "user": pr.get("user", {}).get("login", ""),
        }
        for pr in data
    ]
