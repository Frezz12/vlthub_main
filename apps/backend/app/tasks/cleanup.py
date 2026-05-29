import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


def clean_temp_files_task(paths: list[str]) -> None:
    for p in paths:
        path = Path(p)
        if path.exists():
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
            else:
                path.unlink()
            logger.info("Cleaned %s", p)


def clean_old_uploads_task(max_age_days: int = 30) -> int:
    import time
    cutoff = time.time() - max_age_days * 86400
    count = 0
    upload_dir = Path(settings.upload_dir)
    if not upload_dir.exists():
        return 0
    for f in upload_dir.rglob("*"):
        if f.is_file() and f.stat().st_mtime < cutoff:
            f.unlink()
            count += 1
    logger.info("Cleaned %d old files", count)
    return count
