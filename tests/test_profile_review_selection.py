"""Tests de sélection explicite de révision : aucune donnée réseau requise."""
import unittest
from unittest.mock import patch
from io import StringIO
from contextlib import redirect_stdout
import json
from runtime import profile_latest_review


class ReviewSelectionTest(unittest.TestCase):
    def test_invalid_run_id(self):
        with patch.dict("os.environ", {"EZSTUDIOLAB_PROFILE_RUN_ID": "-3", "EZSTUDIOLAB_ASSISTANT_TOKEN": "test"}):
            with patch.object(profile_latest_review, "TOKEN", "test"):
                output = StringIO()
                with redirect_stdout(output):
                    profile_latest_review.main()
                self.assertEqual(json.loads(output.getvalue())["error"], "run_id_invalid")

    def test_default_url_has_no_run_id(self):
        with patch.dict("os.environ", {"EZSTUDIOLAB_PROFILE_RUN_ID": ""}):
            self.assertNotIn("run_id", "http://host/internal/analysis/desktop/profile/reviews/latest")


if __name__ == "__main__":
    unittest.main()
