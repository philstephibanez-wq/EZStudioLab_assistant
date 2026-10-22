import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_physical_documents import extract_printed_credit_candidates, inspect_scans_with_local_ocr


class PhysicalOcrV16a7(unittest.TestCase):
    def test_track_specific_lines_remain_unverified(self):
        sample = "Album credits\n\nWish You Were Here\nDavid Gilmour: acoustic guitar\nRoger Waters - bass guitar\n\nNext song\nNick Mason: drums"
        candidates = extract_printed_credit_candidates(sample, "Wish You Were Here")
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["musician"], "David Gilmour")
        self.assertTrue(all(x["evidence_eligible"] is False for x in candidates))

    def test_album_wide_credit_is_not_track_evidence(self):
        self.assertEqual(extract_printed_credit_candidates(
            "Album credits\nDavid Gilmour: acoustic guitar", "Wish You Were Here"), [])

    def test_ambiguous_duplicate_heading_is_rejected(self):
        self.assertEqual(extract_printed_credit_candidates(
            "Wish You Were Here\nDavid Gilmour: guitar\nWish You Were Here\nRoger Waters: bass",
            "Wish You Were Here"), [])

    def test_opt_in_is_required(self):
        with patch.dict("os.environ", {"EZS_PROFILE_BOOKLET_OCR": "0"}):
            self.assertEqual(inspect_scans_with_local_ocr([], "Wish You Were Here")["status"], "disabled")


if __name__ == "__main__":
    unittest.main()
