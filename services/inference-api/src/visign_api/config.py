# services/inference-api/src/visign_api/config.py
# Cau hinh runtime: artifact path, MIME allowlist, gioi han clip, timeout cho slot suy luan va CORS (T022).
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Gia tri mac dinh theo docs/team/fe-be-api-convention.md muc 3 va ai-backend-contract.md
DEFAULT_MAX_CLIP_BYTES = 10 * 1024 * 1024
DEFAULT_MIN_DURATION_MS = 300
DEFAULT_MAX_DURATION_MS = 6000
# Thoi gian doi slot suy luan, khong phai thoi gian xu ly toan luong
DEFAULT_INFERENCE_WAIT_TIMEOUT_SECONDS = 3.0
WILDCARD_ORIGIN = "*"
# Cong cu admin noi bo (T079): token ngan de doan nen bi tu choi; inspect mot clip 6 s mat vai giay
MIN_ADMIN_TOKEN_LENGTH = 16
DEFAULT_ADMIN_INSPECT_TIMEOUT_SECONDS = 60.0

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
    # hide_input_in_errors: loi cau hinh (vd token qua ngan) khong in lai gia tri vao log khoi dong
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
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
    # Kieu Literal[False]: cau hinh True (code hoac env) lam app dung luc khoi dong thay vi bat credential
    cors_allow_credentials: Literal[False] = False
    # Nguon dac trung khi chua co artifact (parity, smoke); None de visign_ai dung mac dinh cua no.
    # Artifact pilot/full mang schema rieng va duoc kiem o predictor (T037)
    feature_schema_version: str | None = None
    feature_schema_path: Path | None = None
    visign_model_dir: Path | None = None
    # Swagger/ReDoc/openapi.json chi bat khi dev local (API_DOCS_ENABLED=true); production tat de khong lo
    # be mat API thua (T092). Contract chinh thuc nam o specs/.../contracts/openapi.yaml
    api_docs_enabled: bool = False
    # Tao san bo detector MediaPipe o thread nen cho request ke tiep (T065, SC-002); tat bang
    # DETECTOR_PREWARM_ENABLED=false de quay ve tao detector theo tung clip ma khong can doi code
    detector_prewarm_enabled: bool = True
    # Cong cu admin noi bo (T079, FR-021, contracts/admin-tools.md): chi bat khi co VISIGN_ADMIN_TOKEN; token
    # khong duoc commit, log hay tra ve. Workspace local luu trang thai/lich su pilot; None thi pilot tra 503
    visign_admin_token: SecretStr | None = None
    visign_admin_workspace: Path | None = None
    admin_inspect_timeout_seconds: float = Field(
        DEFAULT_ADMIN_INSPECT_TIMEOUT_SECONDS, gt=0
    )

    @field_validator("visign_admin_token", mode="before")
    @classmethod
    def treat_blank_admin_token_as_disabled(cls, admin_token: object) -> object:
        if isinstance(admin_token, str) and not admin_token.strip():
            return None
        return admin_token

    @field_validator("visign_admin_token")
    @classmethod
    def require_strong_admin_token(
        cls, admin_token: SecretStr | None
    ) -> SecretStr | None:
        if (
            admin_token is not None
            and len(admin_token.get_secret_value()) < MIN_ADMIN_TOKEN_LENGTH
        ):
            raise ValueError(
                f"VISIGN_ADMIN_TOKEN phai dai it nhat {MIN_ADMIN_TOKEN_LENGTH} ky tu"
            )
        return admin_token

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
