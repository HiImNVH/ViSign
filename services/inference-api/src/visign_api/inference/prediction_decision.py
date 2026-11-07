# services/inference-api/src/visign_api/inference/prediction_decision.py
# Luat quyet dinh thuan: chi chap nhan khi confidence dat nguong cua artifact, neu khong tra "Khong nhan dien duoc" (T048).
from dataclasses import dataclass

from visign_api.domain.prediction import REJECTED_PREDICTION_TEXT
from visign_api.inference.predictor import RawPrediction


@dataclass(frozen=True)
class PredictionDecision:
    accepted: bool
    text: str
    classLabel: str | None


def decide_prediction(
    raw_prediction: RawPrediction, acceptance_threshold: float
) -> PredictionDecision:
    # Nguong bao gom: confidence bang dung nguong duoc chap nhan, khop cach tinh nguong tu validation cua P3
    has_display_text = bool(raw_prediction.displayText.strip())
    if raw_prediction.confidence >= acceptance_threshold and has_display_text:
        return PredictionDecision(
            accepted=True,
            text=raw_prediction.displayText,
            classLabel=raw_prediction.classLabel,
        )
    # Hien phap I: khong ep chon mot tu khi model khong du chac chan
    return PredictionDecision(
        accepted=False, text=REJECTED_PREDICTION_TEXT, classLabel=None
    )
