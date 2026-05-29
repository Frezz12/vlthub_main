import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def convert_to_mp3(input_path: str, output_path: str, bitrate: str = "192k") -> bool:
    try:
        subprocess.run(
            ["ffmpeg", "-i", input_path, "-b:a", bitrate, output_path, "-y"],
            check=True, capture_output=True,
        )
        logger.info("Converted %s to %s", input_path, output_path)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("FFmpeg conversion failed: %s", e.stderr.decode())
        return False
    except FileNotFoundError:
        logger.error("FFmpeg not found")
        return False


def get_audio_duration(file_path: str) -> float | None:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            check=True, capture_output=True, text=True,
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return None
