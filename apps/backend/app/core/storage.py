import hashlib
import os
import shutil
from pathlib import Path

from app.core.config import settings


def get_upload_path() -> Path:
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def calculate_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def archive_to_zip(source_dir: str, dest_path: str) -> str:
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.make_archive(str(dest.with_suffix("")), "zip", source_dir)
    return str(dest)


def extract_zip(archive_path: str, dest_dir: str) -> None:
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(archive_path, dest_dir, "zip")


def clean_temp_files(paths: list[str]) -> None:
    for p in paths:
        path = Path(p)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)
