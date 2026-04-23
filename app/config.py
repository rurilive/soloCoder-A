from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/imgbed.db"
    SECRET_KEY: str = "change-me-in-production-very-strong-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    UPLOAD_DIR: Path = Path("./uploads")
    MAX_FILE_SIZE: int = 100 * 1024 * 1024
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    ]
    ALLOWED_VIDEO_TYPES: List[str] = [
        "video/mp4",
        "video/webm",
        "video/quicktime",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def ALLOWED_MIME_TYPES(self) -> List[str]:
        return self.ALLOWED_IMAGE_TYPES + self.ALLOWED_VIDEO_TYPES


@lru_cache
def get_settings() -> Settings:
    return Settings()
