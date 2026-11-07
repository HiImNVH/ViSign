# services/inference-api/tests/unit/test_config.py
# Kiem tra cau hinh API: gioi han clip, MIME, timeout, CORS va override qua bien moi truong (T022).
from pathlib import Path

import pytest
from pydantic import ValidationError
from visign_api.config import Settings, get_settings

CONTRACT_MAX_CLIP_BYTES = 10_485_760
CONTRACT_MIN_DURATION_MS = 300
CONTRACT_MAX_DURATION_MS = 6000
VITE_DEV_ORIGIN = "http://127.0.0.1:5173"


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Chay trong thu muc rong de khong doc nham file .env cua may dev
    monkeypatch.chdir(tmp_path)
    for variable_name in (
        "MODEL_ARTIFACT_PATH",
        "CORS_ORIGINS",
        "MAX_CLIP_BYTES",
        "MIN_DURATION_MS",
        "MAX_DURATION_MS",
        "INFERENCE_WAIT_TIMEOUT_SECONDS",
        "FEATURE_SCHEMA_VERSION",
        "FEATURE_SCHEMA_PATH",
        "VISIGN_MODEL_DIR",
        "CORS_ALLOW_CREDENTIALS",
    ):
        monkeypatch.delenv(variable_name, raising=False)


def test_feature_source_settings_default_to_pipeline_defaults() -> None:
    # None de pipeline dung schema/detector mac dinh cua visign_ai; artifact pilot/full truyen schema rieng
    default_settings = Settings()

    assert default_settings.feature_schema_version is None
    assert default_settings.feature_schema_path is None
    assert default_settings.visign_model_dir is None


def test_feature_source_settings_are_read_from_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("FEATURE_SCHEMA_VERSION", "visign-xy-32-v0.3-draft")
    monkeypatch.setenv("FEATURE_SCHEMA_PATH", str(tmp_path / "feature_schema.json"))
    monkeypatch.setenv("VISIGN_MODEL_DIR", str(tmp_path / "models"))

    configured_settings = Settings()

    assert configured_settings.feature_schema_version == "visign-xy-32-v0.3-draft"
    assert configured_settings.feature_schema_path == tmp_path / "feature_schema.json"
    assert configured_settings.visign_model_dir == tmp_path / "models"


def test_defaults_match_published_clip_contract() -> None:
    default_settings = Settings()

    assert default_settings.max_clip_bytes == CONTRACT_MAX_CLIP_BYTES
    assert default_settings.min_duration_ms == CONTRACT_MIN_DURATION_MS
    assert default_settings.max_duration_ms == CONTRACT_MAX_DURATION_MS
    assert default_settings.inference_wait_timeout_seconds == 3.0


def test_default_mime_allowlist_accepts_only_webm_vp8_vp9() -> None:
    allowed_mime_types = Settings().allowed_mime_types

    assert "video/webm" in allowed_mime_types
    assert all(mime_type.startswith("video/webm") for mime_type in allowed_mime_types)
    assert not any("mp4" in mime_type for mime_type in allowed_mime_types)


def test_missing_model_artifact_path_means_no_artifact_configured() -> None:
    # Fail closed: khong tu dung fixture khi chua cau hinh artifact
    assert Settings().model_artifact_path is None


def test_model_artifact_path_is_read_from_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MODEL_ARTIFACT_PATH", str(tmp_path / "pilot-v1"))

    assert Settings().model_artifact_path == tmp_path / "pilot-v1"


def test_cors_defaults_to_vite_origins_without_credentials() -> None:
    default_settings = Settings()

    assert VITE_DEV_ORIGIN in default_settings.cors_origins
    assert "*" not in default_settings.cors_origins
    assert default_settings.cors_allow_credentials is False


def test_cors_origins_are_overridden_by_json_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", '["https://visign.example"]')

    assert Settings().cors_origins == ["https://visign.example"]


def test_wildcard_cors_origin_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", '["*"]')

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(
    ("variable_name", "invalid_value"),
    [
        ("MAX_CLIP_BYTES", "0"),
        ("MIN_DURATION_MS", "-1"),
        ("INFERENCE_WAIT_TIMEOUT_SECONDS", "0"),
    ],
)
def test_non_positive_limits_are_rejected(
    monkeypatch: pytest.MonkeyPatch, variable_name: str, invalid_value: str
) -> None:
    monkeypatch.setenv(variable_name, invalid_value)

    with pytest.raises(ValidationError):
        Settings()


def test_minimum_duration_must_be_below_maximum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIN_DURATION_MS", "6000")
    monkeypatch.setenv("MAX_DURATION_MS", "300")

    with pytest.raises(ValidationError):
        Settings()


def test_get_settings_returns_one_cached_instance() -> None:
    get_settings.cache_clear()

    assert get_settings() is get_settings()


def test_credentialed_cors_cannot_be_enabled_in_code() -> None:
    # Quy uoc API muc 6: MVP khong co cookie/dang nhap nen CORS khong bao gio gui credential
    with pytest.raises(ValidationError):
        Settings(cors_allow_credentials=True)


def test_credentialed_cors_cannot_be_enabled_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Cau hinh sai phai lam app dung luc khoi dong thay vi bi bo qua am tham
    monkeypatch.setenv("CORS_ALLOW_CREDENTIALS", "true")

    with pytest.raises(ValidationError):
        Settings()
