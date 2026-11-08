"""T011: duplicate IDs, release exclusions and signer/source-video leakage."""

import csv
import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from visign_ai.dataset.manifest_schema import (
    MANIFEST_COLUMNS,
    ManifestRow,
    ManifestSchemaError,
    read_manifest_csv,
    validate_dataset_version,
    validate_rows,
)


def sample(**changes: object) -> ManifestRow:
    row: dict[str, object] = dict(
        zip(
            MANIFEST_COLUMNS,
            (
                "dataset-p0_0123456789ab",
                "CAM_ON_UNKNOWN_1",
                "CAM_ON",
                "",
                "dataset-p0_0123456789ab",
                "",
                "unknown",
                "unverified",
                "",
                "reviewed/dataset-p0/sample.mp4",
                "",
                "1000",
                "30",
                "",
            ),
            strict=True,
        )
    )
    row.update(changes)
    return ManifestRow.from_mapping(row)


def validate(
    rows: list[ManifestRow],
    *,
    dataset_root: Path | None = None,
    for_release: bool = False,
) -> list[ManifestRow]:
    return validate_rows(
        rows,
        known_meanings={"CAM_ON", "GIAY_TO", "NHAN"},
        known_classes={
            "CAM_ON_UNKNOWN_1": "CAM_ON",
            "GIAY_TO_UNKNOWN_1": "GIAY_TO",
            "NHAN_UNKNOWN_1": "NHAN",
        },
        dataset_root=dataset_root,
        for_release=for_release,
    )


class ManifestValidationTests(unittest.TestCase):
    def test_csv_roundtrip_optional_source_and_signer(self):
        row = sample()
        self.assertIsNone(row.source_uri)
        self.assertIsNone(row.signer_id)
        self.assertEqual(row, ManifestRow.from_mapping(row.to_csv_row()))

    def test_invalid_rows(self):
        cases = [
            {"sampleId": "filename_1"},
            {"recordingSessionId": ""},
            {"recordingSessionId": "dataset-p0-R001"},
            {"signerId": "real name"},
            {"classLabel": "CAM_ON_UNKNOWN_01"},
            {"classLabel": "CAM_ON_EXTRA_UNKNOWN_1"},
            {"meaningId": "cảm_ơn"},
            {"rawPath": "../outside.mp4"},
            {"rawPath": "C:\\clip.mp4"},
            {"landmarkPath": "/outside.npz"},
            {"durationMs": "0"},
            {"durationMs": "299"},
            {"durationMs": "6001"},
            {"frameCount": True},
            {"frameCount": "1.5"},
            {"licenseStatus": "pending"},
            {"verificationStatus": "accepted"},
            {"split": "holdout"},
            {"verificationStatus": "rejected"},
            {"sourceUri": "https://user:pass@example.org/video"},
            {"sourceUri": "https://example.org/video?token=secret"},
            {"sourceUri": "https://[broken"},
            {"rawPath": "clip\x00.mp4"},
            {"rejectionReason": " Sai nhãn "},
            {"rejectionReason": "Ca\u0309m o\u031bn"},
        ]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(ManifestSchemaError):
                sample(**change)

    def test_known_signer_session(self):
        validate([sample(signerId="S001", recordingSessionId="S001-R01")])
        with self.assertRaises(ManifestSchemaError):
            sample(signerId="S002", recordingSessionId="S001-R01")

    def test_reference_source_hash_and_signer_session(self):
        for session in ["S001-R01", "dataset-p0_0123456789ab"]:
            validate([sample(recordingSessionId=session)])
        for session in [
            "self-rec-R01",
            "qipedc-R02",
            "-source-R01",
            "source--id-R01",
            "Source-R01",
            "source-R1",
        ]:
            with self.assertRaises(ManifestSchemaError):
                sample(recordingSessionId=session)

    def test_duplicate_sample(self):
        with self.assertRaisesRegex(ManifestSchemaError, "duplicate sampleId"):
            validate([sample(), sample()])

    def test_registry_reference(self):
        for row in [
            sample(classLabel="CAM_ON_UNKNOWN_2"),
            sample(meaningId="OTHER", classLabel="OTHER_UNKNOWN_1"),
        ]:
            with self.assertRaises(ManifestSchemaError):
                validate([row])

    def test_cross_meaning_shared_source_cannot_leak(self):
        first = sample(
            meaningId="GIAY_TO", classLabel="GIAY_TO_UNKNOWN_1", split="train"
        )
        second = sample(
            sampleId="dataset-p0_abcdef012345",
            meaningId="NHAN",
            classLabel="NHAN_UNKNOWN_1",
            split="test",
        )
        with self.assertRaisesRegex(ManifestSchemaError, "recordingSessionId leakage"):
            validate([first, second])
        validate([first, replace(second, split="train")])

    def test_same_signer_in_distinct_source_videos_is_allowed(self):
        first = sample(signerId="S001", split="train")
        second = sample(
            sampleId="dataset-p0_abcdef012345",
            signerId="S001",
            recordingSessionId="dataset-p0_abcdef012345",
            split="test",
        )
        validate([first, second])

    def test_release_excludes_unknown_restricted_rejected_and_unsplit(self):
        for row in [
            sample(split="train"),
            sample(licenseStatus="restricted", split="train"),
            sample(
                licenseStatus="approved",
                verificationStatus="rejected",
                rejectionReason="wrong label",
                split="train",
            ),
            sample(licenseStatus="approved"),
        ]:
            with self.assertRaises(ManifestSchemaError):
                validate([row], for_release=True)
        validate([sample(licenseStatus="approved", split="train")], for_release=True)

    def test_hash_and_missing_raw(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = b"synthetic byte fixture, not a video"
            (root / "clip.mp4").write_bytes(content)
            row = sample(
                sampleId="dataset-p0_" + hashlib.sha256(content).hexdigest()[:12],
                rawPath="clip.mp4",
            )
            validate([row], dataset_root=root)
            with self.assertRaisesRegex(ManifestSchemaError, "hash mismatch"):
                validate(
                    [replace(row, sample_id="dataset-p0_ffffffffffff")],
                    dataset_root=root,
                )
            with self.assertRaisesRegex(ManifestSchemaError, "missing"):
                validate([replace(row, raw_path="absent.mp4")], dataset_root=root)

    def test_duplicate_content_under_different_source_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = b"synthetic content duplication fixture"
            (root / "a.mp4").write_bytes(content)
            (root / "b.mp4").write_bytes(content)
            suffix = hashlib.sha256(content).hexdigest()[:12]
            first = sample(sampleId="source-a_" + suffix, rawPath="a.mp4")
            second = sample(sampleId="source-b_" + suffix, rawPath="b.mp4")
            with self.assertRaisesRegex(ManifestSchemaError, "duplicate raw content"):
                validate([first, second], dataset_root=root)

    def test_mixed_assigned_and_unassigned_source_group_fails(self):
        with self.assertRaisesRegex(ManifestSchemaError, "recordingSessionId leakage"):
            validate(
                [sample(split="train"), sample(sampleId="dataset-p0_abcdef012345")]
            )

    def test_canonical_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream, fieldnames=MANIFEST_COLUMNS, lineterminator="\n"
                )
                writer.writeheader()
                writer.writerow(sample().to_csv_row())
            self.assertEqual(read_manifest_csv(path), [sample()])
            good = path.read_bytes()
            for bad in [
                b"\xef\xbb\xbf" + good,
                good.replace(b"\n", b"\r\n"),
                good.replace(b"sampleId", b"sampleIdTypo", 1),
                good[:-1],
            ]:
                path.write_bytes(bad)
                with self.assertRaises(ManifestSchemaError):
                    read_manifest_csv(path)

    def test_dataset_versions(self):
        for good in ["p0-v1", "pilot-v2", "pilot-reviewed-v12"]:
            self.assertEqual(validate_dataset_version(good), good)
        for bad in ["p0", "p0-v0", "p0-v01", "p0-v1 ", "../p0-v1"]:
            with self.assertRaises(ManifestSchemaError):
                validate_dataset_version(bad)

    def test_frozen_p0_registry(self):
        root = Path(__file__).resolve().parents[3]
        path = root / "data/manifests/p0-meanings.csv"
        raw = path.read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", raw)
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 10)
        self.assertEqual(
            {row["meaningId"] for row in rows},
            {
                "GIAY_TO",
                "DAU_BUNG",
                "SOT",
                "NHAN",
                "BAN",
                "CAM_ON",
                "GIUP_DO",
                "XIN_LOI",
                "DAU_DAU",
                "KHONG",
            },
        )
        self.assertTrue(
            all(
                row["priority"] == "P0"
                and row["active"] == "true"
                and row["category"] in {"basic", "medical", "administrative"}
                for row in rows
            )
        )


if __name__ == "__main__":
    unittest.main()
