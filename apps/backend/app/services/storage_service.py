import os
from pathlib import Path

from app.core.config import settings
from app.core.storage import calculate_sha256


def get_version_storage_path(project_id: str, version_id: str) -> Path:
    path = Path(settings.upload_dir) / project_id / version_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_preview_storage_path(project_id: str, version_id: str) -> Path:
    path = Path(settings.upload_dir) / project_id / version_id / "previews"
    path.mkdir(parents=True, exist_ok=True)
    return path


def verify_file_hash(file_path: str, expected_hash: str) -> bool:
    actual = calculate_sha256(file_path)
    return actual == expected_hash
