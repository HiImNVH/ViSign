# ai/src/visign_ai/training/gru_classifier.py
"""Phan lop chuoi landmark co padding bang GRU."""

import torch
from torch import Tensor, nn
from torch.nn.utils.rnn import pack_padded_sequence


class GRUClassifier(nn.Module):
    """Tra logits theo thu tu lop ma caller dung khi gan nhan."""

    def __init__(
        self, input_size: int, hidden_size: int, num_classes: int, num_layers: int = 1
    ) -> None:
        super().__init__()
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
        self.classifier = nn.Linear(hidden_size, num_classes)

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
        packed = pack_padded_sequence(
            sequences, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, hidden = self.gru(packed)
        return self.classifier(hidden[-1])
