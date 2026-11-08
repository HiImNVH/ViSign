# ai/src/visign_ai/training/train.py
"""Train a ViSign GRU from an approved schema and audited manifest."""

import argparse
import csv
import json
import math
import os
import random
import re
import sys
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from zipfile import BadZipFile

import numpy as np
import torch
import yaml
from torch import Tensor
from torch.utils.data import DataLoader, Dataset

from visign_ai.cli import make_console_output_safe
from visign_ai.evaluation.release_gate import build_model_metadata
from visign_ai.landmarks.sequence_transform import schema_digest

from .augmentation import AugmentedDataset
from .group_weights import feature_scale
from .gru_classifier import GRUClassifier
from .sequence_dataset import SequenceDataset, collate_sequences
from .tracking import start_tracking
from .training_inputs import TrainingInputs, prepare_inputs


def make_loader(inputs: TrainingInputs, root: Path, split: str) -> DataLoader[Any]:
    dataset: Dataset[Any] = SequenceDataset(
        (row for row in inputs.rows if row["split"] == split),
        root,
        inputs.labels,
        inputs.schema,
    )
    augmentation = inputs.config.get("augmentation")
    if split == "train" and augmentation:
        # Chi tang cuong tap train; validation/test giu nguyen de chon checkpoint/nguong va danh gia trung thuc
        dataset = AugmentedDataset(dataset, augmentation, inputs.config["seed"])
    return DataLoader(
        dataset,
        batch_size=inputs.config["batch_size"],
        shuffle=split == "train",
        generator=torch.Generator().manual_seed(inputs.config["seed"]),
        collate_fn=collate_sequences,
    )


def train_epoch(
    model: GRUClassifier, loader: DataLoader[Any], optimizer: torch.optim.Optimizer
) -> float:
    model.train()
    device = next(model.parameters()).device
    total, count = 0.0, 0
    for features, lengths, targets in loader:
        optimizer.zero_grad()
        logits = model(features.to(device), lengths)
        loss = torch.nn.functional.cross_entropy(logits, targets.to(device))
        if not torch.isfinite(loss):
            raise ValueError("Non-finite training loss")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
        optimizer.step()
        total += loss.item() * len(targets)
        count += len(targets)
    return total / count


@torch.inference_mode()
def validate(
    model: GRUClassifier, loader: DataLoader[Any]
) -> tuple[float, Tensor, Tensor]:
    model.eval()
    device = next(model.parameters()).device
    scores, labels = [], []
    total, count = 0.0, 0
    for features, lengths, targets in loader:
        logits = model(features.to(device), lengths)
        total += torch.nn.functional.cross_entropy(
            logits, targets.to(device), reduction="sum"
        ).item()
        count += len(targets)
        scores.append(logits.softmax(dim=1).cpu())
        labels.append(targets)
    loss = total / count
    if not math.isfinite(loss):
        raise ValueError("Non-finite validation loss")
    return loss, torch.cat(scores), torch.cat(labels)


def threshold_sweep(
    scores: Tensor, truth: Tensor, candidates: list[float]
) -> list[dict[str, float]]:
    confidence, predicted = scores.max(dim=1)
    correct = predicted == truth
    rows = []
    for threshold in candidates:
        accepted = confidence >= threshold
        accepted_count = accepted.sum().item()
        correct_count = (correct & accepted).sum().item()
        rows.append(
            {
                "threshold": threshold,
                "coverage": accepted_count / len(truth),
                "acceptedClassAccuracy": correct_count / accepted_count
                if accepted_count
                else 0.0,
                "score": (2 * correct_count - accepted_count) / len(truth),
            }
        )
    return rows


def fit(
    inputs: TrainingInputs,
    args: argparse.Namespace,
    on_epoch: Callable[[int, int], None] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    config = inputs.config
    seed = config["seed"]
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    if args.device == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA is not available")
    model_config: dict[str, Any] = {
        "input_size": config["input_size"],
        "hidden_size": config["hidden_size"],
        "num_classes": len(inputs.labels),
        "num_layers": config["num_layers"],
    }
    group_weights = config.get("group_weights")
    if group_weights is not None:
        # He so theo dac trung di cung checkpoint de API nhan dung nhu luc train
        model_config["feature_scale"] = feature_scale(
            inputs.schema["landmarkOrder"], group_weights
        )
    model = GRUClassifier(**model_config).to(args.device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config["learning_rate"])
    training = make_loader(inputs, args.feature_root, "train")
    validation = make_loader(inputs, args.feature_root, "validation")
    history = []
    tracker = start_tracking(
        config,
        getattr(args, "model_version", "visign-train"),
        {
            **{key: value for key, value in config.items() if key != "wandb"},
            "datasetVersion": getattr(args, "dataset_version", None),
            "manifestSha256": inputs.manifest_sha256,
            "classLabels": inputs.labels,
            "trainSamples": sum(row["split"] == "train" for row in inputs.rows),
            "validationSamples": sum(
                row["split"] == "validation" for row in inputs.rows
            ),
        },
    )
    best_loss = math.inf
    best_epoch = 0
    best_state: dict[str, Tensor] = {}
    for epoch in range(1, config["epochs"] + 1):
        training_loss = train_epoch(model, training, optimizer)
        validation_loss, _, _ = validate(model, validation)
        history.append(
            {
                "epoch": epoch,
                "trainLoss": training_loss,
                "validationLoss": validation_loss,
            }
        )
        if on_epoch is not None:
            on_epoch(epoch, config["epochs"])
        if tracker is not None:
            tracker.log_epoch(epoch, training_loss, validation_loss)
        if validation_loss < best_loss:
            best_loss, best_epoch = validation_loss, epoch
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in model.state_dict().items()
            }

    model.load_state_dict(best_state)
    _, scores, truth = validate(model, validation)
    sweep = threshold_sweep(scores, truth, config["threshold_candidates"])
    chosen = max(
        sweep, key=lambda item: (item["score"], item["coverage"], -item["threshold"])
    )
    checkpoint = {
        "modelConfig": model_config,
        "stateDict": best_state,
        "schemaSha256": schema_digest(inputs.schema),
        "groupWeights": group_weights,
        "labelBinding": {
            "classLabels": inputs.labels,
            "meaningMap": inputs.meaning_map,
            "displayTextMap": inputs.display_text_map,
        },
    }
    report = {
        "seed": seed,
        "config": config,
        "device": args.device,
        "torchVersion": str(torch.__version__),
        "manifestSha256": inputs.manifest_sha256,
        "splitAudit": inputs.split_audit,
        "history": history,
        "bestEpoch": best_epoch,
        "validationThresholdSweep": sweep,
        "thresholdRule": "Maximize correct accepted minus incorrect accepted, then coverage, then lower threshold",
        "acceptanceThreshold": chosen["threshold"],
        "groupWeights": group_weights,
        "wandbRunId": None,
        "wandbMode": None,
        "wandbUrl": None,
    }
    if tracker is not None:
        report.update(
            tracker.finish(
                {
                    "bestEpoch": best_epoch,
                    "bestValidationLoss": best_loss,
                    "acceptanceThreshold": chosen["threshold"],
                },
                sweep,
            )
        )
    return checkpoint, report


def publish(
    output: Path, checkpoint: dict[str, Any], documents: dict[str, dict[str, Any]]
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".visign-train-", dir=output.parent) as temporary:
        staging = Path(temporary) / "artifact"
        staging.mkdir()
        torch.save(checkpoint, staging / "model.pt")
        for name, value in documents.items():
            (staging / name).write_text(
                json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                encoding="utf-8",
            )
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Output exists: {output}")
        staging.rename(output)


def train(
    args: argparse.Namespace, on_epoch: Callable[[int, int], None] | None = None
) -> None:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*-v[1-9][0-9]*", args.dataset_version):
        raise ValueError("dataset-version must match <manifest>-v<positive integer>")
    if not args.model_version.strip():
        raise ValueError("model-version cannot be blank")
    output = args.output.absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Output exists: {output}")
    inputs = prepare_inputs(args)
    checkpoint, report = fit(inputs, args, on_epoch)
    metadata = build_model_metadata(
        {
            **checkpoint["labelBinding"],
            "modelVersion": args.model_version,
            "artifactKind": inputs.config["artifact_kind"],
            "datasetVersion": args.dataset_version,
            "featureSchemaVersion": inputs.schema["featureSchemaVersion"],
            "extractorVersion": inputs.schema["extractorVersion"],
            "meanings": list(inputs.display_text_map),
            "acceptanceThreshold": report["acceptanceThreshold"],
        }
    )
    report["datasetVersion"] = args.dataset_version
    publish(
        output,
        checkpoint,
        {
            "feature_schema.json": inputs.schema,
            "model_info.json": metadata,
            "training-report.json": report,
        },
    )


def main() -> int:
    make_console_output_safe()
    parser = argparse.ArgumentParser(description=__doc__)
    for option in (
        "manifest",
        "feature-root",
        "class-map",
        "schema",
        "config",
        "output",
    ):
        parser.add_argument(f"--{option}", type=Path, required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--classes", nargs="+")
    parser.add_argument("--p0-meanings", type=Path)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    args = parser.parse_args()
    try:
        train(args)
    except (
        OSError,
        ValueError,
        RuntimeError,
        TypeError,
        KeyError,
        csv.Error,
        yaml.YAMLError,
        BadZipFile,
    ) as error:
        print(f"T036: {error}", file=sys.stderr)
        return 2
    print("Training artifact written; test evaluation pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
