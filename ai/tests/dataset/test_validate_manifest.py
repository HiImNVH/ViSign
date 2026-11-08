"""Synthetic metadata fixtures only: these are not training data."""

import contextlib
import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from visign_ai.dataset.manifest_schema import MANIFEST_COLUMNS, ManifestRow
from visign_ai.dataset.validate_manifest import audit, main

REGISTRY = Path(__file__).resolve().parents[3] / "data/manifests/p0-meanings.csv"


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.classes = self.root / "classes.csv"
        self.classes.write_text(
            "classLabel,meaningId,region,variantName,verified,active\n"
            "CAM_ON_HN_2,CAM_ON,HN,2,false,false\n",
            encoding="utf-8",
            newline="\n",
        )
        self.path = self.root / "manifest.csv"
        self.row = ManifestRow(
            sample_id="dataset-p0_0123456789ab",
            class_label="CAM_ON_HN_2",
            meaning_id="CAM_ON",
            recording_session_id="dataset-p0_0123456789ab",
            license_status="unknown",
            verification_status="unverified",
            raw_path="clip.mp4",
            duration_ms=1000,
            frame_count=30,
        ).to_csv_row()

    def write(self, rows):
        with self.path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=MANIFEST_COLUMNS, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)

    def test_audit_coverage_includes_zero_classes_and_unknown_signer(self):
        self.write([self.row])
        report = audit(self.path, REGISTRY, self.classes)
        self.assertTrue(report["valid"])
        self.assertEqual(report["coverage"]["total"]["missingSignerCount"], 1)
        self.assertEqual(report["coverage"]["byMeaning"]["GIAY_TO"]["sampleCount"], 0)
        self.assertEqual(report["coverage"]["releaseExcludedCount"], 1)
        self.assertFalse(report["releaseEligible"])
        self.assertEqual(report["hashAudit"], "NOT_RUN")

    def test_duplicate_or_unknown_class_fails(self):
        self.write([self.row, self.row])
        self.assertFalse(audit(self.path, REGISTRY, self.classes)["valid"])
        self.write([{**self.row, "classLabel": "CAM_ON_HN_99"}])
        self.assertFalse(audit(self.path, REGISTRY, self.classes)["valid"])

    def test_inventory_cannot_claim_release(self):
        fields = dict(self.row, sha256="0123456789ab" + "0" * 52)
        fields.update(rawPath="", durationMs="", frameCount="")
        with self.path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=list(fields), lineterminator="\n"
            )
            writer.writeheader()
            writer.writerow(fields)
        report = audit(self.path, REGISTRY, self.classes, inventory=True)
        self.assertTrue(report["valid"])
        self.assertEqual(report["pendingMetadataCounts"]["durationMs"], 1)
        self.assertFalse(
            audit(self.path, REGISTRY, self.classes, inventory=True, for_release=True)[
                "valid"
            ]
        )

    def test_manifest_hash_audit(self):
        content = b"synthetic byte fixture only"
        (self.root / "clip.mp4").write_bytes(content)
        self.write(
            [
                {
                    **self.row,
                    "sampleId": "dataset-p0_"
                    + hashlib.sha256(content).hexdigest()[:12],
                }
            ]
        )
        self.assertTrue(
            audit(self.path, REGISTRY, self.classes, dataset_root=self.root)["valid"]
        )
        (self.root / "clip.mp4").write_bytes(b"tampered")
        self.assertFalse(
            audit(self.path, REGISTRY, self.classes, dataset_root=self.root)["valid"]
        )

    def test_lead_source_session_has_inventory_manifest_parity(self):
        row = {**self.row, "recordingSessionId": "dataset-p0_0123456789ab"}
        self.write([row])
        self.assertTrue(audit(self.path, REGISTRY, self.classes)["valid"])
        fields = dict(row, sha256="0123456789ab" + "0" * 52)
        with self.path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=list(fields), lineterminator="\n"
            )
            writer.writeheader()
            writer.writerow(fields)
        self.assertTrue(
            audit(self.path, REGISTRY, self.classes, inventory=True)["valid"]
        )

    def test_cli_exit_status_and_no_overwrite(self):
        self.write([self.row])
        report_path = self.root / "report.json"
        args = [
            "--manifest",
            str(self.path),
            "--registry",
            str(REGISTRY),
            "--classes",
            str(self.classes),
            "--report",
            str(report_path),
        ]
        self.assertEqual(main(args), 0)
        self.assertTrue(json.loads(report_path.read_text(encoding="utf-8"))["valid"])
        before = report_path.read_bytes()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(args), 1)
        self.assertEqual(report_path.read_bytes(), before)
        self.write([self.row, self.row])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(args[:-2]), 1)

    def test_invalid_class_catalog_and_csv_header(self):
        self.write([self.row])
        self.classes.write_text(
            "classLabel,meaningId,region,variantName,verified,active\n"
            "CAM_ON_HN_2,CAM_ON,HN,2,FALSE,false\n",
            encoding="utf-8",
            newline="\n",
        )
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(
                main(
                    [
                        "--manifest",
                        str(self.path),
                        "--registry",
                        str(REGISTRY),
                        "--classes",
                        str(self.classes),
                    ]
                ),
                1,
            )

    def test_release_requires_active_classes_all_meanings_and_root(self):
        self.write([{**self.row, "licenseStatus": "approved", "split": "train"}])
        report = audit(self.path, REGISTRY, self.classes, for_release=True)
        self.assertFalse(report["valid"])
        self.assertFalse(report["releaseEligible"])

    def test_all_train_cannot_pass_release_even_with_all_meanings(self):
        from visign_ai.dataset.meaning_registry import read_p0_meanings

        meanings = read_p0_meanings(REGISTRY)
        classes = ["classLabel,meaningId,region,variantName,verified,active"]
        rows = []
        for index, meaning_id in enumerate(meanings):
            content = f"synthetic fixture {index}".encode()
            filename = f"clip{index}.mp4"
            (self.root / filename).write_bytes(content)
            sample_id = "fixture_" + hashlib.sha256(content).hexdigest()[:12]
            label = meaning_id + "_UNKNOWN_1"
            classes.append(f"{label},{meaning_id},UNKNOWN,1,true,true")
            rows.append(
                {
                    **self.row,
                    "sampleId": sample_id,
                    "recordingSessionId": sample_id,
                    "meaningId": meaning_id,
                    "classLabel": label,
                    "rawPath": filename,
                    "licenseStatus": "approved",
                    "split": "train",
                }
            )
        self.classes.write_text(
            "\n".join(classes) + "\n", encoding="utf-8", newline="\n"
        )
        self.write(rows)
        report = audit(
            self.path, REGISTRY, self.classes, dataset_root=self.root, for_release=True
        )
        self.assertFalse(report["valid"])
        self.assertFalse(report["releaseEligible"])
        self.assertIn(
            "MISSING_CLASS_SPLITS", {error["code"] for error in report["errors"]}
        )
        self.assertFalse(report["modelDemoReady"])

    def training_fixture(self, allocations):
        classes = ["classLabel,meaningId,region,variantName,verified,active"]
        rows = []
        for meaning_id, splits in allocations.items():
            label = meaning_id + "_UNKNOWN_1"
            classes.append(f"{label},{meaning_id},UNKNOWN,1,true,true")
            for index, split in enumerate(splits):
                filename = f"{meaning_id}-{index}.mp4"
                content = f"synthetic {meaning_id} {index}".encode()
                (self.root / filename).write_bytes(content)
                sample_id = "fixture_" + hashlib.sha256(content).hexdigest()[:12]
                rows.append(
                    {
                        **self.row,
                        "sampleId": sample_id,
                        "recordingSessionId": sample_id,
                        "meaningId": meaning_id,
                        "classLabel": label,
                        "rawPath": filename,
                        "licenseStatus": "approved",
                        "verificationStatus": "verified",
                        "sourceUri": "dataset:synthetic-fixture",
                        "split": split,
                    }
                )
        self.classes.write_text(
            "\n".join(classes) + "\n", encoding="utf-8", newline="\n"
        )
        self.write(rows)

    def test_complete_per_class_splits_can_pass_metadata_gate(self):
        from visign_ai.dataset.meaning_registry import read_p0_meanings

        self.training_fixture(
            {key: ["train", "validation", "test"] for key in read_p0_meanings(REGISTRY)}
        )
        report = audit(
            self.path, REGISTRY, self.classes, dataset_root=self.root, for_release=True
        )
        self.assertTrue(report["valid"])
        self.assertTrue(report["releaseEligible"])
        self.assertFalse(report["modelDemoReady"])
        self.assertFalse(report["fullQualityGateEvaluated"])

    def test_pilot_training_checks_each_selected_class_not_only_global_split_names(
        self,
    ):
        self.training_fixture(
            {"CAM_ON": ["train", "validation", "test"], "NHAN": ["train"]}
        )
        report = audit(
            self.path, REGISTRY, self.classes, dataset_root=self.root, for_training=True
        )
        self.assertFalse(report["trainingEligible"])
        self.assertEqual(
            report["classSplitCoverage"]["NHAN_UNKNOWN_1"]["missingSplits"],
            ["test", "validation"],
        )
        self.training_fixture({"CAM_ON": ["train", "validation", "test"]})
        report = audit(
            self.path,
            REGISTRY,
            self.classes,
            dataset_root=self.root,
            for_training=True,
            selected_classes={"CAM_ON_UNKNOWN_1"},
        )
        self.assertTrue(report["valid"])
        self.assertTrue(report["trainingEligible"])
        self.assertFalse(report["releaseEligible"])

    def test_missing_or_unknown_selected_class_is_blocked(self):
        self.training_fixture({"CAM_ON": ["train", "validation", "test"]})
        report = audit(
            self.path,
            REGISTRY,
            self.classes,
            dataset_root=self.root,
            for_training=True,
            selected_classes={"CAM_ON_UNKNOWN_1", "MISSING_HN_1"},
        )
        self.assertFalse(report["valid"])
        self.assertIn(
            "UNKNOWN_SELECTED_CLASS", {error["code"] for error in report["errors"]}
        )
        self.training_fixture({"CAM_ON": ["train", "validation", "test"], "NHAN": []})
        report = audit(
            self.path,
            REGISTRY,
            self.classes,
            dataset_root=self.root,
            for_training=True,
            selected_classes={"CAM_ON_UNKNOWN_1", "NHAN_UNKNOWN_1"},
        )
        self.assertFalse(report["valid"])
        self.assertEqual(
            len(report["classSplitCoverage"]["NHAN_UNKNOWN_1"]["missingSplits"]), 3
        )

    def full_fixture(self):
        from visign_ai.dataset.meaning_registry import read_p0_meanings

        self.training_fixture(
            {
                key: ["train"] * 12 + ["validation"] * 5 + ["test"] * 3
                for key in read_p0_meanings(REGISTRY)
            }
        )
        from visign_ai.dataset.validate_manifest import read_csv

        rows = read_csv(self.path)
        for row in rows:
            row["signerId"] = {"train": "S001", "validation": "S002", "test": "S003"}[
                row["split"]
            ]
        self.write(rows)
        return rows

    def training_report(self, *, full=False):
        return audit(
            self.path,
            REGISTRY,
            self.classes,
            dataset_root=self.root,
            **({"for_full_training": True} if full else {"for_training": True}),
        )

    def test_full_200_12_5_3_with_session_isolation_passes_data_gate_only(self):
        self.full_fixture()
        report = self.training_report(full=True)
        self.assertTrue(report["trainingEligible"], report["errors"])
        self.assertEqual(report["trainingMode"], "full")
        self.assertEqual(report["labelAndLicenseApprovedCount"], 200)
        self.assertEqual(report["hashAudit"], "PASSED")
        self.assertEqual(report["hashAuditDetails"]["passed"], 200)
        self.assertFalse(report["modelDemoReady"])
        self.assertFalse(report["fullQualityGateEvaluated"])

    def test_pilot_cannot_be_used_to_bypass_full_gate(self):
        self.full_fixture()
        self.assertIn("PILOT_MEANING_LIMIT", self.training_report()["errorCounts"])

    def test_equal_total_200_with_wrong_meaning_split_is_blocked(self):
        rows = self.full_fixture()
        changed = next(row for row in rows if row["split"] == "validation")
        changed.update(split="train", signerId="S001")
        self.write(rows)
        report = self.training_report(full=True)
        errors = [e for e in report["errors"] if e["code"] == "MEANING_SPLIT_QUOTA"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["missing"]["validation"], 1)
        self.assertEqual(errors[0]["excess"]["train"], 1)
        self.assertFalse(report["trainingEligible"])

    def test_no_fake_approval_from_active_flag_or_global_split_totals(self):
        self.training_fixture({"CAM_ON": ["train", "validation", "test"]})
        from visign_ai.dataset.validate_manifest import read_csv

        rows = read_csv(self.path)
        rows[0]["verificationStatus"] = "unverified"
        rows[1]["licenseStatus"] = "unknown"
        self.write(rows)
        self.classes.write_text(
            self.classes.read_text().replace("true,true", "false,true"),
            encoding="utf-8",
            newline="\n",
        )
        report = self.training_report()
        self.assertFalse(report["trainingEligible"])
        self.assertEqual(report["labelAndLicenseApprovedCount"], 0)
        self.assertTrue(
            {"SAMPLES_LICENSE_NOT_APPROVED", "CLASS_NOT_VERIFIED"}
            <= report["errorCounts"].keys()
        )

    def test_full_optional_signer_and_source_video_leakage(self):
        rows = self.full_fixture()
        rows[0]["signerId"] = ""
        self.write(rows)
        self.assertTrue(self.training_report(full=True)["trainingEligible"])
        rows[0]["signerId"] = "S002"
        self.write(rows)
        self.assertTrue(self.training_report(full=True)["trainingEligible"])
        rows[0]["recordingSessionId"] = next(
            row["recordingSessionId"] for row in rows if row["split"] == "test"
        )
        self.write(rows)
        self.assertIn("SPLIT_LEAKAGE", self.training_report(full=True)["errorCounts"])

    def test_two_samples_cannot_cover_three_class_splits(self):
        self.training_fixture({"CAM_ON": ["train", "validation"]})
        report = self.training_report()
        stats = report["classSplitCoverage"]["CAM_ON_UNKNOWN_1"]
        self.assertTrue(stats["reassignmentAloneRuledOut"])
        self.assertEqual(stats["minimumAdditionalIndependentGroups"], 1)
        self.assertEqual(
            report["collectionPlan"]["classSplitRequirements"][0]["split"], "test"
        )

    def test_distinct_sessions_of_same_signer_are_independent(self):
        self.training_fixture({"CAM_ON": ["train"] * 5})
        from visign_ai.dataset.validate_manifest import read_csv

        rows = read_csv(self.path)
        for row in rows:
            row["signerId"] = "S001"
        self.write(rows)
        stats = self.training_report()["classSplitCoverage"]["CAM_ON_UNKNOWN_1"]
        self.assertEqual(stats["potentialIndependentGroupCount"], 5)
        self.assertEqual(stats["minimumAdditionalIndependentGroups"], 0)

    def test_approved_educational_source_may_omit_uri(self):
        self.training_fixture({"CAM_ON": ["train", "validation", "test"]})
        self.path.write_text(
            self.path.read_text().replace("dataset:synthetic-fixture", ""),
            encoding="utf-8",
            newline="\n",
        )
        self.assertTrue(self.training_report()["trainingEligible"])

    def test_hash_audit_continues_after_bad_file(self):
        self.training_fixture({"CAM_ON": ["train", "validation", "test"]})
        (self.root / "CAM_ON-0.mp4").write_bytes(b"tampered")
        (self.root / "CAM_ON-1.mp4").unlink()
        report = self.training_report()
        self.assertEqual(report["hashAudit"], "FAILED")
        self.assertEqual(report["hashAuditDetails"]["checked"], 3)
        self.assertEqual(report["hashAuditDetails"]["passed"], 1)
        self.assertTrue(
            {"RAW_HASH_MISMATCH", "RAW_FILE_MISSING_OR_UNSAFE"}
            <= report["errorCounts"].keys()
        )
        self.assertFalse(report["trainingEligible"])

    def test_incompatible_training_modes_are_rejected_by_api_and_cli(self):
        self.write([self.row])
        with self.assertRaisesRegex(ValueError, "choose exactly one gate"):
            audit(
                self.path,
                REGISTRY,
                self.classes,
                for_training=True,
                for_full_training=True,
            )
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(
                [
                    "--manifest",
                    str(self.path),
                    "--classes",
                    str(self.classes),
                    "--for-training",
                    "--for-full-training",
                ]
            )

    def test_full_target_cannot_override_inactive_classes_or_missing_raw_root(self):
        self.full_fixture()
        report = audit(self.path, REGISTRY, self.classes, for_full_training=True)
        self.assertFalse(report["trainingEligible"])
        self.assertIn("RELEASE_INPUT_REQUIRED", report["errorCounts"])
        self.classes.write_text(
            self.classes.read_text().replace("true,true", "true,false"),
            encoding="utf-8",
            newline="\n",
        )
        report = self.training_report(full=True)
        self.assertFalse(report["trainingEligible"])
        self.assertEqual(report["errorCounts"]["CLASS_INACTIVE"], 200)
        self.assertEqual(report["labelAndLicenseApprovedCount"], 0)

    def test_only_source_session_links_groups_across_meanings(self):
        from visign_ai.dataset.validate_manifest import independent_group_ids

        rows = [
            {"sampleId": "a", "recordingSessionId": "session-1", "signerId": "S001"},
            {"sampleId": "b", "recordingSessionId": "session-2", "signerId": "S002"},
            {"sampleId": "c", "recordingSessionId": "session-1", "signerId": "S002"},
        ]
        self.assertEqual(len(set(independent_group_ids(rows).values())), 2)

    def test_duplicate_bytes_under_another_source_id_block_training(self):
        self.training_fixture({"CAM_ON": ["train", "validation", "test"]})
        from visign_ai.dataset.validate_manifest import read_csv

        rows = read_csv(self.path)
        rows[1]["rawPath"] = rows[0]["rawPath"]
        rows[1]["sampleId"] = rows[0]["sampleId"].replace("fixture_", "other-source_")
        self.write(rows)
        report = self.training_report()
        self.assertFalse(report["trainingEligible"])
        self.assertEqual(report["errorCounts"]["DUPLICATE_RAW_CONTENT"], 1)

    def test_cli_full_gate_writes_failure_report_with_collection_plan(self):
        self.training_fixture({"CAM_ON": ["train", "validation", "test"]})
        report_path = self.root / "full-report.json"
        self.assertEqual(
            main(
                [
                    "--manifest",
                    str(self.path),
                    "--registry",
                    str(REGISTRY),
                    "--classes",
                    str(self.classes),
                    "--dataset-root",
                    str(self.root),
                    "--for-full-training",
                    "--report",
                    str(report_path),
                ]
            ),
            1,
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["trainingMode"], "full")
        self.assertIn("MEANING_SPLIT_QUOTA", report["errorCounts"])
        self.assertEqual(report["collectionPlan"]["missingBySplit"]["train"], 119)


if __name__ == "__main__":
    unittest.main()
