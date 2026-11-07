# services/inference-api/src/visign_api/inference/predictor_registry.py
# Giu predictor dang phuc vu; candidate loi khong thay predictor dang chay va khong lui ve fixture (T037).
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from visign_api.domain.errors import ModelNotReadyException
from visign_api.domain.model_version import ArtifactKind
from visign_api.inference.artifact_loader import (
    ArtifactRejectedError,
    LoadedArtifact,
    load_artifact,
)
from visign_api.inference.gru_predictor import GruRuntime, load_gru_predictor
from visign_api.inference.predictor import FixturePredictor, Predictor

PredictorFactory = Callable[[LoadedArtifact], Predictor]

# Registry chi co fixture thi pilot/full fail closed; dung lam nen cho bo factory mac dinh
FIXTURE_PREDICTOR_FACTORIES: Mapping[ArtifactKind, PredictorFactory] = {
    ArtifactKind.FIXTURE: FixturePredictor,
}


def build_predictor_factories(
    gru_runtime: GruRuntime,
) -> Mapping[ArtifactKind, PredictorFactory]:
    # Pilot/full dung chung adapter GRU; torch chi duoc nap khi kich hoat artifact that
    gru_factory = partial(load_gru_predictor, gru_runtime=gru_runtime)
    return {
        **FIXTURE_PREDICTOR_FACTORIES,
        ArtifactKind.PILOT: gru_factory,
        ArtifactKind.FULL: gru_factory,
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
