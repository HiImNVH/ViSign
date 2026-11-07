# ai/src/visign_ai/training/sequence_dataset.py
"""Doc tensor T017 va tao batch cho GRU."""

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import torch
from torch import Tensor
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import Dataset

from visign_ai.landmarks.sequence_transform import schema_digest

type SequenceSample = tuple[Tensor, int]


class SequenceDataset(Dataset[SequenceSample]):
    """Doc NPZ theo tung mau; class map cua caller quyet dinh chi so lop."""

    def __init__(
        self,
        rows: Iterable[Mapping[str, str]],
        root: Path,
        class_labels: Sequence[str],
        schema: Mapping[str, Any],
    ) -> None:
        self.class_labels = tuple(class_labels)
        label_indices = {label: index for index, label in enumerate(self.class_labels)}
        if (
            not label_indices
            or "" in label_indices
            or len(label_indices) != len(self.class_labels)
        ):
            raise ValueError("Class labels must be nonempty and unique")

        self.root = root.resolve()
        self.point_count: int = len(schema["landmarkOrder"])
        self.expected_shape = (schema["targetFrameCount"], 3 * self.point_count)
        self.metadata = {
            "featureSchemaVersion": schema["featureSchemaVersion"],
            "extractorVersion": schema["extractorVersion"],
            "schemaSha256": schema_digest(schema),
        }
        self.samples: list[tuple[str, str, int]] = []
        for row in rows:
            sample_id, label = row["sampleId"], row["classLabel"]
            if label not in label_indices:
                raise ValueError(
                    f"{sample_id}: classLabel is outside the class map: {label}"
                )
            self.samples.append((sample_id, row["landmarkPath"], label_indices[label]))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> SequenceSample:
        sample_id, relative_path, label = self.samples[index]
        path = self._artifact_path(relative_path)
        with np.load(path, allow_pickle=False) as archive:
            if "sampleId" not in archive or archive["sampleId"].item() != sample_id:
                raise ValueError(f"{sample_id}: artifact sampleId mismatch")
            for key, expected in self.metadata.items():
                if key not in archive or archive[key].item() != expected:
                    raise ValueError(f"{sample_id}: {key} mismatch")
            if "features" not in archive or "missingPointMask" not in archive:
                raise ValueError(f"{sample_id}: artifact has no features or point mask")
            features = archive["features"]
            missing_points = archive["missingPointMask"]

        if features.shape != self.expected_shape or features.dtype != np.float32:
            raise ValueError(
                f"{sample_id}: expected float32 features shaped {self.expected_shape}"
            )
        if not np.isfinite(features).all():
            raise ValueError(f"{sample_id}: non-finite features")
        validity = features[:, 2 * self.point_count :]
        if (
            missing_points.dtype != np.bool_
            or not np.isin(validity, (0, 1)).all()
            or not np.array_equal(missing_points, validity == 0)
        ):
            raise ValueError(f"{sample_id}: invalid point mask")
        return torch.from_numpy(features), label

    def _artifact_path(self, value: str) -> Path:
        relative = PurePosixPath(value)
        if (
            relative.is_absolute()
            or relative.suffix != ".npz"
            or ".." in relative.parts
            or any(char in value for char in ("\\", ":", "\x00"))
        ):
            raise ValueError("landmarkPath must be a relative NPZ path")
        resolved = self.root.joinpath(*relative.parts).resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError("landmarkPath escapes dataset root")
        return resolved


def collate_sequences(
    samples: Sequence[SequenceSample],
) -> tuple[Tensor, Tensor, Tensor]:
    """Tra features, do dai chuoi, va chi so lop theo thu tu batch."""
    if not samples:
        raise ValueError("Cannot collate an empty batch")
    sequences, labels = zip(*samples, strict=True)
    return (
        pad_sequence(sequences, batch_first=True),
        torch.tensor([len(sequence) for sequence in sequences], dtype=torch.long),
        torch.tensor(labels, dtype=torch.long),
    )
