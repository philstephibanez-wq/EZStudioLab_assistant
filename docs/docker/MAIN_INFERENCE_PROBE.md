# Recette MAIN — runtime déclaratif réel v1.6a(131)

Le moteur CUDA Docker a déjà répondu sur MAIN par un appel manuel HTTP 200 puis un chat réussi. Cette tranche vérifie **le chemin applicatif Python** `preset JSON -> runtime/inference_runtime.py -> API OpenAI-compatible locale -> réponse tracée`, qui n'avait pas encore été essayé en situation réelle.

## Contrats de sécurité et de portée
- Branchement volontaire, à la demande : ne démarre, ne redémarre, n'arrête, ne télécharge ni ne déploie quoi que ce soit.
- Fonctionne seulement si le serveur local du preset est déjà prêt. Aucun appel LAB ni entrée d'assertion musicale privée.
- Affiche le modèle, le fournisseur, le SHA256 du preset et le texte généré, sans fabriquer de BON/FAUX/NON TROUVÉ ; zéro preuve indépendante dans cette recette.
- Pas de fichier log temporaire dans Git, pas de dépendance à H:\\temp, aucun token requis ; Windows PowerShell 5.1 compatible.
- Sur MAIN la requête exploite le serveur `127.0.0.1:18720` avec le GGUF Qwen 2.5 1.5B utilisé lors de la recette CUDA.

## Commandes MAIN (exécuter uniquement les lignes, pas le prompt PowerShell)
```powershell
cd H:\EZStudioLab_assistant
git pull --ff-only origin assistant-main
python -m unittest discover -s tests -p test_inference_probe.py
python -m unittest discover -s tests -p test_inference_runtime.py
python -m runtime.inference_probe
```

Attendu : 4 tests de probe, 5 tests de runtime, puis JSON `status: INFERENCE_OK`, fournisseur, modèle, `preset_sha256` de 64 hex et une phrase de réponse. Le modèle peut paraphraser : ne pas tester la sémantique en lui imposant une sortie exacte. S'il n'est plus prêt, erreur `INFERENCE_PROBE_FAILED` et code 2, pas de verdict. Les tests sont indépendants du GPU ; seule la dernière commande effectue une vraie inférence.

**Non livré dans cette tranche** : appel du workflow métier, collecte des sources Web, recoupement avec l'enregistrement précis, persistance de verdicts et qualification de qualité de réponse. Aucun succès de test simulé ne vaut recette GPU MAIN.
