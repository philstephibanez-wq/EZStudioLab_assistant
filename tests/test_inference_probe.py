import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("inference_probe", ROOT / "runtime" / "inference_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class InferenceProbeTests(unittest.TestCase):
    def test_success_preserves_trace_without_inventing_verdict(self):
        calls = []
        def fake_client(path, messages):
            calls.append((path, messages))
            return {"text": "Non vérifiée.", "model": "test-gguf", "provider": "openai-compatible", "preset_sha256": "a" * 64}
        result = probe.probe(ROOT / "config" / "inference.main.json", client=fake_client)
        self.assertEqual(result["status"], "INFERENCE_OK")
        self.assertEqual(result["musical_verdict"], None)
        self.assertEqual(result["independent_sources_checked"], 0)
        self.assertEqual(result["preset_sha256"], "a" * 64)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(calls[0][1]), 2)

    def test_empty_reply_fails_closed(self):
        with self.assertRaises(RuntimeError):
            probe.probe(client=lambda *args: {"text": "", "preset_sha256": "b" * 64})

    def test_missing_sha_fails_closed(self):
        with self.assertRaises(RuntimeError):
            probe.probe(client=lambda *args: {"text": "ok"})

    def test_main_reports_unavailable_without_success(self):
        old = probe.probe
        try:
            probe.probe = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline"))
            self.assertEqual(probe.main([]), 2)
        finally:
            probe.probe = old


if __name__ == "__main__":
    unittest.main()
