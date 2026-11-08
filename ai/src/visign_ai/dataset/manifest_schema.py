"""SignSample manifest row contract (T010).

The CSV column names follow ``specs/001-vsl-recognition-mvp/data-model.md``
and ``docs/team/data-convention.md``. Batch-level and cross-file checks belong
to the manifest validator (T012); this module also checks duplicate sample IDs
within a supplied collection because uniqueness cannot be a row-only property.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from urllib.parse import parse_qsl, urlsplit

from .entities import DataSplit, LicenseStatus, VerificationStatus

MANIFEST_COLUMNS = (
    "sampleId",
    "classLabel",
    "meaningId",
    "signerId",
    "recordingSessionId",
    "sourceUri",
    "licenseStatus",
    "verificationStatus",
    "rejectionReason",
    "rawPath",
    "landmarkPath",
    "durationMs",
    "frameCount",
    "split",
)

_REQUIRED_COLUMNS = frozenset(MANIFEST_COLUMNS) - {
    "signerId",
    "sourceUri",
    "rejectionReason",
    "landmarkPath",
    "split",
}
_SAMPLE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*_[0-9a-f]{12}\Z")
_MEANING_ID = re.compile(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*\Z")
_CLASS_LABEL = re.compile(
    r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_(?:HCM|HN|HP|OTHER|UNKNOWN)_[1-9][0-9]*\Z"
)
_SIGNER_ID = re.compile(r"S[0-9]{3}\Z")
_SESSION_ID = re.compile(
    r"(?:[a-z0-9]+(?:-[a-z0-9]+)*_[0-9a-f]{12}|S[0-9]{3}-R[0-9]{2})\Z"
)
_SENSITIVE_QUERY_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "key",
        "password",
        "secret",
        "signature",
        "token",
        "sig",
        "x-amz-signature",
        "x-amz-credential",
        "x-goog-signature",
        "x-goog-credential",
    }
)


class ManifestSchemaError(ValueError):
    """Raised when a manifest row violates the shared data contract."""


def _text(name: str, value: object, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value or value != value.strip():
        raise ManifestSchemaError(f"{name} must be a non-empty, trimmed string")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ManifestSchemaError(f"{name} must not contain control characters")
    if unicodedata.normalize("NFC", value) != value:
        raise ManifestSchemaError(f"{name} must use Unicode NFC")
    return value


def _relative_path(name: str, value: str) -> None:
    # Paths always use / relative to the external dataset root; reject traversal.
    if (
        value.startswith("/")
        or "\\" in value
        or ":" in value
        or any(part in ("", ".", "..") for part in value.split("/"))
    ):
        raise ManifestSchemaError(f"{name} must be a safe relative POSIX path")


def _positive_integer(name: str, value: object) -> int:
    if type(value) is int:
        result = value
    elif isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        result = int(value)
    else:
        raise ManifestSchemaError(f"{name} must be an integer > 0")
    if result <= 0:
        raise ManifestSchemaError(f"{name} must be an integer > 0")
    return result


@dataclass(frozen=True, slots=True)
class ManifestRow:
    """One validated video/landmark sample; optional fields are null until audited.

    ``split`` is recorded here but assigned only by the split tool (T018).
    Class/meaning registry references, media metadata, and source-video split
    integrity are checked by downstream validation (T012/T018).
    """

    sample_id: str
    class_label: str
    meaning_id: str
    recording_session_id: str
    license_status: LicenseStatus
    verification_status: VerificationStatus
    raw_path: str
    duration_ms: int
    frame_count: int
    source_uri: str | None = None
    signer_id: str | None = None
    rejection_reason: str | None = None
    landmark_path: str | None = None
    split: DataSplit | None = None

    def __post_init__(self) -> None:
        for name in (
            "sample_id",
            "class_label",
            "meaning_id",
            "recording_session_id",
            "license_status",
            "verification_status",
            "raw_path",
        ):
            _text(name, getattr(self, name))
        for name in (
            "source_uri",
            "signer_id",
            "rejection_reason",
            "landmark_path",
            "split",
        ):
            _text(name, getattr(self, name), optional=True)

        if not _SAMPLE_ID.fullmatch(self.sample_id):
            raise ManifestSchemaError(
                "sampleId must be {sourceId}_{12 lowercase hex SHA-256}"
            )
        if not _MEANING_ID.fullmatch(self.meaning_id):
            raise ManifestSchemaError("meaningId must be UPPER_SNAKE_CASE")
        if not _CLASS_LABEL.fullmatch(self.class_label):
            raise ManifestSchemaError(
                "classLabel must be {meaningId}_{region}_{variant}"
            )
        if self.class_label.rsplit("_", 2)[0] != self.meaning_id:
            raise ManifestSchemaError("classLabel must belong to meaningId")
        if self.signer_id is not None and not _SIGNER_ID.fullmatch(self.signer_id):
            raise ManifestSchemaError("signerId must match S###")
        if not _SESSION_ID.fullmatch(self.recording_session_id):
            raise ManifestSchemaError(
                "recordingSessionId must be a source sampleId, sourceId-R## or S###-R##"
            )
        if (
            self.recording_session_id.startswith("S")
            and self.signer_id is not None
            and not self.recording_session_id.startswith(self.signer_id + "-R")
        ):
            raise ManifestSchemaError("signer session must match signerId")

        if self.license_status not in ("approved", "restricted", "unknown"):
            raise ManifestSchemaError(
                "licenseStatus must be approved, restricted or unknown"
            )
        if self.verification_status not in ("verified", "unverified", "rejected"):
            raise ManifestSchemaError(
                "verificationStatus must be verified, unverified or rejected"
            )
        if self.split is not None and self.split not in ("train", "validation", "test"):
            raise ManifestSchemaError("split must be train, validation, test or null")
        object.__setattr__(self, "license_status", LicenseStatus(self.license_status))
        object.__setattr__(
            self, "verification_status", VerificationStatus(self.verification_status)
        )
        if self.split is not None:
            object.__setattr__(self, "split", DataSplit(self.split))
        if self.verification_status == "rejected" and self.rejection_reason is None:
            raise ManifestSchemaError(
                "rejectionReason is required for rejected samples"
            )

        _relative_path("rawPath", self.raw_path)
        if self.landmark_path is not None:
            _relative_path("landmarkPath", self.landmark_path)

        try:
            parsed_source = urlsplit(self.source_uri or "")
        except ValueError as exc:
            raise ManifestSchemaError("sourceUri is malformed") from exc
        if (
            parsed_source.username
            or parsed_source.password
            or any(
                key.lower() in _SENSITIVE_QUERY_KEYS
                for key, _ in parse_qsl(parsed_source.query, keep_blank_values=True)
            )
        ):
            raise ManifestSchemaError("sourceUri must not contain credentials")

        # Direct construction is strictly typed; from_mapping parses CSV digits.
        for name, value in (
            ("durationMs", self.duration_ms),
            ("frameCount", self.frame_count),
        ):
            if type(value) is not int:
                raise ManifestSchemaError(f"{name} must be an integer > 0")
            _positive_integer(name, value)
        if not 300 <= self.duration_ms <= 6000:
            raise ManifestSchemaError(
                "durationMs must be within pipeline limits 300..6000"
            )

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> ManifestRow:
        """Parse camelCase metadata (including CSV strings) into a validated row."""
        unexpected = set(data) - set(MANIFEST_COLUMNS)
        missing = _REQUIRED_COLUMNS - set(data)
        if unexpected or missing:
            raise ManifestSchemaError(
                f"invalid manifest columns: missing={sorted(missing)}, "
                f"extra={sorted(map(str, unexpected))}"
            )

        def required(key: str) -> str:
            value = _text(key, data[key])
            assert value is not None
            return value

        def optional(key: str) -> str | None:
            value = data.get(key)
            return None if value is None or value == "" else _text(key, value)

        return cls(
            sample_id=required("sampleId"),
            class_label=required("classLabel"),
            meaning_id=required("meaningId"),
            signer_id=optional("signerId"),
            recording_session_id=required("recordingSessionId"),
            source_uri=optional("sourceUri"),
            license_status=cast(LicenseStatus, required("licenseStatus")),
            verification_status=cast(
                VerificationStatus, required("verificationStatus")
            ),
            rejection_reason=optional("rejectionReason"),
            raw_path=required("rawPath"),
            landmark_path=optional("landmarkPath"),
            duration_ms=_positive_integer("durationMs", data["durationMs"]),
            frame_count=_positive_integer("frameCount", data["frameCount"]),
            split=cast(DataSplit | None, optional("split")),
        )

    def to_csv_row(self) -> dict[str, str]:
        """Return ordered CSV-compatible fields (empty string represents null)."""
        values = (
            self.sample_id,
            self.class_label,
            self.meaning_id,
            self.signer_id,
            self.recording_session_id,
            self.source_uri,
            self.license_status,
            self.verification_status,
            self.rejection_reason,
            self.raw_path,
            self.landmark_path,
            self.duration_ms,
            self.frame_count,
            self.split,
        )
        return {
            column: "" if value is None else str(value)
            for column, value in zip(MANIFEST_COLUMNS, values, strict=True)
        }

    @property
    def passes_release_exclusions(self) -> bool:
        """Only first-pass gating; full release has additional quality checks."""
        return (
            self.license_status == "approved" and self.verification_status != "rejected"
        )


def validate_unique_sample_ids(rows: Iterable[ManifestRow]) -> None:
    """Reject duplicate sample IDs across rows, including different labels/splits."""
    first_seen: dict[str, int] = {}
    for index, row in enumerate(rows, start=1):
        previous = first_seen.setdefault(row.sample_id, index)
        if previous != index:
            raise ManifestSchemaError(
                f"duplicate sampleId {row.sample_id!r} at rows {previous} and {index}"
            )


def validate_rows(
    rows: Iterable[ManifestRow],
    *,
    known_meanings: set[str],
    known_classes: Mapping[str, str],
    dataset_root: Path | None = None,
    for_release: bool = False,
) -> list[ManifestRow]:
    """Validate registry references, group isolation and optional raw-file hashes.

    A class registry maps classLabel to meaningId. No registry or class is invented.
    This does not assign splits or prove semantic labels, rights or model quality.
    """
    result = list(rows)
    validate_unique_sample_ids(result)
    sessions: dict[str, set[str | None]] = {}
    hashes: set[str] = set()
    for row in result:
        if row.meaning_id not in known_meanings:
            raise ManifestSchemaError(f"unknown meaningId: {row.meaning_id}")
        if known_classes.get(row.class_label) != row.meaning_id:
            raise ManifestSchemaError(
                f"unknown/mismatched classLabel: {row.class_label}"
            )
        sessions.setdefault(row.recording_session_id, set()).add(row.split)
        if for_release and (not row.passes_release_exclusions or row.split is None):
            raise ManifestSchemaError(f"sample excluded from release: {row.sample_id}")
        if dataset_root is not None:
            root = dataset_root.resolve()
            raw = (root / row.raw_path).resolve()
            if not raw.is_relative_to(root) or not raw.is_file():
                raise ManifestSchemaError("rawPath missing or escapes dataset root")
            with raw.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if row.sample_id.rsplit("_", 1)[1] != digest[:12]:
                raise ManifestSchemaError(f"raw hash mismatch: {row.sample_id}")
            if digest in hashes:
                raise ManifestSchemaError("duplicate raw content across sources")
            hashes.add(digest)
    for group, splits in sessions.items():
        if len(splits) > 1:
            raise ManifestSchemaError(
                f"recordingSessionId leakage/mixed assigned splits: {group}"
            )
    return result


def read_manifest_csv(path: Path) -> list[ManifestRow]:
    """Read canonical UTF-8/no-BOM/LF CSV; inventory review files are separate."""
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise ManifestSchemaError(
            "CSV must be UTF-8 without BOM, LF, with final newline"
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ManifestSchemaError("CSV must be UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    if reader.fieldnames != list(MANIFEST_COLUMNS):
        raise ManifestSchemaError("CSV header must match MANIFEST_COLUMNS in order")
    try:
        return [ManifestRow.from_mapping(row) for row in reader]
    except csv.Error as exc:
        raise ManifestSchemaError("malformed CSV") from exc


def validate_dataset_version(value: str) -> str:
    """Version is manifest-level metadata, never inferred from the ZIP filename."""
    _text("datasetVersion", value)
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*-v[1-9][0-9]*", value):
        raise ManifestSchemaError(
            "datasetVersion must match {manifest}-v{positive integer}"
        )
    return value
