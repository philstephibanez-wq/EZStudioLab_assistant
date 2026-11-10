"""Regression contracts: no duplicate weights and canonical model path."""
import pathlib, sys, unittest, os
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'app'))
from local_ai_runtime import LocalAIRuntimeConfig, local_model_path
from ai_provider import AIProviderConfig, LocalAIProvider

class CanonicalModelsTest(unittest.TestCase):
    def test_runtime_returns_canonical_not_cache(self):
        path=r'\\EZSTUDIO-MAIN\EZModels\assistant\bench\model.gguf'
        cfg=LocalAIRuntimeConfig(canonical_model=path,shared_model_root=r'\\EZSTUDIO-MAIN\EZModels',
            cache_root=pathlib.Path('/unused-cache'),runtime_root=pathlib.Path('/unused-runtime'),
            endpoint='http://127.0.0.1:8720',port=8720,device='Vulkan1',gpu_layers=99,
            context_size=4096,server_exe=pathlib.Path('/unused'))
        self.assertEqual(str(local_model_path(cfg)),path)
    def test_provider_uses_canonical(self):
        path=r'\\EZSTUDIO-MAIN\EZModels\assistant\bench\model.gguf'
        cfg=AIProviderConfig(provider='local',shared_model_root=r'\\EZSTUDIO-MAIN\EZModels',local_model_path=path)
        self.assertEqual(LocalAIProvider(cfg).model_path,path)

if __name__=='__main__':unittest.main()
