# Recherche Web ouverte et théorie des ensembles — v1.6a(138)

Première tranche **exécutable en lecture seule**. Ce moteur cherche via une interface de recherche Web générale (DuckDuckGo HTML), découvre des domaines arbitraires sans liste fermée de sites musicaux, ouvre des pages HTML publiques, indexe les caractéristiques finales de LAB selon leurs **mentions textuelles** puis calcule les intersections réellement constatées. Il produit événements/erreurs et un JSON des ensembles. Les mentions sont des **candidats de couverture documentaire**, et ne sont pas des preuves musicales ni des validations d'identité. Les verdicts restent vides.

**La recherche Web ouverte n'est PAS encore un agent autonome complet** : il manque l'identité d'enregistrement prouvée, l'extraction structurée des valeurs indépendantes, Qwen fondé sur pièces, le mécanisme BON/FAUX/NON TROUVÉ, et le retour persistant LAB. Un échec réseau est déclaré, jamais converti en FAUX. L'accès de l'agent doit être confiné à une politique réseau d'egress public pour résister au DNS rebinding. La disponibilité des moteurs externes n'est pas garantie.

Pour tester **sans claim, sans token dans le JSON et sans exécuter PROFILE** sur MAIN, après avoir récupéré le contexte authentifié de #181 dans la variable PowerShell `$result` :

```powershell
cd H:\EZStudioLab_assistant
git pull --ff-only origin assistant-main
python -m unittest discover -s tests -p test_open_web_sets.py
New-Item -ItemType Directory -Force H:\temp\assistant-web-181 | Out-Null
$result | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 H:\temp\assistant-web-181\job.json
python -m runtime.open_web_sets --input H:\temp\assistant-web-181\job.json --output H:\temp\assistant-web-181\sets.json
Get-Content H:\temp\assistant-web-181\sets.json -Encoding UTF8 | ConvertFrom-Json | Select-Object job_id,run_id,song_id,status,discovered_count,read_count
```

**Important** : Python PowerShell 5.1 peut produire un BOM UTF-8 ; l'entrée utilise utf-8-sig. N'exécuter aucun appel `claim`/`finish` pour #181. Le statut canonical reste queued.
