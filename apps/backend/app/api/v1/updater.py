from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["updater"])


@router.get("/updater/check")
async def check_update():
    ver = settings.app_version
    base = settings.app_base_url

    platforms: dict[str, dict[str, str]] = {}

    if settings.app_update_sig_windows:
        platforms["windows-x86_64"] = {
            "signature": settings.app_update_sig_windows,
            "url": f"{base}/downloads/VLTHub_{ver}_x64_en-US.msi",
        }
        platforms["windows-x86_64-msi"] = {
            "signature": settings.app_update_sig_windows,
            "url": f"{base}/downloads/VLTHub_{ver}_x64_en-US.msi",
        }
        platforms["windows-x86_64-nsis"] = {
            "signature": settings.app_update_sig_windows,
            "url": f"{base}/downloads/VLTHub_{ver}_x64-setup.exe",
        }

    if settings.app_update_sig_macos_x86_64:
        platforms["darwin-x86_64"] = {
            "signature": settings.app_update_sig_macos_x86_64,
            "url": f"{base}/downloads/VLTHub_{ver}_x64.app.tar.gz",
        }
        platforms["darwin-x86_64-app"] = {
            "signature": settings.app_update_sig_macos_x86_64,
            "url": f"{base}/downloads/VLTHub_{ver}_x64.app.tar.gz",
        }

    if settings.app_update_sig_macos_aarch64:
        platforms["darwin-aarch64"] = {
            "signature": settings.app_update_sig_macos_aarch64,
            "url": f"{base}/downloads/VLTHub_{ver}_aarch64.app.tar.gz",
        }
        platforms["darwin-aarch64-app"] = {
            "signature": settings.app_update_sig_macos_aarch64,
            "url": f"{base}/downloads/VLTHub_{ver}_aarch64.app.tar.gz",
        }

    if settings.app_update_sig_linux_x86_64:
        platforms["linux-x86_64"] = {
            "signature": settings.app_update_sig_linux_x86_64,
            "url": f"{base}/downloads/VLTHub_{ver}_amd64.AppImage",
        }
        platforms["linux-x86_64-appimage"] = {
            "signature": settings.app_update_sig_linux_x86_64,
            "url": f"{base}/downloads/VLTHub_{ver}_amd64.AppImage",
        }
        platforms["linux-x86_64-deb"] = {
            "signature": settings.app_update_sig_linux_x86_64,
            "url": f"{base}/downloads/VLTHub_{ver}_amd64.deb",
        }

    return {
        "version": ver,
        "notes": "Улучшения производительности и исправления ошибок",
        "pub_date": settings.app_update_pub_date,
        "platforms": platforms,
    }
