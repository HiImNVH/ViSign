"""T013 regression checks for the approved vocabulary and invalid registries."""

import tempfile
import unicodedata
import unittest
from pathlib import Path

from visign_ai.dataset.meaning_registry import MeaningRegistryError, read_p0_meanings

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "data/manifests/p0-meanings.csv"
EXPECTED = {
    "GIAY_TO": ("Giấy tờ (giấy)", "administrative"),
    "DAU_BUNG": ("Đau bụng", "medical"),
    "SOT": ("Sốt", "medical"),
    "NHAN": ("Nhận", "basic"),
    "BAN": ("Bạn", "basic"),
    "CAM_ON": ("Cảm ơn", "basic"),
    "GIUP_DO": ("Giúp đỡ", "basic"),
    "XIN_LOI": ("Xin lỗi", "basic"),
    "DAU_DAU": ("Đau đầu", "medical"),
    "KHONG": ("Không", "basic"),
}


class MeaningRegistryTests(unittest.TestCase):
    def test_exact_approved_labels_and_categories(self):
        registry = read_p0_meanings(REGISTRY)
        self.assertEqual(
            {
                key: (row["displayText"], row["category"])
                for key, row in registry.items()
            },
            EXPECTED,
        )
        self.assertNotEqual(registry["KHONG"]["displayText"], "Không nhận diện được")

    def assert_invalid(self, content: bytes):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.csv"
            path.write_bytes(content)
            with self.assertRaises(MeaningRegistryError):
                read_p0_meanings(path)

    def test_duplicate_ids_or_display_texts(self):
        raw = REGISTRY.read_bytes()
        self.assert_invalid(raw.replace(b"NHAN,", b"BAN,"))
        self.assert_invalid(raw.replace("NHAN,Nhận,".encode(), "NHAN,Bạn,".encode()))

    def test_missing_or_extra_meaning(self):
        raw = REGISTRY.read_bytes()
        self.assert_invalid(b"\n".join(raw.splitlines()[:-1]) + b"\n")
        self.assert_invalid(raw + "MO_RONG,Mở rộng,basic,P0,true\n".encode())

    def test_invalid_fields_and_enums(self):
        raw = REGISTRY.read_bytes()
        for old, new in [
            (b"GIAY_TO,", b"giay_to,"),
            (b"administrative", b"admin"),
            (b",P0,", b",P1,"),
            (b",true", b",false"),
            (b",true", b",TRUE"),
            (b"GIAY_TO,", b"GIAY_TO, "),
        ]:
            with self.subTest(new=new):
                self.assert_invalid(raw.replace(old, new, 1))

    def test_encoding_and_header(self):
        raw = REGISTRY.read_bytes()
        for content in [
            b"\xef\xbb\xbf" + raw,
            raw.replace(b"\n", b"\r\n"),
            raw[:-1],
            raw.replace(b"category", b"wrongHeader", 1),
            b"\xff\n",
            unicodedata.normalize("NFD", raw.decode()).encode(),
        ]:
            with self.subTest(content=content[:30]):
                self.assert_invalid(content)

    def test_short_or_extra_csv_row(self):
        raw = REGISTRY.read_bytes()
        self.assert_invalid(raw.replace(b"administrative,P0,true", b"administrative"))
        self.assert_invalid(
            raw.replace(b"administrative,P0,true", b"administrative,P0,true,extra")
        )


if __name__ == "__main__":
    unittest.main()
