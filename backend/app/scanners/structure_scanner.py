import os
from typing import List, Dict, Any

IGNORED_DIRS = {
    "node_modules", "venv", ".venv", "env", ".env", "build", "dist",
    ".git", "__pycache__", ".pytest_cache", "coverage", ".nyc_output",
    "target", ".gradle", "vendor", "cache", ".cache", "tmp", "temp",
}
IGNORED_EXTENSIONS = {
    ".pyc", ".pyo", ".class", ".jar", ".war", ".lock", ".log",
    ".DS_Store", ".map",
}
MAX_TREE_DEPTH = 6
MAX_FILES = 500


def scan_structure(root_path: str) -> Dict[str, Any]:
    tree = []
    file_count = 0
    dir_count = 0
    languages: Dict[str, int] = {}
    total_size = 0

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]

        rel_dir = os.path.relpath(dirpath, root_path)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
        if depth > MAX_TREE_DEPTH:
            dirnames.clear()
            continue

        if rel_dir != ".":
            dir_count += 1
            tree.append({"path": rel_dir.replace(os.sep, "/"), "type": "directory"})

        for fname in filenames:
            if file_count >= MAX_FILES:
                break
            ext = os.path.splitext(fname)[1].lower()
            if ext in IGNORED_EXTENSIONS:
                continue

            full_path = os.path.join(dirpath, fname)
            try:
                size = os.path.getsize(full_path)
            except OSError:
                size = 0

            rel_path = os.path.relpath(full_path, root_path).replace(os.sep, "/")
            tree.append({"path": rel_path, "type": "file", "size": size})
            total_size += size
            file_count += 1

            lang = _ext_to_language(ext)
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

    sorted_langs = sorted(languages.keys(), key=lambda l: languages[l], reverse=True)

    return {
        "folder_tree": tree,
        "file_count": file_count,
        "dir_count": dir_count,
        "languages": sorted_langs,
        "language_breakdown": languages,
        "total_size_bytes": total_size,
    }


def _ext_to_language(ext: str) -> str:
    mapping = {
        ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
        ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java",
        ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
        ".cs": "C#", ".cpp": "C++", ".c": "C", ".swift": "Swift",
        ".kt": "Kotlin", ".scala": "Scala", ".html": "HTML",
        ".css": "CSS", ".scss": "SCSS", ".less": "LESS",
        ".sql": "SQL", ".sh": "Shell", ".bash": "Shell",
        ".yaml": "YAML", ".yml": "YAML", ".json": "JSON",
        ".toml": "TOML", ".xml": "XML", ".md": "Markdown",
        ".tf": "Terraform", ".dockerfile": "Docker",
    }
    if ext == "" and "Dockerfile" in ext:
        return "Docker"
    return mapping.get(ext, "")
