import unittest
from dataclasses import replace

from visign_ai.dataset.entities import DataSplit, LicenseStatus, VerificationStatus
from visign_ai.dataset.manifest_schema import ManifestRow, ManifestSchemaError


class ManifestSchemaTests(unittest.TestCase):
    def row(self):
        return ManifestRow(
            sample_id="dataset-p0_0123456789ab", class_label="CAM_ON_HN_2",
            meaning_id="CAM_ON", recording_session_id="dataset-p0_0123456789ab",
            license_status=LicenseStatus.UNKNOWN, verification_status=VerificationStatus.UNVERIFIED,
            raw_path="reviewed/dataset-p0/sample.mp4", duration_ms=1000, frame_count=30,
        )

    def test_optional_metadata_and_roundtrip(self):
        row = self.row()
        self.assertIsNone(row.signer_id)
        self.assertIsNone(row.source_uri)
        self.assertIsNone(row.split)
        self.assertIsInstance(row.license_status, LicenseStatus)
        self.assertEqual(row, ManifestRow.from_mapping(row.to_csv_row()))
        self.assertIs(replace(row, split="test").split, DataSplit.TEST)

    def test_strict_numeric_direct_construction(self):
        for fields in [{"duration_ms": "1000"}, {"frame_count": True}, {"frame_count": 0}]:
            with self.subTest(fields=fields), self.assertRaises(ManifestSchemaError):
                replace(self.row(), **fields)

    def test_required_session_and_unknown_column(self):
        data = self.row().to_csv_row()
        del data["recordingSessionId"]
        with self.assertRaises(ManifestSchemaError):
            ManifestRow.from_mapping(data)
        data = self.row().to_csv_row()
        data["typo"] = "value"
        with self.assertRaises(ManifestSchemaError):
            ManifestRow.from_mapping(data)


if __name__ == "__main__":
    unittest.main()
