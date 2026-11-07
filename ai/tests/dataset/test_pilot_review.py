"""ai/tests/dataset/test_pilot_review.py: T076 candidate preparation boundaries."""

import csv
import json
import unittest

import test_split_audit as fixtures
from visign_ai.dataset.pilot_review import build_pilot_review


class PilotReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.SplitPipelineTests("test_session_only_pilot_explicit_and_input_unchanged")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        for index, row in enumerate(self.fixture.rows):
            row["split"] = "train" if index < 3 else "validation" if index < 5 else "test"
        self.fixture.write_rows()
        self.output = self.fixture.root / "pilot-review"

    def build(self, meanings=None):
        return build_pilot_review(self.fixture.manifest, fixtures.REGISTRY, self.fixture.classes,
                                  self.fixture.root, self.output, meanings or {"CAM_ON"})

    def test_pending_candidates_remain_unapproved(self):
        self.fixture.rows[0]["verificationStatus"] = "unverified"
        self.fixture.write_rows()
        before = self.fixture.manifest.read_bytes()
        report = self.build()
        self.assertEqual(report["candidateCount"], 6)
        self.assertTrue(report["pilotDataGatePassed"])
        self.assertFalse(report["approvedPilotManifestCreated"])
        self.assertFalse((self.output / "pilot.csv").exists())
        self.assertEqual(self.fixture.manifest.read_bytes(), before)
        with (self.output / "sample-review.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertTrue(all(not r["labelDecision"] and not r["rightsDecision"]
                            and r["decision"] == "pending" and not r["reviewer"] for r in rows))
        with (self.output / "pilot.candidates.DRAFT.csv").open(encoding="utf-8", newline="") as stream:
            self.assertEqual(list(csv.DictReader(stream)), self.fixture.rows)

    def test_verified_fixture_can_pass_data_gate_but_not_model_gate(self):
        report = self.build()
        self.assertTrue(report["pilotDataGatePassed"])
        self.assertEqual(report["structuralSplitFeasibility"]["status"], "FEASIBLE")
        self.assertFalse(report["modelDemoReady"])
        self.assertFalse(report["schemaApprovalChecked"])
        self.assertFalse(report["approvedPilotManifestCreated"])

    def test_selection_cannot_exceed_three_or_use_missing_meaning(self):
        for meanings in [{"CAM_ON", "NHAN", "SOT", "GIAY_TO"}, {"NOT_P0"}, {"NHAN"}]:
            with self.subTest(meanings=meanings), self.assertRaises(ValueError):
                self.build(meanings)
        self.assertFalse(self.output.exists())

    def test_unassigned_or_leaking_split_requires_resolution(self):
        self.fixture.rows[0]["split"] = ""
        self.fixture.write_rows()
        with self.assertRaises(ValueError):
            self.build()
        self.fixture.rows[0]["split"] = "train"
        self.fixture.rows[1]["recordingSessionId"] = self.fixture.rows[-1]["recordingSessionId"]
        self.fixture.write_rows()
        with self.assertRaises(ValueError):
            self.build()

    def test_invalid_hash_aborts_before_creating_review_output(self):
        (self.fixture.root / self.fixture.rows[0]["rawPath"]).write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.output.exists())

    def test_no_overwrite_and_quotas_are_reproducible(self):
        self.build()
        before = (self.output / "summary.json").read_bytes()
        quotas = json.loads((self.output / "pilot-quotas.json").read_text(encoding="utf-8"))
        self.assertEqual(quotas, {"CAM_ON": {"train": 3, "validation": 2, "test": 1}})
        with self.assertRaises(ValueError):
            self.build()
        self.assertEqual((self.output / "summary.json").read_bytes(), before)
