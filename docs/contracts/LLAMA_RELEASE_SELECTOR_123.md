# Correctif distribution llama.cpp — v1.6a(123)

La route GitHub `releases/latest` expose une release produit ne contenant parfois que `nightly-tag.txt`, sans exécutable Windows. Le bootstrap utilise désormais les 20 releases récentes, ignore draft/prerelease et prend la première ayant un et un seul asset `llama-bNNNNN-bin-win-cpu-x64.zip`. Il continue d'exiger la somme SHA-256 publiée dans `asset.digest` et la vérification des octets téléchargés, avant installation sur H:. Le chemin GGUF, le modèle, le preset local, les services Caddy et la science LAB restent inchangés.

Test sur MAIN: `python .\\tests\\test_llama_release_selector_123.py` puis `powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\install-main.ps1 -Apply`. La réussite du test statique ne prouve pas que la distribution démarre.
