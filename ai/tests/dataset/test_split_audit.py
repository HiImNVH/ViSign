"""ai/tests/dataset/test_split_audit.py: T056 isolation and exact-quota regressions."""

import contextlib
import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from visign_ai.dataset.create_splits import assign_groups, main, prepare_split
from visign_ai.dataset.manifest_schema import MANIFEST_COLUMNS, ManifestRow

REGISTRY = Path(__file__).resolve().parents[3] / "data/manifests/p0-meanings.csv"


def synthetic_rows(count=6):
    return [
        {
            "sampleId": f"fixture_{i:012x}",
            "meaningId": "CAM_ON",
            "classLabel": "CAM_ON_UNKNOWN_1",
            "recordingSessionId": f"fixture_{i:012x}",
            "signerId": "",
        }
        for i in range(count)
    ]


class SplitSolverTests(unittest.TestCase):
    def test_exact_and_reproducible(self):
        rows = synthetic_rows()
        quotas = {"CAM_ON": {"train": 3, "validation": 2, "test": 1}}
        first = assign_groups(rows, quotas)
        self.assertEqual(first["status"], "FEASIBLE")
        self.assertEqual(
            first["assignment"],
            assign_groups(list(reversed(rows)), quotas)["assignment"],
        )
        assigned = list(first["assignment"].values())
        self.assertEqual(
            [assigned.count(s) for s in ("train", "validation", "test")], [3, 2, 1]
        )

    def test_fewer_than_three_groups_is_infeasible(self):
        rows = synthetic_rows()
        for row in rows:
            row["recordingSessionId"] = "source-R01"
        self.assertEqual(
            assign_groups(rows, {"CAM_ON": {"train": 3, "validation": 2, "test": 1}})[
                "status"
            ],
            "INFEASIBLE",
        )

    def test_known_signer_preference_and_fallback_preserve_input(self):
        rows = synthetic_rows()
        for i, row in enumerate(rows):
            row["signerId"] = f"S{i // 2 + 1:03}"
        quotas = {"CAM_ON": {"train": 2, "validation": 2, "test": 2}}
        result = assign_groups(rows, quotas)
        self.assertEqual(result["signerPreference"], "satisfied-for-known-signers")
        for i in range(0, 6, 2):
            self.assertEqual(
                result["assignment"][rows[i]["sampleId"]],
                result["assignment"][rows[i + 1]["sampleId"]],
            )
        for row in rows:
            row["signerId"] = "S001"
        before = [dict(row) for row in rows]
        result = assign_groups(rows, quotas)
        self.assertEqual(result["status"], "FEASIBLE")
        self.assertEqual(result["signerPreference"], "fallback-to-source-video")
        self.assertEqual(rows, before)

    def test_multi_meaning_source_stays_together(self):
        rows = synthetic_rows(3)
        others = [
            {
                **r,
                "sampleId": r["sampleId"].replace("fixture_", "other_"),
                "meaningId": "NHAN",
                "classLabel": "NHAN_UNKNOWN_1",
            }
            for r in rows
        ]
        quotas = {
            m: {"train": 1, "validation": 1, "test": 1} for m in ("CAM_ON", "NHAN")
        }
        assignment = assign_groups(rows + others, quotas)["assignment"]
        for first, second in zip(rows, others, strict=True):
            self.assertEqual(
                assignment[first["sampleId"]], assignment[second["sampleId"]]
            )

    def test_rare_variant_cannot_disappear_from_evaluation(self):
        rows = synthetic_rows()
        rows[0]["classLabel"] = "CAM_ON_UNKNOWN_2"
        result = assign_groups(
            rows, {"CAM_ON": {"train": 3, "validation": 2, "test": 1}}
        )
        self.assertEqual(result["status"], "INFEASIBLE")

    def test_counts_wrong_and_invalid_quotas_are_not_rounded(self):
        self.assertEqual(
            assign_groups(
                synthetic_rows(), {"CAM_ON": {"train": 12, "validation": 5, "test": 3}}
            )["status"],
            "INFEASIBLE",
        )
        with self.assertRaises(ValueError):
            assign_groups(
                synthetic_rows(),
                {"CAM_ON": {"train": True, "validation": 2, "test": 3}},
            )

    def test_search_limit_is_distinct_from_infeasible(self):
        result = assign_groups(
            synthetic_rows(),
            {"CAM_ON": {"train": 3, "validation": 2, "test": 1}},
            max_states=1,
        )
        self.assertEqual(result["status"], "SEARCH_LIMIT")

    def test_large_groups_cannot_be_split_to_fill_quota(self):
        rows = synthetic_rows(6)
        for i, row in enumerate(rows):
            row["recordingSessionId"] = f"source-R{i // 2 + 1:02}"
        self.assertEqual(
            assign_groups(rows, {"CAM_ON": {"train": 3, "validation": 2, "test": 1}})[
                "status"
            ],
            "INFEASIBLE",
        )


class SplitPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = self.root / "input.csv"
        self.classes = self.root / "classes.csv"
        self.quotas = self.root / "quotas.json"
        self.output = self.root / "output.csv"
        self.report = self.root / "report.json"
        self.rows = []
        self.build({"CAM_ON": (3, 2, 1)}, known_signers=False)

    def write_rows(self):
        with self.manifest.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=MANIFEST_COLUMNS, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(self.rows)

    def build(self, targets, *, known_signers):
        self.rows = []
        catalog = ["classLabel,meaningId,region,variantName,verified,active"]
        quotas = {}
        for meaning, allocation in targets.items():
            label = meaning + "_UNKNOWN_1"
            catalog.append(f"{label},{meaning},UNKNOWN,1,true,true")
            quotas[meaning] = dict(
                zip(("train", "validation", "test"), allocation, strict=True)
            )
            for split_index, count in enumerate(allocation):
                for i in range(count):
                    raw = f"synthetic {meaning} {split_index} {i}".encode()
                    sample_id = "fixture_" + hashlib.sha256(raw).hexdigest()[:12]
                    (self.root / (sample_id + ".mp4")).write_bytes(raw)
                    self.rows.append(
                        ManifestRow.from_mapping(
                            {
                                "sampleId": sample_id,
                                "classLabel": label,
                                "meaningId": meaning,
                                "signerId": f"S{split_index + 1:03}"
                                if known_signers
                                else "",
                                "recordingSessionId": sample_id,
                                "sourceUri": "dataset:synthetic",
                                "licenseStatus": "approved",
                                "verificationStatus": "verified",
                                "rejectionReason": "",
                                "rawPath": sample_id + ".mp4",
                                "landmarkPath": "",
                                "durationMs": "1000",
                                "frameCount": "30",
                                "split": "",
                            }
                        ).to_csv_row()
                    )
        self.classes.write_text(
            "\n".join(catalog) + "\n", encoding="utf-8", newline="\n"
        )
        self.quotas.write_text(json.dumps(quotas), encoding="utf-8")
        self.write_rows()

    def args(self, mode="pilot"):
        args = [
            "--manifest",
            str(self.manifest),
            "--registry",
            str(REGISTRY),
            "--classes",
            str(self.classes),
            "--dataset-root",
            str(self.root),
            "--output",
            str(self.output),
            "--report",
            str(self.report),
            "--dataset-version",
            "fixture-v1",
            "--mode",
            mode,
        ]
        return args + (["--pilot-quotas", str(self.quotas)] if mode == "pilot" else [])

    def test_session_only_pilot_explicit_and_input_unchanged(self):
        before = self.manifest.read_bytes()
        self.assertEqual(main(self.args()), 0)
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(report["splitEvidence"], "video-held-out")
        self.assertFalse(report["modelDemoReady"])
        self.assertEqual(self.manifest.read_bytes(), before)
        output = self.output.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(self.args()), 1)
        self.assertEqual(self.output.read_bytes(), output)

    def test_full_video_held_out_200_pipeline(self):
        from visign_ai.dataset.meaning_registry import read_p0_meanings

        self.build(
            {m: (12, 5, 3) for m in read_p0_meanings(REGISTRY)}, known_signers=True
        )
        self.assertEqual(main(self.args("full")), 0)
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(report["splitEvidence"], "video-held-out")
        self.assertTrue(report["dataGatePassed"])

    def test_full_optional_signer_unverified_and_blank_source(self):
        from visign_ai.dataset.meaning_registry import read_p0_meanings

        self.build(
            {m: (12, 5, 3) for m in read_p0_meanings(REGISTRY)}, known_signers=False
        )
        for row in self.rows:
            row.update(verificationStatus="unverified", sourceUri="")
        self.write_rows()
        self.assertEqual(main(self.args("full")), 0)
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertTrue(report["dataGatePassed"])
        self.assertEqual(report["splitEvidence"], "video-held-out")
        with self.output.open(encoding="utf-8", newline="") as stream:
            output_rows = list(csv.DictReader(stream))
        self.assertEqual(len(output_rows), 200)
        self.assertTrue(
            all(
                r["verificationStatus"] == "unverified"
                and not r["signerId"]
                and not r["sourceUri"]
                for r in output_rows
            )
        )

    def test_rejected_sample_blocks_split_without_output(self):
        self.rows[0].update(
            verificationStatus="rejected", rejectionReason="wrong label"
        )
        self.write_rows()
        self.assertEqual(main(self.args()), 1)
        self.assertFalse(self.output.exists())
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(report["issues"]["SAMPLE_NOT_APPROVED"], 1)

    def test_unverified_samples_preserved_in_manifest(self):
        self.rows[0]["verificationStatus"] = "unverified"
        self.write_rows()
        self.assertEqual(main(self.args()), 0)
        with self.output.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[0]["verificationStatus"], "unverified")

    def test_missing_p0_coverage_blocks_full_before_assignment(self):
        report, assigned = prepare_split(
            self.manifest, REGISTRY, self.classes, self.root, mode="full"
        )
        self.assertEqual(report["issues"]["MISSING_P0_COVERAGE"], 1)
        self.assertNotIn("MISSING_SIGNER_ID", report["issues"])
        self.assertFalse(assigned)

    def test_hash_mismatch_cannot_produce_manifest(self):
        (self.root / self.rows[0]["rawPath"]).write_bytes(b"changed")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(self.args()), 1)
        self.assertFalse(self.output.exists())

    def test_review_package_is_not_a_training_manifest(self):
        from visign_ai.dataset.review_package import build_package

        self.rows[0]["verificationStatus"] = "unverified"
        self.write_rows()
        output = self.root / "review"
        summary = build_package(
            self.manifest, REGISTRY, self.classes, self.root, output
        )
        self.assertFalse(summary["fullTrainingEligible"])
        self.assertFalse(summary["approvedPilotManifestCreated"])
        self.assertFalse((output / "pilot.csv").exists())
        self.assertFalse((output / "p0.csv").exists())
        with (output / "sample-review.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 6)
        self.assertTrue(
            all(
                row["expertLabelDecision"] == ""
                and row["decision"] == "pending"
                and row["reviewer"] == ""
                and row["rightsEvidenceReference"] == ""
                for row in rows
            )
        )
        with self.assertRaises(ValueError):
            build_package(self.manifest, REGISTRY, self.classes, self.root, output)


if __name__ == "__main__":
    unittest.main()
