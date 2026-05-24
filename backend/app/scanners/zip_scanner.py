import os
import zipfile
import tempfile
import shutil
from typing import Dict, Any, Optional


MAX_ZIP_SIZE = 100 * 1024 * 1024  # 100MB
MAX_UNZIPPED_SIZE = 300 * 1024 * 1024  # 300MB
MAX_FILES_IN_ZIP = 2000
BLOCKED_EXTENSIONS = {".exe", ".dll", ".so", ".dylib", ".bat", ".cmd", ".sh"}

IGNORED_DIRS = {
    "node_modules", "venv", ".venv", "build", "dist", "__pycache__",
    ".git", ".gradle", "target", "vendor",
}


def safe_extract_zip(zip_path: str, extract_to: Optional[str] = None) -> Dict[str, Any]:
    if extract_to is None:
        extract_to = tempfile.mkdtemp(prefix="ai_teammate_upload_")

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = zf.infolist()

            if len(members) > MAX_FILES_IN_ZIP:
                return {
                    "success": False,
                    "error": f"ZIP contains too many files ({len(members)}). Max: {MAX_FILES_IN_ZIP}",
                    "extract_path": None,
                }

            total_unzipped = sum(m.file_size for m in members)
            if total_unzipped > MAX_UNZIPPED_SIZE:
                return {
                    "success": False,
                    "error": f"Unzipped size ({total_unzipped // 1024 // 1024}MB) exceeds limit (300MB)",
                    "extract_path": None,
                }

            for member in members:
                member_path = os.path.realpath(os.path.join(extract_to, member.filename))
                if not member_path.startswith(os.path.realpath(extract_to) + os.sep):
                    return {
                        "success": False,
                        "error": "ZIP contains path traversal attack — rejected",
                        "extract_path": None,
                    }

                ext = os.path.splitext(member.filename)[1].lower()
                if ext in BLOCKED_EXTENSIONS:
                    continue

            for member in members:
                parts = member.filename.replace("\\", "/").split("/")
                if any(p in IGNORED_DIRS for p in parts):
                    continue
                ext = os.path.splitext(member.filename)[1].lower()
                if ext in BLOCKED_EXTENSIONS:
                    continue
                try:
                    zf.extract(member, extract_to)
                except Exception:
                    continue

        return {
            "success": True,
            "error": None,
            "extract_path": extract_to,
            "file_count": len(members),
        }
    except zipfile.BadZipFile:
        return {"success": False, "error": "Invalid or corrupted ZIP file", "extract_path": None}
    except Exception as e:
        return {"success": False, "error": str(e), "extract_path": None}


def cleanup_extract(path: str) -> None:
    try:
        if path and os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


def get_project_root(extract_path: str) -> str:
    entries = os.listdir(extract_path)
    visible = [e for e in entries if not e.startswith(".")]
    if len(visible) == 1:
        candidate = os.path.join(extract_path, visible[0])
        if os.path.isdir(candidate):
            return candidate
    return extract_path
