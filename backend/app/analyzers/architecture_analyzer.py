from typing import Dict, Any, List


ARCH_PATTERNS = {
    "monolith": {
        "keywords": ["all-in-one", "single process"],
        "indicators": lambda d: (
            not d.get("has_docker") and
            len(d.get("frameworks", [])) <= 2 and
            not _has_microservices(d)
        ),
    },
    "microservices": {
        "indicators": lambda d: _has_microservices(d),
    },
    "fullstack_web": {
        "indicators": lambda d: (
            any(f in d.get("frameworks", []) for f in ["React", "Vue.js", "Next.js", "Svelte", "Angular"]) and
            any(f in d.get("frameworks", []) for f in ["FastAPI", "Django", "Flask", "Express.js", "Next.js"])
        ),
    },
    "api_only": {
        "indicators": lambda d: (
            any(f in d.get("frameworks", []) for f in ["FastAPI", "Django", "Flask", "Express.js"]) and
            not any(f in d.get("frameworks", []) for f in ["React", "Vue.js", "Next.js"])
        ),
    },
    "frontend_only": {
        "indicators": lambda d: (
            any(f in d.get("frameworks", []) for f in ["React", "Vue.js", "Next.js", "Svelte"]) and
            not any(f in d.get("frameworks", []) for f in ["FastAPI", "Django", "Flask", "Express.js"])
        ),
    },
    "data_pipeline": {
        "indicators": lambda d: any(f in d.get("frameworks", []) for f in ["Celery", "Dramatiq"]),
    },
    "serverless": {
        "indicators": lambda d: any(c in d.get("cloud", []) for c in ["AWS", "GCP", "Azure"]),
    },
}


def _has_microservices(deps: Dict) -> bool:
    return (
        deps.get("has_docker") and
        any("service" in str(deps).lower() for _ in [1])
    )


def analyze_architecture(
    structure: Dict[str, Any],
    dependencies: Dict[str, Any],
) -> Dict[str, Any]:
    arch_type = _detect_architecture_type(dependencies)
    quality_score = _compute_architecture_score(structure, dependencies)
    summary = _generate_summary(arch_type, dependencies, structure)
    recommendations = _generate_recommendations(arch_type, dependencies, structure)

    return {
        "type": arch_type,
        "quality_score": quality_score,
        "summary": summary,
        "recommendations": recommendations,
        "separation_of_concerns": _check_separation(structure),
        "scalability_indicators": _check_scalability(dependencies),
        "deployment_readiness": _check_deployment(dependencies),
    }


def _detect_architecture_type(deps: Dict) -> str:
    for arch, config in ARCH_PATTERNS.items():
        if config.get("indicators") and config["indicators"](deps):
            return arch
    return "custom"


def _compute_architecture_score(structure: Dict, deps: Dict) -> float:
    score = 50.0

    if deps.get("has_docker"):
        score += 10
    if deps.get("has_ci"):
        score += 10
    if deps.get("has_tests"):
        score += 15

    frameworks = deps.get("frameworks", [])
    if len(frameworks) >= 2:
        score += 5
    if len(frameworks) >= 4:
        score += 5

    dbs = deps.get("databases", [])
    if dbs:
        score += 5

    # Penalize missing essentials
    if not deps.get("has_tests"):
        score -= 10
    if not deps.get("has_ci"):
        score -= 5

    file_count = structure.get("file_count", 0)
    if file_count > 10:
        score += 5

    return min(max(round(score, 1), 0), 100)


def _generate_summary(arch_type: str, deps: Dict, structure: Dict) -> str:
    frameworks = deps.get("frameworks", [])
    databases = deps.get("databases", [])
    languages = structure.get("languages", [])

    parts = []
    if languages:
        parts.append(f"Primary language: {languages[0]}")
    if frameworks:
        parts.append(f"Frameworks: {', '.join(frameworks[:5])}")
    if databases:
        parts.append(f"Databases: {', '.join(databases)}")

    arch_descriptions = {
        "fullstack_web": "Full-stack web application with separate frontend and backend layers",
        "api_only": "Backend API service — consider adding a frontend or client SDK",
        "frontend_only": "Frontend-only application — consider adding a backend API",
        "microservices": "Microservices architecture with containerized services",
        "monolith": "Monolithic application — consider modular decomposition at scale",
        "data_pipeline": "Data processing pipeline with async task execution",
        "serverless": "Cloud-native serverless architecture",
        "custom": "Custom architecture pattern detected",
    }

    desc = arch_descriptions.get(arch_type, "Unknown architecture")
    if parts:
        return f"{desc}. {'. '.join(parts)}."
    return desc


def _generate_recommendations(arch_type: str, deps: Dict, structure: Dict) -> List[str]:
    recs = []

    if not deps.get("has_tests"):
        recs.append("Add test suite — no tests detected (target >70% coverage)")
    if not deps.get("has_docker"):
        recs.append("Containerize with Docker for consistent deployment")
    if not deps.get("has_ci"):
        recs.append("Set up CI/CD pipeline (GitHub Actions recommended)")
    if not deps.get("databases"):
        recs.append("Consider adding a persistent database for production use")

    if arch_type == "monolith" and structure.get("file_count", 0) > 50:
        recs.append("Large monolith detected — consider extracting services as it grows")
    if arch_type == "api_only":
        recs.append("API-only project — add API documentation (OpenAPI/Swagger)")
    if arch_type == "fullstack_web":
        recs.append("Implement environment-based configuration (dev/staging/prod)")

    return recs[:8]


def _check_separation(structure: Dict) -> Dict[str, bool]:
    tree_paths = [item.get("path", "") for item in structure.get("folder_tree", [])]
    paths_str = " ".join(tree_paths).lower()

    return {
        "has_frontend_dir": any(d in paths_str for d in ["frontend", "client", "src/pages", "src/components"]),
        "has_backend_dir": any(d in paths_str for d in ["backend", "api", "server", "app"]),
        "has_tests_dir": any(d in paths_str for d in ["tests", "test", "__tests__", "spec"]),
        "has_config_dir": any(d in paths_str for d in ["config", ".env", "settings"]),
    }


def _check_scalability(deps: Dict) -> List[str]:
    indicators = []
    if deps.get("has_docker"):
        indicators.append("Containerized — horizontally scalable")
    if "Redis" in deps.get("databases", []):
        indicators.append("Redis detected — caching/queue ready")
    if deps.get("cloud"):
        indicators.append(f"Cloud ready: {', '.join(deps['cloud'])}")
    if not indicators:
        indicators.append("No explicit scalability infrastructure detected")
    return indicators


def _check_deployment(deps: Dict) -> Dict[str, Any]:
    return {
        "has_docker": deps.get("has_docker", False),
        "has_ci_cd": deps.get("has_ci", False),
        "cloud_providers": deps.get("cloud", []),
        "devops_tools": deps.get("devops", []),
        "ready": deps.get("has_docker", False) or bool(deps.get("cloud")),
    }
