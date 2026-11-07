# ai/tests/training/test_gru_classifier.py
"""Kiem tra contract GRU cho pilot va full."""

import pytest
import torch
from visign_ai.training.gru_classifier import GRUClassifier


@pytest.mark.parametrize(
    "num_classes", [2, 3, 10], ids=["pilot-two", "pilot-max", "full"]
)
def test_logits_shape_for_class_subset(num_classes: int) -> None:
    model = GRUClassifier(input_size=234, hidden_size=8, num_classes=num_classes)
    sequences = torch.zeros(2, 32, 234)
    logits = model(sequences, torch.tensor([19, 32]))
    assert logits.shape == (2, num_classes)
    assert torch.isfinite(logits).all()


def test_packing_ignores_padding_and_preserves_unsorted_batch_order() -> None:
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(17)
        model = GRUClassifier(234, 8, 3, num_layers=2).eval()
        sequences = torch.randn(3, 32, 234)
    lengths = torch.tensor([3, 32, 11])
    changed_padding = sequences.clone()
    for index, length in enumerate(lengths.tolist()):
        changed_padding[index, length:] = 100.0

    with torch.inference_mode():
        actual = model(sequences, lengths)
        expected = torch.cat(
            [
                model(sequences[index : index + 1, :length], lengths[index : index + 1])
                for index, length in enumerate(lengths.tolist())
            ],
            dim=0,
        )
        torch.testing.assert_close(actual, expected)
        torch.testing.assert_close(
            model(changed_padding, lengths), actual, rtol=0, atol=0
        )


def test_seeded_cpu_forward_is_reproducible() -> None:
    sequences = torch.ones(2, 32, 234)
    lengths = torch.tensor([32, 14])
    with torch.random.fork_rng(devices=[]), torch.inference_mode():
        torch.manual_seed(29)
        first = GRUClassifier(234, 8, 3).eval()(sequences, lengths)
        torch.manual_seed(29)
        second = GRUClassifier(234, 8, 3).eval()(sequences, lengths)
    torch.testing.assert_close(first, second, rtol=0, atol=0)


@pytest.mark.parametrize(
    ("lengths", "message"),
    [
        (torch.tensor([0, 4]), "outside"),
        (torch.tensor([33, 4]), "outside"),
        (torch.tensor([4.5, 8.0]), "integers"),
        (torch.tensor([32]), "batch"),
    ],
)
def test_rejects_invalid_lengths(lengths: torch.Tensor, message: str) -> None:
    model = GRUClassifier(234, 8, 3)
    with pytest.raises(ValueError, match=message):
        model(torch.zeros(2, 32, 234), lengths)
