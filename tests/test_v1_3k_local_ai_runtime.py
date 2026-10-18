from __future__ import annotations
import json, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]; APP=ROOT/"app"
if str(APP) not in sys.path: sys.path.insert(0,str(APP))
from ai_provider import AIProviderConfig, LocalAIProvider
from local_ai_runtime import LocalAIRuntimeConfig, local_model_path, sync_local_model_cache
class V13KLocalAIRuntimeContract(unittest.TestCase):
    def test_provider_maps_canonical_model_to_local_cache(self):
        cfg=AIProviderConfig(provider="local",shared_model_root=r"\\EZSTUDIO-MAIN\EZModels",local_model_path=r"\\EZSTUDIO-MAIN\EZModels\assistant\bench\qwen\model.gguf",local_cache_root=r"C:\EZStudioLab_assistant\runtime\models-cache",local_endpoint="http://127.0.0.1:8720")
        self.assertTrue(LocalAIProvider(cfg).model_path.endswith(r"assistant\bench\qwen\model.gguf"))
    def test_provider_rejects_outside_root(self):
        with self.assertRaises(RuntimeError): LocalAIProvider(AIProviderConfig(provider="local",shared_model_root=r"\\EZSTUDIO-MAIN\EZModels",local_model_path=r"C:\models\forbidden.gguf"))
    def test_sync_cache_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp); sr=b/"src"; s=sr/"assistant"/"model.gguf"; s.parent.mkdir(parents=True); s.write_bytes(b"abc")
            c=LocalAIRuntimeConfig(str(s),str(sr),b/"cache",b/"runtime","http://127.0.0.1:8720",8720,"Vulkan1",99,4096,b/"runtime"/"bin"/"llama-server.exe")
            a=sync_local_model_cache(c); d=sync_local_model_cache(c)
            self.assertTrue(a["copied"]); self.assertFalse(d["copied"]); self.assertEqual(local_model_path(c).read_bytes(),b"abc")
    def test_local_provider_http_contract(self):
        cfg=AIProviderConfig(provider="local",shared_model_root=r"\\EZSTUDIO-MAIN\EZModels",local_model_path=r"\\EZSTUDIO-MAIN\EZModels\assistant\model.gguf",local_cache_root=r"C:\EZStudioLab_assistant\runtime\models-cache",local_endpoint="http://127.0.0.1:8720")
        p=LocalAIProvider(cfg); seen=[]
        class R:
            def __init__(self,x): self.x=x
            def __enter__(self): return self
            def __exit__(self,*a): return False
            def read(self,n): return json.dumps(self.x).encode()
        def fake(req,timeout):
            seen.append(req.full_url)
            return R({"status":"ok"}) if req.full_url.endswith("/health") else R({"choices":[{"message":{"content":json.dumps({"summary":"ok","confidence":0.8,"dimensions":{},"sources":[]})}}]})
        preset = {
            "schema": "ezs.assistant.review-preset.v1", "id": "profile-qwen-baseline-1",
            "phase": "profile", "provider": "local",
            "prompt": "Review independently sourced PROFILE evidence with rigorous confidence. " * 4,
            "temperature": 0.1, "max_tokens": 1200, "context_max_chars": 6500,
        }
        canonical = r"\\EZSTUDIO-MAIN\EZStudio_lab\presets\assistant\profile-baseline-1.json"
        with patch("urllib.request.urlopen",fake), \
             patch("declarative_review.Path.read_bytes",return_value=json.dumps(preset).encode("utf-8")), \
             patch.dict("os.environ", {"EZSTUDIOLAB_REVIEW_PRESET_PATH": canonical}):
            self.assertTrue(p.status()["enabled"]); self.assertEqual(p.review_profile({"run_id":1,"title":"S","artist":"A"},{"sources":[]})["status"],"completed")
        self.assertTrue(any(x.endswith("/v1/chat/completions") for x in seen))
if __name__=="__main__": unittest.main()
