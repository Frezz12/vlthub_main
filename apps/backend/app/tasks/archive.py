import logging

from app.core.storage import archive_to_zip, extract_zip

logger = logging.getLogger(__name__)


def archive_project_task(source_dir: str, dest_path: str) -> str:
    logger.info("Archiving %s to %s", source_dir, dest_path)
    return archive_to_zip(source_dir, dest_path)


def extract_project_task(archive_path: str, dest_dir: str) -> None:
    logger.info("Extracting %s to %s", archive_path, dest_dir)
    extract_zip(archive_path, dest_dir)
