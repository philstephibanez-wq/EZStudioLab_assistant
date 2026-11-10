"""Contract v1.7a6: explicit local model location, no SMB, no model copies."""
from __future__ import annotations
import json,sys,unittest,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
class LocalModels176(unittest.TestCase):
    def test_legacy_env_unc_forbidden(self):
        from local_ai_runtime import _relative_model_path
        with self.assertRaisesRegex(RuntimeError,'local_ai_smb_forbidden'):
            _relative_model_path(r'\\server\share',r'\\server\share\model.gguf')
        with self.assertRaisesRegex(RuntimeError,'local_ai_parent_traversal_forbidden'):
            _relative_model_path(r'H:\EZSModels',r'H:\EZSModels\..\bad.gguf')
    def test_configuration_shared_by_provider_and_runtime(self):
        import ai_provider,local_ai_runtime
        self.assertEqual(ai_provider.DEFAULT_SHARED_MODEL_ROOT,r'H:\EZSModels')
        self.assertEqual(local_ai_runtime.DEFAULT_SHARED_MODEL_ROOT,r'H:\EZSModels')
        self.assertEqual(ai_provider._ezs_local_model_config.__name__,'_ezs_local_model_config')
        self.assertEqual(local_ai_runtime._ezs_local_model_config.__name__,'_ezs_local_model_config')
    def test_php_keeps_identity_and_config_guards(self):
        src=(ROOT/'src/Service/AssistantLlamaLifecycle.php').read_text(encoding='utf-8')
        self.assertIn('GPU_LOCAL_MODEL_CONFIG_MISSING',src)
        self.assertIn('LLAMA_STOP_IDENTITY_MISMATCH',src)
        self.assertIn('GPU_CANONICAL_MODEL_INVALID',src)
        self.assertNotIn('EZSTUDIO-MAIN',src)
    def test_ocr_no_unc(self):
        src=(ROOT/'app/profile_tesseract_runtime.py').read_text(encoding='utf-8')
        self.assertIn('network_model_path_refused',src)
        self.assertIn('_ezs_local_tessdata_default',src)
    def test_persisted_model_points_outside_assistant(self):
        p=ROOT/'runtime/state/local-model.json'
        cfg=json.loads(p.read_text(encoding='utf-8'))
        self.assertEqual(cfg['schema'],'ezs.assistant.model-location.v1')
        from pathlib import PureWindowsPath
        model=PureWindowsPath(cfg['model']); storage=PureWindowsPath(cfg['root'])
        self.assertTrue(model.is_absolute() and storage.is_absolute())
        self.assertTrue(model.relative_to(storage).parts)
        self.assertNotIn('models-cache',str(model).lower())
        self.assertFalse(str(model).startswith('\\'))
    def test_version(self):
        self.assertEqual((ROOT/'VERSION').read_text(encoding='utf-8').strip(),'1.7a6')
if __name__=='__main__':unittest.main()
