from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class DockerCudaContract(unittest.TestCase):
    def test_gpu_service_opt_in_and_local_only(self):
        c = (ROOT / "docker/main/compose.cuda.yaml").read_text(encoding="utf-8")
        self.assertIn('profiles: ["cuda-smoke"]', c)
        self.assertIn("gpus: all", c)
        self.assertIn("127.0.0.1:18720:8080", c)
        self.assertIn("restart: \"no\"", c)
        self.assertNotIn("network_mode: host", c)

    def test_explicit_read_only_existing_model(self):
        c = (ROOT / "docker/main/compose.cuda.yaml").read_text(encoding="utf-8")
        self.assertIn("EZS_ASSISTANT_MODEL_DIR:?", c)
        self.assertIn("EZS_ASSISTANT_MODEL_FILE:?", c)
        self.assertIn("read_only: true", c)
        self.assertIn("ghcr.io/ggml-org/llama.cpp:server-cuda", c)
        self.assertNotIn("huggingface-cli", c)

    def test_no_automatic_activation(self):
        docs = (ROOT / "docs/docker/MAIN_CUDA_SMOKE.md").read_text(encoding="utf-8")
        self.assertIn("analyse GPU active", docs)
        self.assertIn("cuda-smoke", docs)
        self.assertIn("aucun téléchargement automatique", docs)

if __name__ == "__main__":
    unittest.main()
