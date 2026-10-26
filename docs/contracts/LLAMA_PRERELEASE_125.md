# MAIN — correctif v1.6a(125) sélection llama.cpp

Les releases officielles `ggml-org/llama.cpp` qui publient `llama-bNNNNN-bin-win-cpu-x64.zip` sont marquées `prerelease=true` dans l'API GitHub. Les exclure systématiquement rendait `LLAMA_CPU_X64_RELEASE_NOT_FOUND` inévitable, malgré leur présence et leur somme SHA-256 publiée.

La sélection conserve le filtre `draft`, l'unicité de l'asset CPU Windows x64, et le SHA-256 obligatoire ; elle n'exclut plus `prerelease`. Test contractuel connecté à l'API GitHub : `tests/test_llama_release_live_125.ps1`, lecture seule et sans téléchargement de ZIP. Installation seulement par `scripts/install-main.ps1 -Apply` après réussite du test. Les modèles et les sources LAB ne changent pas.
