from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def compact(source: str) -> str:
    return "".join(source.split())


class AssistantWebArchitectureV13(unittest.TestCase):
    def test_stack_contract(self):
        req = json.loads((ROOT / "composer.json").read_text(encoding="utf-8"))["require"]
        for package in (
            "symfony/framework-bundle",
            "symfony/twig-bundle",
            "symfony/monolog-bundle",
            "symfony/process",
        ):
            self.assertIn(package, req)
        self.assertNotIn("doctrine/orm", req)
        self.assertNotIn("doctrine/doctrine-bundle", req)

    def test_no_database(self):
        controller = (ROOT / "src/Controller/DashboardController.php").read_text(
            encoding="utf-8"
        )
        status = compact((ROOT / "app/web_status.py").read_text(encoding="utf-8"))
        self.assertIn("'database'=>false", compact(controller))
        self.assertIn('"database":False', status)
        self.assertIn('"persistence_owner":"LAB"', status)

    def test_network_boundaries(self):
        status = compact((ROOT / "app/web_status.py").read_text(encoding="utf-8"))
        self.assertIn('"transport":"REST"', status)
        self.assertIn('"transport":"SMB"', status)
        self.assertIn('"scope":"AImodelsonly"', status)

    def test_front(self):
        base = (ROOT / "templates/base.html.twig").read_text(encoding="utf-8")
        dashboard = (ROOT / "templates/dashboard/index.html.twig").read_text(
            encoding="utf-8"
        )
        self.assertIn("jquery-3.7.1.min.js", base)
        self.assertIn("$.getJSON('/api/status')", dashboard)

    def test_caddy(self):
        caddy = (ROOT / "Caddyfile").read_text(encoding="utf-8")
        self.assertIn(":8712", caddy)
        self.assertIn("127.0.0.1:8713", caddy)


if __name__ == "__main__":
    unittest.main()
