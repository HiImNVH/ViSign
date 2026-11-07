# ai/tests/training/test_sequence_dataset.py
"""Kiem tra duong noi tu NPZ T017 den batch GRU."""

from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
from numpy.typing import NDArray
from torch.utils.data import DataLoader
from visign_ai.landmarks.extract_manifest import write_sequence
from visign_ai.landmarks.sequence_transform import load_schema
from visign_ai.training.gru_classifier import GRUClassifier
from visign_ai.training.sequence_dataset import SequenceDataset, collate_sequences


def make_sample(
    root: Path, sample_id: str, label: str, schema: dict[str, Any]
) -> dict[str, str]:
    path = root / f"{sample_id}.npz"
    features: NDArray[np.float32] = np.zeros((32, 234), dtype=np.float32)
    features[:, 156:] = 1
    features[0, 156] = 0
    write_sequence(
        path,
        sample_id,
        {
            "schema": schema,
            "tensor": features,
            "tensor_mask": features[:, 156:] == 1,
            "target": np.linspace(0, 1000, 32),
        },
    )
    return {"sampleId": sample_id, "classLabel": label, "landmarkPath": path.name}


def test_t017_npz_batch_reaches_gru_in_class_map_order(tmp_path: Path) -> None:
    schema = load_schema()
    labels = ["SOT_HCM_1", "CAM_ON_HN_1", "NHAN_HCM_1"]
    rows = [
        make_sample(tmp_path, "one", labels[1], schema),
        make_sample(tmp_path, "two", labels[0], schema),
    ]
    dataset = SequenceDataset(rows, tmp_path, labels, schema)
    assert dataset.class_labels == tuple(labels)
    loader = DataLoader(dataset, batch_size=2, collate_fn=collate_sequences)
    sequences, lengths, targets = next(iter(loader))
    assert sequences.shape == (2, 32, 234)
    assert lengths.tolist() == [32, 32]
    assert targets.tolist() == [1, 0]
    assert lengths.dtype == targets.dtype == torch.long
    with torch.inference_mode():
        logits = GRUClassifier(234, 8, len(labels))(sequences, lengths)
    assert logits.shape == (2, 3)
    assert torch.isfinite(logits).all()


def test_collate_keeps_temporal_positions_and_pads_to_longest() -> None:
    short = torch.ones(2, 234)
    long = torch.ones(5, 234) * 2
    sequences, lengths, targets = collate_sequences([(short, 2), (long, 0)])
    assert sequences.shape == (2, 5, 234)
    assert lengths.tolist() == [2, 5]
    assert targets.tolist() == [2, 0]
    torch.testing.assert_close(sequences[0, :2], short)
    assert not sequences[0, 2:].any()


def test_rejects_labels_outside_class_map(tmp_path: Path) -> None:
    row = {"sampleId": "one", "classLabel": "SOT_HCM_1", "landmarkPath": "one.npz"}
    with pytest.raises(ValueError, match="outside the class map"):
        SequenceDataset([row], tmp_path, ["CAM_ON_HN_1"], load_schema())


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"sampleId": np.array("different")}, "sampleId"),
        ({"schemaSha256": np.array("wrong")}, "schemaSha256"),
        ({"extractorVersion": np.array("wrong")}, "extractorVersion"),
        ({"features": np.zeros((32, 160), dtype=np.float32)}, "float32 features"),
        ({"features": np.full((32, 234), np.nan, dtype=np.float32)}, "non-finite"),
        ({"missingPointMask": np.zeros((32, 78), dtype=bool)}, "point mask"),
    ],
)
def test_rejects_incompatible_npz(
    tmp_path: Path, change: dict[str, Any], message: str
) -> None:
    schema = load_schema()
    row = make_sample(tmp_path, "one", "SOT_HCM_1", schema)
    path = tmp_path / row["landmarkPath"]
    with np.load(path, allow_pickle=False) as archive:
        arrays = dict(archive)
    np.savez_compressed(path, **(arrays | change))
    dataset = SequenceDataset([row], tmp_path, ["SOT_HCM_1"], schema)
    with pytest.raises(ValueError, match=message):
        dataset[0]


@pytest.mark.parametrize("path", ["../outside.npz", "/root.npz", "C:outside.npz"])
def test_rejects_paths_outside_dataset(tmp_path: Path, path: str) -> None:
    row = {"sampleId": "one", "classLabel": "SOT_HCM_1", "landmarkPath": path}
    dataset = SequenceDataset([row], tmp_path, ["SOT_HCM_1"], load_schema())
    with pytest.raises(ValueError, match="relative NPZ"):
        dataset[0]
