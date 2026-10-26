import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('inference_runtime', ROOT / 'runtime' / 'inference_runtime.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RuntimeTest(unittest.TestCase):
    def preset(self, data):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / 'preset.json'
        path.write_text(json.dumps(data), encoding='utf-8')
        return path

    def config(self):
        return json.loads((ROOT / 'config' / 'inference.main.json').read_text(encoding='utf-8'))

    def test_config_valid_and_sha_stable(self):
        p = self.preset(self.config())
        cfg, sha = module.load_preset(p)
        self.assertEqual(cfg['provider'], 'openai-compatible')
        self.assertEqual(len(sha), 64)

    def test_external_address_rejected(self):
        cfg = self.config()
        cfg['endpoint'] = 'http://example.com:18720'
        with self.assertRaises(module.InferenceConfigurationError):
            module.load_preset(self.preset(cfg))

    def test_missing_preset_fails_closed(self):
        with self.assertRaises(FileNotFoundError):
            module.load_preset('does-not-exist.json')

    def test_valid_inference_and_sha(self):
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *args): self.close()
        def fake_open(request, timeout):
            self.assertTrue(request.full_url.endswith('/v1/chat/completions'))
            self.assertEqual(json.loads(request.data)['stream'], False)
            return Response(b'{"choices":[{"message":{"content":"ok"}}]}')
        result = module.infer(self.preset(self.config()), [{'role':'user','content':'test'}], opener=fake_open)
        self.assertEqual(result['text'], 'ok')
        self.assertEqual(len(result['preset_sha256']), 64)

    def test_invalid_reply_never_returns_verdict(self):
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *args): self.close()
        with self.assertRaises(RuntimeError):
            module.infer(self.preset(self.config()), [{'role':'user','content':'test'}], opener=lambda *args, **kwargs: Response(b'{}'))


if __name__ == '__main__':
    unittest.main()
