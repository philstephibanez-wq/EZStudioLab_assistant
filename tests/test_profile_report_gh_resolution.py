import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
import profile_report

class GitHubCliResolutionTests(unittest.TestCase):
    def test_missing_cli_fails_with_explicit_error(self):
        with patch.object(profile_report.shutil,"which",return_value=None), patch.object(profile_report.os,"name","posix"):
            with self.assertRaisesRegex(RuntimeError,"report_github_cli_not_found"):
                profile_report._gh("repos/test/test/contents/file.json")
    def test_path_cli_used_without_shell(self):
        class Result:
            returncode=0
            stdout=b"{}"
            stderr=b""
        with patch.object(profile_report.shutil,"which",return_value="C:/Program Files/GitHub CLI/gh.exe"), patch.object(profile_report.subprocess,"run",return_value=Result()) as run:
            profile_report._gh("repos/test/test/contents/file.json")
            self.assertEqual(run.call_args.args[0][0],"C:/Program Files/GitHub CLI/gh.exe")
            self.assertEqual(run.call_args.args[0][1],"api")
if __name__=="__main__":
    unittest.main()
