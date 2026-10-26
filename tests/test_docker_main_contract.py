from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MainDockerSmokeContract(unittest.TestCase):
    def test_explicit_isolated_profile_and_loopback(self):
        source = (ROOT / "docker/main/compose.yaml").read_text(encoding="utf-8")
        self.assertIn('profiles: ["smoke"]', source)
        self.assertIn('127.0.0.1:18713:8713', source)
        self.assertIn('restart: "no"', source)
        self.assertNotIn("network_mode: host", source)
        self.assertNotIn("privileged: true", source)

    def test_no_models_secrets_workers_in_image(self):
        source = (ROOT / "docker/main/Dockerfile").read_text(encoding="utf-8")
        ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8")
        self.assertIn('FROM php:8.4-cli-bookworm', source)
        self.assertIn('CMD ["php", "-S"', source)
        for key in ("runtime", "logs", "models", ".env", "*.gguf"):
            self.assertIn(key, ignored)
        self.assertNotIn("profile_guardian", source)
        self.assertNotIn("llama-server", source)

    def test_readme_is_explicitly_non_production(self):
        doc = (ROOT / "docs/docker/MAIN_PREFLIGHT.md").read_text(encoding="utf-8")
        self.assertIn("smoke-test Web Symfony", doc)
        self.assertIn("aucun worker", doc)
        self.assertIn("assistant-main", doc)

if __name__ == "__main__":
    unittest.main()
