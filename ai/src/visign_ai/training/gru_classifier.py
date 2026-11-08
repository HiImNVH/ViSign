# ai/src/visign_ai/training/gru_classifier.py
"""Phan lop chuoi landmark co padding bang GRU."""

import math
from collections.abc import Sequence

import torch
from torch import Tensor, nn
from torch.nn.utils.rnn import pack_padded_sequence


class GRUClassifier(nn.Module):
    """Tra logits theo thu tu lop ma caller dung khi gan nhan.

    ``feature_scale`` (tuy chon) nhan tung dac trung truoc GRU de the hien trong so nhom diem (tay/mat/vai, xem
    ``group_weights.py``). He so luu trong buffer nen nam trong state_dict va di cung artifact; model cu khong co
    he so van nap duoc nhu truoc.
    """

    feature_scale: Tensor | None

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_classes: int,
        num_layers: int = 1,
        feature_scale: Sequence[float] | None = None,
    ) -> None:
        super().__init__()
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
        self.classifier = nn.Linear(hidden_size, num_classes)
        if feature_scale is None:
            self.feature_scale = None
        else:
            values = [float(value) for value in feature_scale]
            if len(values) != input_size or not all(
                math.isfinite(v) and v > 0 for v in values
            ):
                raise ValueError(
                    "feature_scale must have input_size positive finite values"
                )
            self.register_buffer(
                "feature_scale", torch.tensor(values, dtype=torch.float32)
            )

    def forward(self, sequences: Tensor, lengths: Tensor) -> Tensor:
        if (
            sequences.ndim != 3
            or sequences.shape[0] == 0
            or sequences.shape[2] != self.gru.input_size
            or lengths.shape != (sequences.shape[0],)
        ):
            raise ValueError(
                "Expected nonempty [batch, time, features] and [batch] lengths"
            )
        if lengths.dtype not in (torch.int32, torch.int64):
            raise ValueError("Sequence lengths must be integers")
        if torch.any((lengths < 1) | (lengths > sequences.shape[1])):
            raise ValueError("Sequence lengths are outside the padded time dimension")
        if self.feature_scale is not None:
            # Khung padding bang 0 van bang 0 sau khi nhan
            sequences = sequences * self.feature_scale
        packed = pack_padded_sequence(
            sequences, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, hidden = self.gru(packed)
        return self.classifier(hidden[-1])
