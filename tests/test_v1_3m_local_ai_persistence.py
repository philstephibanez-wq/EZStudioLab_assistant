from __future__ import annotations
import json, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/"app"
if str(APP) not in sys.path: sys.path.insert(0,str(APP))
import local_ai_runtime as runtime
from local_ai_runtime import LocalAIRuntimeConfig, sync_local_model_cache

class V13MLocalAIPersistenceContract(unittest.TestCase):
    def cfg(self,b):
        shared=b/"shared"; canonical=shared/"assistant"/"model.gguf"
        return LocalAIRuntimeConfig(str(canonical),str(shared),b/"cache",b/"runtime","http://127.0.0.1:8720",8720,"Vulkan1",99,4096,b/"runtime"/"bin"/"llama-server.exe")
    def test_cache_offline_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp); c=self.cfg(b); s=Path(c.canonical_model); s.parent.mkdir(parents=True); s.write_bytes(b"abc")
            self.assertTrue(sync_local_model_cache(c)["copied"]); s.unlink()
            x=sync_local_model_cache(c); self.assertEqual(x["status"],"cached_offline"); self.assertFalse(x["copied"])
    def test_invalid_cache_does_not_hide_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp); c=self.cfg(b); t=runtime.local_model_path(c); t.parent.mkdir(parents=True); t.write_bytes(b"bad")
            c.runtime_root.mkdir(parents=True)
            (c.runtime_root/"cache-manifest.json").write_text(json.dumps({"canonical_model":c.canonical_model,"size":999}),encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,"local_ai_canonical_model_missing"): sync_local_model_cache(c)
    def test_persistent_windows_task_contract(self):
        src=Path(runtime.__file__).read_text(encoding="utf-8")
        self.assertIn('LOCAL_AI_TASK_NAME = "EZStudioLab Assistant Local AI"',src)
        self.assertIn("Register-ScheduledTask",src); self.assertIn("Start-ScheduledTask",src)
        self.assertIn("EZS_ASSISTANT_LOCAL_AI_RECOVERY",src)
        self.assertIn("_register_and_start_task(cfg, model)",src)
    def test_stop_unregisters_tasks(self):
        src=Path(runtime.__file__).read_text(encoding="utf-8")
        self.assertIn("_stop_and_unregister_tasks()",src)
        self.assertIn("Unregister-ScheduledTask",src)

if __name__=="__main__": unittest.main()
