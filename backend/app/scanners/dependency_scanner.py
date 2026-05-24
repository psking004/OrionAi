import json
import os
import re
from typing import Dict, List, Any


def scan_dependencies(root_path: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "python": {},
        "node": {},
        "frameworks": [],
        "databases": [],
        "cloud": [],
        "devops": [],
        "has_docker": False,
        "has_ci": False,
        "has_tests": False,
    }

    # Python requirements
    for fname in ("requirements.txt", "requirements-dev.txt", "Pipfile", "pyproject.toml"):
        fpath = os.path.join(root_path, fname)
        if os.path.isfile(fpath):
            result["python"].update(_parse_python_deps(fpath))

    # Node package.json
    pjson = os.path.join(root_path, "package.json")
    if os.path.isfile(pjson):
        result["node"].update(_parse_node_deps(pjson))

    # Docker
    for dname in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml"):
        if os.path.isfile(os.path.join(root_path, dname)):
            result["has_docker"] = True

    # CI/CD
    if os.path.isdir(os.path.join(root_path, ".github", "workflows")):
        result["has_ci"] = True
    for ci in (".travis.yml", "circle.yml", ".circleci", "Jenkinsfile", ".gitlab-ci.yml"):
        if os.path.exists(os.path.join(root_path, ci)):
            result["has_ci"] = True

    # Tests
    for tdir in ("tests", "test", "__tests__", "spec"):
        if os.path.isdir(os.path.join(root_path, tdir)):
            result["has_tests"] = True

    # Detect frameworks from all deps
    all_deps: List[str] = list(result["python"].keys()) + list(result["node"].keys())
    result["frameworks"] = _detect_frameworks(all_deps)
    result["databases"] = _detect_databases(all_deps, root_path)
    result["cloud"] = _detect_cloud(all_deps, root_path)
    result["devops"] = _detect_devops(all_deps, root_path)

    return result


def _parse_python_deps(path: str) -> Dict[str, str]:
    deps: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                m = re.match(r"^([A-Za-z0-9_\-\.]+)\s*([>=<!~^].+)?", line)
                if m:
                    deps[m.group(1).lower()] = (m.group(2) or "").strip()
    except Exception:
        pass
    return deps


def _parse_node_deps(path: str) -> Dict[str, str]:
    deps: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            deps.update(data.get(section, {}))
    except Exception:
        pass
    return deps


def _detect_frameworks(deps: List[str]) -> List[str]:
    frameworks = []
    mapping = {
        "fastapi": "FastAPI", "django": "Django", "flask": "Flask",
        "starlette": "Starlette", "tornado": "Tornado",
        "react": "React", "react-dom": "React", "next": "Next.js",
        "vue": "Vue.js", "angular": "@angular", "svelte": "Svelte",
        "express": "Express.js", "koa": "Koa", "hapi": "@hapi",
        "spring": "Spring", "rails": "Ruby on Rails",
        "laravel": "Laravel", "gin": "Gin",
        "sqlalchemy": "SQLAlchemy", "prisma": "Prisma",
        "typeorm": "TypeORM", "sequelize": "Sequelize",
        "drizzle-orm": "DrizzleORM",
        "tailwindcss": "Tailwind CSS", "bootstrap": "Bootstrap",
        "vite": "Vite", "webpack": "Webpack",
        "graphql": "GraphQL", "apollo": "Apollo",
        "celery": "Celery", "dramatiq": "Dramatiq",
    }
    seen = set()
    deps_lower = [d.lower() for d in deps]
    for key, name in mapping.items():
        if key in deps_lower and name not in seen:
            frameworks.append(name)
            seen.add(name)
    return frameworks


def _detect_databases(deps: List[str], root: str) -> List[str]:
    db_map = {
        "psycopg2": "PostgreSQL", "psycopg2-binary": "PostgreSQL",
        "asyncpg": "PostgreSQL", "pg": "PostgreSQL",
        "pymongo": "MongoDB", "motor": "MongoDB", "mongoose": "MongoDB",
        "redis": "Redis", "aioredis": "Redis",
        "pymysql": "MySQL", "mysql2": "MySQL",
        "sqlite3": "SQLite",
        "elasticsearch": "Elasticsearch",
        "cassandra-driver": "Cassandra",
        "supabase": "Supabase",
        "firebase-admin": "Firebase",
    }
    found = []
    deps_lower = [d.lower() for d in deps]
    for key, name in db_map.items():
        if key in deps_lower and name not in found:
            found.append(name)
    return found


def _detect_cloud(deps: List[str], root: str) -> List[str]:
    cloud_map = {
        "boto3": "AWS", "botocore": "AWS",
        "google-cloud": "GCP", "@google-cloud": "GCP",
        "@azure": "Azure", "azure": "Azure",
        "heroku": "Heroku", "vercel": "Vercel",
    }
    found = []
    deps_lower = [d.lower() for d in deps]
    for key, name in cloud_map.items():
        if any(key in d for d in deps_lower) and name not in found:
            found.append(name)
    return found


def _detect_devops(deps: List[str], root: str) -> List[str]:
    tools = []
    if os.path.isfile(os.path.join(root, "Dockerfile")):
        tools.append("Docker")
    if os.path.isfile(os.path.join(root, "docker-compose.yml")):
        tools.append("Docker Compose")
    if os.path.isdir(os.path.join(root, ".github", "workflows")):
        tools.append("GitHub Actions")
    if os.path.isfile(os.path.join(root, ".travis.yml")):
        tools.append("Travis CI")
    if os.path.isfile(os.path.join(root, "k8s")) or os.path.isdir(os.path.join(root, "kubernetes")):
        tools.append("Kubernetes")
    deps_lower = [d.lower() for d in deps]
    if "ansible" in deps_lower:
        tools.append("Ansible")
    if "terraform" in deps_lower:
        tools.append("Terraform")
    return tools
