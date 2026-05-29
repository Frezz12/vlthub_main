from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["updater"])


@router.get("/updater/check")
async def check_update():
    return {
        "version": settings.app_version,
        "notes": "Улучшения производительности и исправления ошибок",
        "pub_date": settings.app_update_pub_date,
        "platforms": {
            "windows-x86_64": {
                "signature": settings.app_update_sig_windows,
                "url": f"{settings.app_base_url}/downloads/VLTHub_{settings.app_version}_x64_en-US.msi",
            },
        },
    }
