"""ai/tests/dataset/test_pilot_owner_assist.py: evidence reuse without fake approvals."""

import unittest

from visign_ai.dataset.pilot_owner_assist import attested_subset


class OwnerEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.row = {
            "sampleId": "fixture_0123456789ab",
            "classLabel": "NHAN_HCM_1",
            "sourceUri": "dataset:self-recorded",
            "licenseStatus": "approved",
            "signerId": "",
            "recordingSessionId": "fixture_0123456789ab",
            "verificationStatus": "unverified",
        }
        self.inv = {
            **self.row,
            "sourceReviewStatus": "user-confirmed-self-recorded",
            "sha256": "0123456789ab" + "0" * 52,
            "groupEvidence": "user-confirmed-independently-recorded-clip",
        }
        self.rights = {
            **self.row,
            "consentStatus": "user-declared-approved",
            "evidenceKind": "user-attestation-in-chat",
        }

    def test_records_prior_attestation_without_changing_label_or_identity(self):
        selected, decisions = attested_subset([self.row], [self.inv], [self.rights])
        self.assertEqual(selected, [self.row])
        self.assertIsNot(selected[0], self.row)
        self.assertEqual(selected[0]["verificationStatus"], "unverified")
        self.assertEqual(selected[0]["signerId"], "")
        self.assertFalse(decisions[0]["independentVerification"])

    def test_self_recorded_uri_alone_is_insufficient(self):
        selected, _ = attested_subset([self.row], [], [self.rights])
        self.assertFalse(selected)

    def test_website_clip_is_excluded_without_revoking_its_original_license(self):
        self.row["sourceUri"] = "https://example.org/clip.mp4"
        selected, decisions = attested_subset([self.row], [self.inv], [self.rights])
        self.assertFalse(selected)
        self.assertIn("external-source", decisions[0]["selectionReason"])
        self.assertEqual(self.row["licenseStatus"], "approved")

    def test_unknown_rights_or_missing_consent_does_not_get_approval(self):
        self.rights["consentStatus"] = "unknown"
        self.assertFalse(attested_subset([self.row], [self.inv], [self.rights])[0])

    def test_hash_group_or_label_mismatch_is_not_silently_repaired(self):
        for change in [
            {"sha256": "a" * 64},
            {"classLabel": "NHAN_HCM_2"},
            {"recordingSessionId": "new-source-R01"},
            {"signerId": "S002"},
            {"groupEvidence": "filename-only"},
        ]:
            with self.subTest(change=change):
                self.assertFalse(
                    attested_subset(
                        [self.row], [{**self.inv, **change}], [self.rights]
                    )[0]
                )

    def test_duplicate_evidence_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            attested_subset([self.row], [self.inv, self.inv], [self.rights])

    def test_rejected_sample_is_not_rescued_by_owner_attestation(self):
        self.row["verificationStatus"] = "rejected"
        selected, decisions = attested_subset([self.row], [self.inv], [self.rights])
        self.assertFalse(selected)
        self.assertEqual(
            decisions[0]["selectionReason"], "rejected-sample-not-selected"
        )
