import unittest
from dataclasses import replace

from visign_ai.dataset.entities import (
    Category,
    EntityValidationError,
    Meaning,
    Priority,
    Region,
    SignClass,
    validate_catalog,
)


class EntityTests(unittest.TestCase):
    def test_valid_entities_and_defaults(self):
        meaning = Meaning("CAM_ON", "Cảm ơn", Category.BASIC)
        cls = SignClass("CAM_ON_HN_2", "CAM_ON", Region.HN, "2")
        self.assertEqual(meaning.priority, Priority.P0)
        self.assertFalse(cls.verified)
        self.assertFalse(cls.active)
        self.assertEqual(validate_catalog([meaning], [cls])[1][cls.class_label], cls)

    def test_invalid_meaning(self):
        good = Meaning("CAM_ON", "Cảm ơn", Category.BASIC)
        for fields in [
            {"meaning_id": "cảm ơn"},
            {"display_text": " Cảm ơn"},
            {"display_text": ""},
            {"display_text": "Ca\u0309m ơn"},
            {"category": "admin"},
            {"priority": "P2"},
            {"active": "true"},
        ]:
            with self.subTest(fields=fields), self.assertRaises(EntityValidationError):
                replace(good, **fields)

    def test_invalid_class(self):
        good = SignClass("CAM_ON_HN_2", "CAM_ON", Region.HN, "2")
        for fields in [
            {"region": "NORTH"},
            {"variant_name": "02"},
            {"variant_name": "0"},
            {"class_label": "CAM_ON_HCM_2"},
            {"verified": "false"},
            {"active": 1},
        ]:
            with self.subTest(fields=fields), self.assertRaises(EntityValidationError):
                replace(good, **fields)

    def test_catalog_identity_and_references(self):
        meaning = Meaning("CAM_ON", "Cảm ơn", Category.BASIC)
        cls = SignClass("CAM_ON_HN_2", "CAM_ON", Region.HN, "2")
        for meanings, classes in [
            ([meaning, meaning], [cls]),
            ([meaning], [cls, cls]),
            ([], [cls]),
            ([replace(meaning, active=False)], [replace(cls, active=True)]),
        ]:
            with self.assertRaises(EntityValidationError):
                validate_catalog(meanings, classes)


if __name__ == "__main__":
    unittest.main()
