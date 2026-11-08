# services/inference-api/src/visign_api/inference/artifact_loader.py
# Nap model_info.json cua artifact fixture/pilot/full va tu choi goi khong the phuc vu an toan (T037).
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from visign_api.domain.model_version import ArtifactKind, ModelMetadata

MODEL_INFO_FILE = "model_info.json"
PILOT_MAX_MEANINGS = 3
FULL_MEANING_COUNT = 10


class ArtifactRejectedError(ValueError):
    # Ly do chi tiet chi vao log server; client chi nhan MODEL_NOT_READY
    pass


@dataclass(frozen=True)
class FixtureResponse:
    classLabel: str | None
    confidence: float | None


@dataclass(frozen=True)
class LoadedArtifact:
    directory: Path
    metadata: ModelMetadata
    displayTextMap: dict[str, str]
    fixtureResponse: FixtureResponse | None


def load_artifact(
    artifact_directory: Path, expected_schema_version: str | None
) -> LoadedArtifact:
    model_info = read_model_info(artifact_directory)
    display_text_map = parse_display_text_map(model_info.pop("displayTextMap", {}))
    fixture_response = parse_fixture_response(model_info.pop("fixtureResponse", None))
    loaded_artifact = LoadedArtifact(
        directory=artifact_directory,
        # Giu chu hien thi trong metadata de /model-info tra meaningDisplayTexts (T109)
        metadata=parse_metadata({**model_info, "displayTextMap": display_text_map}),
        displayTextMap=display_text_map,
        fixtureResponse=fixture_response,
    )
    validate_artifact(loaded_artifact, expected_schema_version)
    return loaded_artifact


def read_model_info(artifact_directory: Path) -> dict[str, Any]:
    try:
        model_info = json.loads(
            (artifact_directory / MODEL_INFO_FILE).read_text(encoding="utf-8-sig")
        )
    except (OSError, ValueError) as read_error:
        raise ArtifactRejectedError(
            f"Khong doc duoc {MODEL_INFO_FILE} tai {artifact_directory}"
        ) from read_error
    if not isinstance(model_info, dict):
        raise ArtifactRejectedError(f"{MODEL_INFO_FILE} phai la mot object JSON")
    return model_info


def parse_display_text_map(raw_display_text_map: Any) -> dict[str, str]:
    if not isinstance(raw_display_text_map, dict) or not all(
        isinstance(display_text, str) for display_text in raw_display_text_map.values()
    ):
        raise ArtifactRejectedError(
            "displayTextMap phai anh xa meaningId sang chu hien thi"
        )
    return dict(raw_display_text_map)


def parse_fixture_response(raw_fixture_response: Any) -> FixtureResponse | None:
    if raw_fixture_response is None:
        return None
    if not isinstance(raw_fixture_response, dict):
        raise ArtifactRejectedError("fixtureResponse phai la mot object JSON")
    raw_confidence = raw_fixture_response.get("confidence")
    try:
        confidence = None if raw_confidence is None else float(raw_confidence)
    except (TypeError, ValueError) as invalid_confidence:
        raise ArtifactRejectedError(
            "fixtureResponse.confidence phai la so"
        ) from invalid_confidence
    return FixtureResponse(
        classLabel=raw_fixture_response.get("classLabel"), confidence=confidence
    )


def parse_metadata(model_info: dict[str, Any]) -> ModelMetadata:
    try:
        return ModelMetadata(**model_info)
    except ValidationError as invalid_metadata:
        raise ArtifactRejectedError(
            f"{MODEL_INFO_FILE} khong dung schema ModelMetadata"
        ) from invalid_metadata


def validate_artifact(
    loaded_artifact: LoadedArtifact, expected_schema_version: str | None
) -> None:
    validate_schema_version(loaded_artifact.metadata, expected_schema_version)
    validate_label_mapping(loaded_artifact.metadata)
    validate_display_texts(loaded_artifact)
    validate_meaning_count(loaded_artifact.metadata)
    validate_fixture_response(loaded_artifact)


def validate_schema_version(
    metadata: ModelMetadata, expected_schema_version: str | None
) -> None:
    # Schema tensor cua artifact phai trung schema phuc vu, neu khong model nhan dau vao sai thu tu
    if (
        expected_schema_version is not None
        and metadata.featureSchemaVersion != expected_schema_version
    ):
        raise ArtifactRejectedError(
            f"featureSchemaVersion {metadata.featureSchemaVersion} khac schema phuc vu {expected_schema_version}"
        )


def validate_label_mapping(metadata: ModelMetadata) -> None:
    if len(set(metadata.meanings)) != len(metadata.meanings):
        raise ArtifactRejectedError("meanings bi trung")
    if not metadata.classLabels or len(set(metadata.classLabels)) != len(
        metadata.classLabels
    ):
        raise ArtifactRejectedError("classLabels rong hoac bi trung")
    if set(metadata.meaningMap) != set(metadata.classLabels):
        raise ArtifactRejectedError("Khoa cua meaningMap phai trung khop classLabels")
    if set(metadata.meaningMap.values()) != set(metadata.meanings):
        raise ArtifactRejectedError(
            "Gia tri cua meaningMap phai phu dung meanings da khai bao"
        )


def validate_display_texts(loaded_artifact: LoadedArtifact) -> None:
    missing_text_meanings = [
        meaning
        for meaning in loaded_artifact.metadata.meanings
        if not loaded_artifact.displayTextMap.get(meaning, "").strip()
    ]
    if missing_text_meanings:
        raise ArtifactRejectedError(
            f"Thieu chu hien thi tieng Viet cho {missing_text_meanings}"
        )


def validate_meaning_count(metadata: ModelMetadata) -> None:
    meaning_count = len(metadata.meanings)
    if (
        metadata.artifactKind is ArtifactKind.PILOT
        and meaning_count > PILOT_MAX_MEANINGS
    ):
        raise ArtifactRejectedError(
            f"Pilot chi ho tro toi da {PILOT_MAX_MEANINGS} nghia"
        )
    if (
        metadata.artifactKind is ArtifactKind.FULL
        and meaning_count != FULL_MEANING_COUNT
    ):
        raise ArtifactRejectedError(f"Full phai ho tro dung {FULL_MEANING_COUNT} nghia")


def validate_fixture_response(loaded_artifact: LoadedArtifact) -> None:
    fixture_response = loaded_artifact.fixtureResponse
    if fixture_response is None:
        return
    metadata = loaded_artifact.metadata
    if metadata.artifactKind is not ArtifactKind.FIXTURE:
        raise ArtifactRejectedError("fixtureResponse chi danh cho artifact fixture")
    if (
        fixture_response.classLabel is not None
        and fixture_response.classLabel not in metadata.classLabels
    ):
        raise ArtifactRejectedError(
            "fixtureResponse.classLabel khong nam trong classLabels"
        )
    if (
        fixture_response.confidence is not None
        and not 0.0 <= fixture_response.confidence <= 1.0
    ):
        raise ArtifactRejectedError("fixtureResponse.confidence phai nam trong [0, 1]")
