import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "scripts" / "benchmark_inference_engines.py"
spec = importlib.util.spec_from_file_location("benchmark_inference_engines", FILE)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class BenchmarkInferenceContract(unittest.TestCase):
    def test_payload_identical_for_two_endpoints(self):
        seen = []
        original = bench.post
        def fake_post(base, payload, timeout):
            seen.append((base, json.dumps(payload, ensure_ascii=False, sort_keys=True)))
            return {"choices": [{"message": {"content": '{"verdict":"non_trouve"}'}}],
                    "usage": {"completion_tokens": 2}}
        try:
            bench.post = fake_post
            result = bench.run([("cuda", "http://localhost:1"), ("vulkan", "http://localhost:2")],
                               "same.gguf", 1, 1)
        finally:
            bench.post = original
        self.assertEqual(len(seen), 6)
        self.assertEqual([x[1] for x in seen[:3]], [x[1] for x in seen[3:]])
        self.assertEqual(result["runs"]["cuda"]["json_valid_count"], 3)

    def test_invalid_json_is_not_a_success(self):
        self.assertFalse(bench._valid_json("not json"))
        self.assertTrue(bench._valid_json('{"ok": true}'))

    def test_no_engine_bootstrap_in_benchmark(self):
        source = FILE.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", source)
        self.assertNotIn("docker run", source)
        self.assertNotIn("start-process", source.lower())


if __name__ == "__main__":
    unittest.main()
