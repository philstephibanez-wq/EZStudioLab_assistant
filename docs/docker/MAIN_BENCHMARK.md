# Benchmark Qwen CUDA versus Vulkan — v1.6a(129)

Ce benchmark **ne démarre, n'arrête et ne télécharge aucun moteur ni modèle**. Il utilise deux serveurs OpenAI-compatible *déjà opérationnels* avec le **même GGUF**, le même contexte et les mêmes paramètres. Il appelle les serveurs **séquentiellement** afin de ne pas créer de concurrence volontaire entre requêtes. Une absence de serveur Vulkan ou un échec de réseau rend le benchmark incomplet : aucune comparaison artificielle.

## État acquis sur MAIN

La version précédente 1.6a(128) a exécuté une première requête réelle CUDA Qwen2.5-1.5B Q4_K_M sur le port loopback 18720 : 33 tokens générés en 1,656 s, `predicted_per_second=19.33`, `prompt_ms=24097.87`. Cela **ne constitue pas** un benchmark comparatif ; le temps de chargement et les conditions de cache sont à considérer.

## Prérequis

- CUDA : `http://127.0.0.1:18720`, modèle déjà prêt (health HTTP 200).
- Vulkan : relever l'adresse exacte du serveur Windows **existant**, son identifiant de modèle et ses paramètres. **Ne pas présumer qu'il fonctionne sur MAIN ni le lancer à l'aveugle**.
- Vérifier la disponibilité GPU de MAIN selon les règles LAB/EZScore avant les mesures.
- Vérifier même GGUF (taille/empreinte), `ctx-size`, `parallel`, couches GPU, template chat, version moteur, et éventuel cache. Les mesures de tokens/s ne sont strictement comparables qu'après contrôle de ces variables.
- Sortie dans `H:\temp`, jamais dans Git ; aucun secret ni prompt privé.

## Commande, seulement lorsque les deux serveurs sont prêts

```powershell
cd H:\EZStudioLab_assistant
python .\scripts\benchmark_inference_engines.py `
  --cuda-url http://127.0.0.1:18720 `
  --vulkan-url http://127.0.0.1:PORT_VULKAN_REEL `
  --model qwen2.5-1.5b-instruct-q4_k_m.gguf `
  --output H:\temp\assistant-benchmark-engines.json
```

Le programme envoie trois prompts de diagnostic, deux répétitions par moteur, `temperature=0`, `max_tokens=120`, et enregistre latence réelle, génération tokens/s, éventuels timings serveur, JSON valide, sorties brutes. Ce jeu de prompts teste le contrat de base, **pas une contre-expertise factuelle démontrée**. Il n'utilise aucune chanson particulière ni aucune preuve publique. Les échecs sont explicites, sans résultats de substitution.

## Validation

Tests statiques locaux à effectuer : `python -m unittest discover -s tests -p test_benchmark_inference_engines.py`. Aucun résultat de benchmark Vulkan ou comparaison CUDA/Vulkan n'est revendiqué par cette livraison. Le JSON généré contient les réponses du modèle et doit rester privé.
