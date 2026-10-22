"""Regression: PROFILE always provides an explicit web investigation status."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
class WebResearchActivation(unittest.TestCase):
    def test_no_hidden_opt_in(self):
        text=(ROOT/"runtime/profile_ai_requests_worker.py").read_text(encoding="utf-8")
        self.assertIn("investigation = research_each_assertion(row, ident)",text)
        self.assertNotIn('if os.getenv("EZS_PROFILE_WEB_INVESTIGATION"',text)
        self.assertIn("verification['web_investigation'] = investigation",text)
    def test_credentials_missing_is_declared_not_silenced(self):
        import sys
        sys.path.insert(0,str(ROOT/"app"))
        from profile_web_investigator import research_each_assertion
        row={"metrics":{"tempo":{"bpm":120}}}
        result=research_each_assertion(row,{"title":"private song","artist":"private author"},api_key="")
        self.assertEqual(result["status"],"unavailable")
        self.assertEqual(result["reason"],"web_provider_credentials_missing")
        self.assertEqual(result["items"][0]["status"],"not_searched")
if __name__=="__main__":unittest.main()
