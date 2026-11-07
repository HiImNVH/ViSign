import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from visign_ai.dataset.manifest_handoff import export_paths, merge_landmarks
from visign_ai.dataset.manifest_schema import (
    MANIFEST_COLUMNS,
    ManifestRow,
    ManifestSchemaError,
    read_manifest_csv,
)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        content = b"synthetic fixture only"
        (self.root / "clip.mp4").write_bytes(content)
        self.row = ManifestRow(
            sample_id="fixture_" + hashlib.sha256(content).hexdigest()[:12],
            class_label="CAM_ON_HN_2", meaning_id="CAM_ON",
            recording_session_id="fixture_" + hashlib.sha256(content).hexdigest()[:12],
            license_status="approved", verification_status="verified", raw_path="clip.mp4",
            duration_ms=1000, frame_count=30,
        )
        self.manifest = self.root / "manifest.csv"
        with self.manifest.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=MANIFEST_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerow(self.row.to_csv_row())
        self.report = self.root / "validation.json"
        self.report.write_text(json.dumps({"valid": True, "inputKind": "manifest",
            "inputSha256": hashlib.sha256(self.manifest.read_bytes()).hexdigest()}), encoding="utf-8")

    def test_export_and_no_overwrite(self):
        output = self.root / "paths.csv"
        self.assertEqual(export_paths(self.manifest, self.report, self.root, output), 1)
        with output.open(encoding="utf-8", newline="") as stream:
            self.assertEqual(list(csv.DictReader(stream)),
                             [{"sampleId": self.row.sample_id, "rawPath": "clip.mp4"}])
        with self.assertRaises(FileExistsError):
            export_paths(self.manifest, self.report, self.root, output)

    def test_draft_export_requires_explicit_flag(self):
        with self.manifest.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=MANIFEST_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerow({**self.row.to_csv_row(), "licenseStatus": "unknown"})
        self.report.write_text(json.dumps({"valid": True, "inputKind": "manifest",
            "inputSha256": hashlib.sha256(self.manifest.read_bytes()).hexdigest()}), encoding="utf-8")
        with self.assertRaises(ManifestSchemaError):
            export_paths(self.manifest, self.report, self.root, self.root / "blocked.csv")
        self.assertEqual(export_paths(self.manifest, self.report, self.root, self.root / "draft.csv",
                                      allow_draft=True), 1)

    def test_stale_report_or_tampered_video_rejected(self):
        (self.root / "clip.mp4").write_bytes(b"changed bytes")
        with self.assertRaises(ManifestSchemaError):
            export_paths(self.manifest, self.report, self.root, self.root / "out.csv")
        self.report.write_text('{"valid":true,"inputKind":"manifest","inputSha256":"wrong"}', encoding="utf-8")
        with self.assertRaises(ManifestSchemaError):
            export_paths(self.manifest, self.report, self.root, self.root / "out.csv")

    def test_join_by_id_preserves_all_other_fields(self):
        relative = "processed/schema/" + self.row.sample_id + ".npz"
        artifact = self.root / relative
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"synthetic artifact path fixture; not a real tensor")
        output = self.root / "merged.csv"
        merge_landmarks(self.manifest, self.report, {self.row.sample_id: relative}, self.root, output)
        result = read_manifest_csv(output)[0].to_csv_row()
        before = self.row.to_csv_row()
        self.assertEqual(result.pop("landmarkPath"), relative)
        before.pop("landmarkPath")
        self.assertEqual(result, before)
        with self.assertRaises(ManifestSchemaError):
            merge_landmarks(self.manifest, self.report, {"unknown": relative}, self.root, self.root / "bad.csv")

    def test_unsafe_or_missing_artifact_rejected(self):
        for relative in ["../outside.npz", "processed/missing.npz"]:
            with self.assertRaises(ManifestSchemaError):
                merge_landmarks(self.manifest, self.report, {self.row.sample_id: relative},
                                self.root, self.root / "bad.csv")


if __name__ == "__main__":
    unittest.main()
