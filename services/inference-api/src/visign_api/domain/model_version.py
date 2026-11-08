# services/inference-api/src/visign_api/domain/model_version.py
# Metadata artifact fixture/pilot/full va cong demoReady cho model demo (T019).
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

# Cong phat hanh FR-016: chi full model du 10 nghia va dat ca hai nguong moi duoc demo
REQUIRED_DEMO_MEANING_COUNT = 10
MIN_DEMO_MACRO_F1 = 0.80
MIN_DEMO_PER_MEANING_RECALL = 0.65
MAX_SUPPORTED_MEANINGS = 10
DEFAULT_ACCEPTANCE_THRESHOLD = 0.70


class ArtifactKind(StrEnum):
    FIXTURE = "fixture"
    PILOT = "pilot"
    FULL = "full"


class ModelMetadata(BaseModel):
    modelVersion: str
    artifactKind: ArtifactKind
    datasetVersion: str
    featureSchemaVersion: str
    extractorVersion: str
    meanings: list[str] = Field(min_length=1, max_length=MAX_SUPPORTED_MEANINGS)
    classLabels: list[str] = Field(default_factory=list)
    meaningMap: dict[str, str] = Field(default_factory=dict)
    displayTextMap: dict[str, str] = Field(default_factory=dict)
    acceptanceThreshold: float = Field(DEFAULT_ACCEPTANCE_THRESHOLD, ge=0.0, le=1.0)
    accuracy: float | None = Field(None, ge=0.0, le=1.0)
    macroF1: float | None = Field(None, ge=0.0, le=1.0)
    perMeaningPrecision: dict[str, float] | None = None
    perMeaningRecall: dict[str, float] | None = None
    evaluatedAt: datetime | None = None
    demoReady: bool = False

    @model_validator(mode="after")
    def enforce_demo_gate(self) -> "ModelMetadata":
        # Khong tin demoReady do artifact tu khai: fail closed neu gate khong dat
        self.demoReady = self.demoReady and passes_demo_gate(self)
        return self


def passes_demo_gate(metadata: ModelMetadata) -> bool:
    if metadata.artifactKind is not ArtifactKind.FULL:
        return False
    if len(metadata.meanings) != REQUIRED_DEMO_MEANING_COUNT:
        return False
    if metadata.macroF1 is None or metadata.macroF1 < MIN_DEMO_MACRO_F1:
        return False
    return has_minimum_recall_for_every_meaning(metadata)


def has_minimum_recall_for_every_meaning(metadata: ModelMetadata) -> bool:
    recall_by_meaning = metadata.perMeaningRecall or {}
    return all(
        recall_by_meaning.get(meaning, -1.0) >= MIN_DEMO_PER_MEANING_RECALL
        for meaning in metadata.meanings
    )


class ModelInfoResponse(BaseModel):
    # Khop contracts/openapi.yaml #/components/schemas/ModelInfo; metric la bat buoc nhung nullable
    modelVersion: str
    artifactKind: Literal["fixture", "pilot", "full"]
    datasetVersion: str
    featureSchemaVersion: str
    extractorVersion: str
    meanings: list[str] = Field(min_length=1, max_length=MAX_SUPPORTED_MEANINGS)
    acceptanceThreshold: float = Field(ge=0.0, le=1.0)
    macroF1: float | None = Field(ge=0.0, le=1.0)
    perMeaningRecall: dict[str, float] | None
    evaluatedAt: str | None
    demoReady: bool
    # T109 (FR-005): chu tieng Viet cua tung nghia de UI khong hien ma nghia; null khi artifact khong khai
    meaningDisplayTexts: dict[str, str] | None = None

    @classmethod
    def from_metadata(cls, metadata: ModelMetadata) -> "ModelInfoResponse":
        evaluated_at = (
            metadata.evaluatedAt.isoformat() if metadata.evaluatedAt else None
        )
        return cls(
            modelVersion=metadata.modelVersion,
            artifactKind=metadata.artifactKind.value,
            datasetVersion=metadata.datasetVersion,
            featureSchemaVersion=metadata.featureSchemaVersion,
            extractorVersion=metadata.extractorVersion,
            meanings=metadata.meanings,
            acceptanceThreshold=metadata.acceptanceThreshold,
            macroF1=metadata.macroF1,
            perMeaningRecall=metadata.perMeaningRecall,
            evaluatedAt=evaluated_at,
            demoReady=metadata.demoReady,
            meaningDisplayTexts={
                meaning: metadata.displayTextMap[meaning]
                for meaning in metadata.meanings
                if metadata.displayTextMap.get(meaning, "").strip()
            }
            or None,
        )
