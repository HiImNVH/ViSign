# services/inference-api/src/visign_api/config.py
# Cau hinh runtime: artifact path, MIME allowlist, gioi han clip, timeout cho slot suy luan va CORS (T022).
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Gia tri mac dinh theo docs/team/fe-be-api-convention.md muc 3 va ai-backend-contract.md
DEFAULT_MAX_CLIP_BYTES = 10 * 1024 * 1024
DEFAULT_MIN_DURATION_MS = 300
DEFAULT_MAX_DURATION_MS = 6000
# Thoi gian doi slot suy luan, khong phai thoi gian xu ly toan luong
DEFAULT_INFERENCE_WAIT_TIMEOUT_SECONDS = 3.0
WILDCARD_ORIGIN = "*"

DEFAULT_ALLOWED_MIME_TYPES = [
    "video/webm",
    "video/webm;codecs=vp8",
    "video/webm;codecs=vp9",
    "video/webm;codecs=vp8,opus",
    "video/webm;codecs=vp9,opus",
]
VITE_DEV_AND_PREVIEW_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # None nghia la chua cau hinh artifact: service degraded, khong tu dung fixture thay the
    model_artifact_path: Path | None = None
    allowed_mime_types: list[str] = Field(
        default_factory=lambda: list(DEFAULT_ALLOWED_MIME_TYPES)
    )
    max_clip_bytes: int = Field(DEFAULT_MAX_CLIP_BYTES, gt=0)
    min_duration_ms: int = Field(DEFAULT_MIN_DURATION_MS, gt=0)
    max_duration_ms: int = Field(DEFAULT_MAX_DURATION_MS, gt=0)
    inference_wait_timeout_seconds: float = Field(
        DEFAULT_INFERENCE_WAIT_TIMEOUT_SECONDS, gt=0
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: list(VITE_DEV_AND_PREVIEW_ORIGINS)
    )
    # MVP khong co cookie/dang nhap nen khong bao gio gui credential qua CORS
    cors_allow_credentials: bool = False

    @field_validator("cors_origins")
    @classmethod
    def reject_wildcard_origin(cls, cors_origins: list[str]) -> list[str]:
        if WILDCARD_ORIGIN in cors_origins:
            raise ValueError("CORS_ORIGINS phai liet ke origin cu the, khong dung '*'")
        return cors_origins

    @model_validator(mode="after")
    def ensure_duration_window(self) -> "Settings":
        if self.min_duration_ms >= self.max_duration_ms:
            raise ValueError("MIN_DURATION_MS phai nho hon MAX_DURATION_MS")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
