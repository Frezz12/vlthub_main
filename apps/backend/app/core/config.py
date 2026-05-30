from pydantic_settings import BaseSettings
from typing import List



class Settings(BaseSettings):
    app_name: str = "VLTHub"
    app_version:str = "0.6.1"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres@localhost:5433/pjasaver"
    database_url_sync: str = "postgresql+psycopg2://postgres@localhost:5433/pjasaver"

    redis_url: str = "redis://localhost:6379/0"



    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    email_confirmation_token_expire_hours: int = 24
    password_reset_token_expire_hours: int = 1

    upload_dir: str = "uploads"
    download_dir: str = "downloads"
    max_file_size_mb: int = 500
    chunk_size_mb: int = 8

    cors_origins: List[str] = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8000",
            "tauri://localhost",
            "http://tauri.localhost",
            "http://vlthub.ru",
            "https://vlthub.ru",
            "http://77.110.105.238",
        ]

    sentry_dsn: str | None = None

    telegram_bot_token: str = ""
    telegram_bot_username: str = ""

    admin_emails: str = "pantseleevniki@gmail.com"

    app_base_url: str = "https://vlthub.ru"
    app_update_pub_date: str = "2026-05-29T00:00:00Z"

    app_update_sig_windows: str = ""
    app_update_sig_macos_x86_64: str = ""
    app_update_sig_macos_aarch64: str = ""
    app_update_sig_linux_x86_64: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
