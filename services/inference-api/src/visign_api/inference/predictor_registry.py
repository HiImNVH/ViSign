# services/inference-api/src/visign_api/inference/predictor_registry.py
# Giu predictor dang phuc vu; candidate loi khong thay predictor dang chay va khong lui ve fixture (T037).
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from visign_api.domain.errors import ModelNotReadyException
from visign_api.domain.model_version import ArtifactKind
from visign_api.inference.artifact_loader import (
    ArtifactRejectedError,
    LoadedArtifact,
    load_artifact,
)
from visign_api.inference.predictor import FixturePredictor, Predictor

PredictorFactory = Callable[[LoadedArtifact], Predictor]

# Pilot/full se dang ky adapter GRU khi P3 ban giao T033/T036; truoc do hai kind nay fail closed
DEFAULT_PREDICTOR_FACTORIES: Mapping[ArtifactKind, PredictorFactory] = {
    ArtifactKind.FIXTURE: FixturePredictor,
}


@dataclass(frozen=True)
class ActivePredictor:
    predictor: Predictor
    artifactDirectory: Path


class PredictorRegistry:
    def __init__(
        self, predictor_factories: Mapping[ArtifactKind, PredictorFactory]
    ) -> None:
        self._predictor_factories = dict(predictor_factories)
        self._active: ActivePredictor | None = None

    @property
    def is_ready(self) -> bool:
        return self._active is not None

    @property
    def active_predictor(self) -> Predictor:
        if self._active is None:
            raise ModelNotReadyException()
        return self._active.predictor

    @property
    def active_artifact_directory(self) -> Path | None:
        return None if self._active is None else self._active.artifactDirectory

    def activate(
        self, artifact_directory: Path, expected_schema_version: str | None
    ) -> None:
        loaded_artifact = load_artifact(artifact_directory, expected_schema_version)
        artifact_kind = loaded_artifact.metadata.artifactKind
        predictor_factory = self._predictor_factories.get(artifact_kind)
        if predictor_factory is None:
            raise ArtifactRejectedError(
                f"Chua co predictor cho artifactKind {artifact_kind.value}"
            )
        # Chi thay predictor sau khi candidate nap xong; loi o bat ky buoc nao deu giu predictor cu
        self._active = ActivePredictor(
            predictor_factory(loaded_artifact), artifact_directory
        )
