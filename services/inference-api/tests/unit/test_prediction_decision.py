# services/inference-api/tests/unit/test_prediction_decision.py
# Kiem tra luat quyet dinh theo nguong confidence: dat nguong moi chap nhan, khong thi "Khong nhan dien duoc" (T044).
import pytest
from visign_api.domain.prediction import REJECTED_PREDICTION_TEXT
from visign_api.inference.prediction_decision import (
    PredictionDecision,
    decide_prediction,
)
from visign_api.inference.predictor import RawPrediction

ACCEPTANCE_THRESHOLD = 0.70


def build_raw_prediction(confidence: float) -> RawPrediction:
    return RawPrediction(
        classLabel="CAM_ON_HN_1",
        displayText="Cảm ơn",
        confidence=confidence,
        timingsMs=None,
        qualityHints=None,
    )


@pytest.mark.parametrize("confidence", [0.70, 0.85, 1.0])
def test_confidence_at_or_above_threshold_is_accepted(confidence: float) -> None:
    decision = decide_prediction(build_raw_prediction(confidence), ACCEPTANCE_THRESHOLD)

    assert decision == PredictionDecision(
        accepted=True, text="Cảm ơn", classLabel="CAM_ON_HN_1"
    )


@pytest.mark.parametrize("confidence", [0.0, 0.42, 0.6999])
def test_confidence_below_threshold_is_rejected_without_class(
    confidence: float,
) -> None:
    # Hien phap I: khong ep chon mot tu khi model khong du chac chan
    decision = decide_prediction(build_raw_prediction(confidence), ACCEPTANCE_THRESHOLD)

    assert decision == PredictionDecision(
        accepted=False, text=REJECTED_PREDICTION_TEXT, classLabel=None
    )


def test_zero_threshold_still_requires_display_text() -> None:
    blank_text_prediction = RawPrediction(
        classLabel="CAM_ON_HN_1",
        displayText="   ",
        confidence=0.99,
        timingsMs=None,
        qualityHints=None,
    )

    decision = decide_prediction(blank_text_prediction, 0.0)

    assert decision.accepted is False
    assert decision.text == REJECTED_PREDICTION_TEXT
