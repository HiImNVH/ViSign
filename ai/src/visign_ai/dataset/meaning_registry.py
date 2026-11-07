"""T013: canonical ten-meaning P0 registry, independent of raw-video approval."""

import argparse
import csv
import hashlib
import io
import json
import re
import unicodedata
from pathlib import Path

COLUMNS = ("meaningId", "displayText", "category", "priority", "active")
CATEGORIES = {"basic", "medical", "administrative"}


class MeaningRegistryError(ValueError):
    """A registry cannot be used because its structure/invariants are invalid."""


def read_p0_meanings(path: Path) -> dict[str, dict[str, str]]:
    """Read exactly ten active P0 meanings; reject errors rather than fixing labels.

    IDs and display texts must each be unique. Returned insertion order follows
    the CSV; it is vocabulary order, not model class order. This does not certify
    sample labels, rights, class coverage or model readiness.
    """
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise MeaningRegistryError("registry must use UTF-8/no BOM/LF/final newline")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MeaningRegistryError("registry must use UTF-8") from exc
    if unicodedata.normalize("NFC", text) != text:
        raise MeaningRegistryError("registry must use Unicode NFC")
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if reader.fieldnames != list(COLUMNS):
            raise MeaningRegistryError("registry header must match COLUMNS in order")
        result: dict[str, dict[str, str]] = {}
        display_texts: set[str] = set()
        for line, row in enumerate(reader, start=2):
            if set(row) != set(COLUMNS) or any(
                not isinstance(value, str) or not value or value != value.strip()
                or any(ord(c) < 32 or ord(c) == 127 for c in value)
                for value in row.values()
            ):
                raise MeaningRegistryError(f"invalid fields at CSV line {line}")
            meaning_id = row["meaningId"]
            if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*", meaning_id):
                raise MeaningRegistryError(f"invalid meaningId: {meaning_id}")
            if meaning_id in result or row["displayText"] in display_texts:
                raise MeaningRegistryError(f"duplicate meaningId/displayText at line {line}")
            if row["category"] not in CATEGORIES:
                raise MeaningRegistryError(f"invalid category at line {line}")
            if row["priority"] != "P0" or row["active"] != "true":
                raise MeaningRegistryError("all ten P0 registry entries must be active P0")
            result[meaning_id] = row
            display_texts.add(row["displayText"])
    except csv.Error as exc:
        raise MeaningRegistryError("malformed registry CSV") from exc
    if len(result) != 10:
        raise MeaningRegistryError(f"registry must contain exactly 10 meanings, got {len(result)}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("data/manifests/p0-meanings.csv"))
    args = parser.parse_args()
    try:
        registry = read_p0_meanings(args.registry)
    except (MeaningRegistryError, OSError) as exc:
        parser.exit(1, f"Registry validation failed: {exc}\n")
    print(json.dumps({
        "valid": True, "meaningCount": len(registry), "meaningIds": list(registry),
        "sha256": hashlib.sha256(args.registry.read_bytes()).hexdigest(),
    }, ensure_ascii=False, indent=2))
