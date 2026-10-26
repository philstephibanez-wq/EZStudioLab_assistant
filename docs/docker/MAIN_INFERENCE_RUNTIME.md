# Runtime declaratif d'inference — v1.6a(130)

Portee : **branche assistant-main seulement**. Premier socle autonome en Python (stdlib), **non branche au workflow d'expertise**. Aucun changement LAB, EZScore, XPS, worker, Compose ou moteurs actifs.

## Contrat
- Preset UTF-8 JSON canonique `config/inference.main.json`, schema `ezstudio-assistant.inference.v1`.
- Provider `openai-compatible`; client HTTP local par defaut `127.0.0.1:18720` (Docker llama.cpp CUDA existant).
- Lecture du preset **a chaque appel** et calcul SHA256 sur les octets lus ; chaque reponse valide expose `preset_sha256`, `provider`, `model`.
- Validation stricte du schema, du modele, des parametres et du port/endpoint loopback. **Les URL externes ne sont pas supportees par ce premier contrat** ; futur provider distant = nouvel adaptateur explicite.
- `infer(path, messages)` retourne du **texte brut du modele**, **jamais** un verdict BON / FAUX / NON TROUVE. Une erreur HTTP, un preset absent ou une reponse malformee provoque une erreur explicite, pas une preuve musicale.
- Pas de cache de verdict, pas de GPU exclusif, pas de deploiement automatique. Pas de secret en Git.
- Aucun appel aux moteurs/presets scientifiques LAB ; l'Assistant ne recoit que les assertions musicales finales, dans les evolutions suivantes.

## Verification locale
```powershell
cd H:\EZStudioLab_assistant
git pull --ff-only origin assistant-main
python -m unittest discover -s tests -p test_inference_runtime.py
```
La recette MAIN end-to-end, le raccordement au workflow musical et les recherches Web documentaires sont **non faits** dans ce commit. Les cinq tests unitaires ont ete executes hors MAIN avant publication.
