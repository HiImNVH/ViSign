# services/inference-api/tests/unit/test_prediction_response.py
# Chung minh trang thai accepted/rejected cua prediction khong the ket hop sai (T020).
import json
import uuid
from typing import Any

import pytest
from pydantic import ValidationError
from visign_api.domain.prediction import PredictionResponse

REJECTED_TEXT = "Không nhận diện được"


def build_response(**overrides: Any) -> PredictionResponse:
    accepted_fields: dict[str, Any] = {
        "requestId": str(uuid.uuid4()),
        "text": "Xin chào",
        "classLabel": "XIN_CHAO_HCM_1",
        "confidence": 0.9,
        "accepted": True,
        "modelVersion": "vsl-fixture-v0.0.1",
        "processingTimeMs": 10,
    }
    accepted_fields.update(overrides)
    return PredictionResponse(**accepted_fields)


def build_rejected_response(**overrides: Any) -> PredictionResponse:
    rejected_fields: dict[str, Any] = {
        "accepted": False,
        "text": REJECTED_TEXT,
        "classLabel": None,
        "confidence": 0.3,
    }
    rejected_fields.update(overrides)
    return build_response(**rejected_fields)


def test_accepted_response_without_diagnostics_is_valid() -> None:
    accepted_response = build_response()

    assert accepted_response.accepted is True
    assert accepted_response.timingsMs is None
    assert accepted_response.qualityHints is None


def test_rejected_response_has_null_class_label() -> None:
    assert build_rejected_response().classLabel is None


def test_absent_diagnostics_are_omitted_but_null_class_label_is_kept() -> None:
    # openapi.yaml: timingsMs/qualityHints optional nhung khong nullable; classLabel bat buoc va nullable
    serialized_response = json.loads(build_rejected_response().model_dump_json())

    assert "timingsMs" not in serialized_response
    assert "qualityHints" not in serialized_response
    assert serialized_response["classLabel"] is None


def test_present_diagnostics_are_serialized() -> None:
    diagnosed_response = build_response(
        timingsMs={"decode": 1, "extract": 2, "infer": 3},
        qualityHints={"handsDetectedRatio": 0.5, "frameCount": 10},
    )

    serialized_response = diagnosed_response.model_dump(mode="json")

    assert serialized_response["timingsMs"] == {"decode": 1, "extract": 2, "infer": 3}
    assert serialized_response["qualityHints"] == {
        "handsDetectedRatio": 0.5,
        "frameCount": 10,
    }


@pytest.mark.parametrize(
    "invalid_overrides",
    [
        {"requestId": "not-a-uuid"},
        {"text": "   "},
        {"classLabel": None},
        {"classLabel": ""},
        {"accepted": False, "text": REJECTED_TEXT, "classLabel": "XIN_CHAO_HCM_1"},
        {"confidence": 1.2},
        {"processingTimeMs": -1},
        {"timingsMs": {"decode": -1, "extract": 0, "infer": 0}},
        {"qualityHints": {"handsDetectedRatio": 1.5, "frameCount": 10}},
        {"qualityHints": {"handsDetectedRatio": 0.5, "frameCount": 0}},
        {
            "qualityHints": {
                "handsDetectedRatio": 0.5,
                "frameCount": 10,
                "landmarks": [[0.1, 0.2]],
            }
        },
    ],
)
def test_invalid_state_combinations_are_rejected(
    invalid_overrides: dict[str, Any],
) -> None:
    with pytest.raises(ValidationError):
        build_response(**invalid_overrides)
