# Contrat d'inférence pour l'explorateur documentaire — v1.6a(108)

## Décision
L'orchestrateur Python, le calcul d'ensembles et le validateur de citations restent déterministes. L'inférence doit **extraire simultanément tous les faits d'une ressource**, comprendre synonymes et langues, puis suggérer des pistes dans une étape ultérieure. La validation et le statut d'enregistrement ne sont jamais laissés au seul modèle.

## Qualification obligatoire avant toute bascule
- Tester le modèle actuellement déployé et des candidats plus performants avec les **mêmes documents**, consignes et budgets ; documents de référence établis indépendamment de LAB.
- Mesurer précision, rappel, citations réelles, faux positifs, latence, consommation de mémoire et stabilité JSON.
- Jeux d'essai multilingues, multi-enregistrements, contradictions, documents longs et injection dans des pages Web.
- Les textes de pages et la sortie d'IA sont non fiables : les citations doivent être extraites de documents réellement téléchargés ; citation textuelle exacte = condition nécessaire, **pas suffisante**, pour valider une preuve musicale.
- Séparer **évaluation** du modèle, **choix** du modèle et **déploiement**. Aucune bascule automatique.
- Modèles stockés sur MAIN, jamais copiés durablement sur le SSD XPS ; respecter les ressources vérifiées du runtime XPS avant de fixer taille/quantification.

## Livrable 108
Module `app/profile_inference_qualification.py` et tests `tests/test_profile_inference_qualification_108.py` : client OpenAI-compatible sur loopback, validation des URL et citations, mesures exact-match, injection d'inférence pour tests hors réseau. Pas de données LAB brutes, de changement du modèle en service, de connexion au worker ou de téléchargement. Les tests unitaires ne sont **pas** une mesure de performance d'un modèle réel. L'évaluation sur XPS doit suivre avant toute recommandation chiffrée.

## Handoff
Fournir un corpus documentaire réel annoté et indépendant, un outil de lancement explicitement opt-in (plusieurs modèles), des mesures mémoire sur XPS et la comparaison coûts/qualité. Ensuite seulement décider de conserver le modèle ou de le remplacer.

## v1.6a(109) : qualification du modèle réellement servi

Le script `app/profile_inference_live_benchmark.py` est un test volontaire (opt-in) de localhost:8720 avec trois textes SYNTHÉTIQUES (ES/FR/EN, variantes studio/live) et un oracle documentaire indépendant. Chaque texte est exploré pour tous les items, les citations sont comparées littéralement et les métriques sont publiées dans la console. Aucune mesure n'est revendiquée avant son exécution sur XPS. Pas de bascule du worker, ni de modification de presets, ni de transfert de modèles. Un corpus Web annoté et un candidat concurrent restent nécessaires avant toute décision de modèle.

## v1.6a(110) — Contrôle JSON contraint

Nouveau benchmark explicitement opt-in avec `response_format=json_schema`, exemple court, validation stricte des identifiants, champs et valeurs mesurées contenues dans les citations. Même corpus de 109 pour comparaison directe. Aucun remplacement d'inférence sans benchmark XPS. Il subsiste une limite : une citation contenant un nom instrumental ne démontre pas, par elle-même, qu'il constitue un crédit exact de la bonne version.

## v1.6a(111) — Comparaison à deux moteurs, isolée

Le comparateur `app/profile_model_comparator.py` compare un serveur de référence à `127.0.0.1:8720` et un modèle candidat **déjà démarré** sur un autre port local, à schéma/consigne/corpus identiques. Il n'installe, ne copie, ne démarre ni n'arrête de modèle. Un essai en erreur est marqué invalide. Le serveur de production n'est pas reconfiguré. L'opérateur doit d'abord inventorier les modèles réellement présents sur MAIN et confirmer les ressources XPS avant tout lancement du candidat ; éviter toute saturation mémoire. Les résultats des trois textes synthétiques ne sont pas une expertise Web et ne suffisent pas à la sélection définitive du moteur. Les mêmes données doivent ultérieurement être évaluées sur corpus documentaire annoté et indépendant.

## v1.6a(112) — Candidat Qwen3-1.7B, stockage MAIN

Candidat GGUF Q4_K_M vérifié sur le catalogue Hugging Face Unsloth; aucun gain de qualité présumé. Le script d'acquisition ne fait rien en lecture seule par défaut, ne télécharge qu'avec --download, exige taille/SHA256 upstream et refuse l'écrasement. Écriture exclusivement sur `\\\\EZSTUDIO-MAIN\\EZModels`; aucune copie ni cache durable sur XPS. Ne lancer **aucun deuxième serveur** tant que les capacités de la machine et la stratégie de benchmark séquentiel n'ont pas été validées. Port 8720 et Qwen de référence intacts.

## v1.6a(113) — Correctif intégrité Hugging Face Xet

Lorsque la liste de fichiers n'expose pas `lfs.sha256`, effectuer une requête HEAD sur le lien `resolve/main`, relever `X-Linked-Etag` (empreinte SHA-256) et `X-Linked-Size`, vérifier leur format et la concordance de taille avec la liste d'origine. Un champ manquant ou incohérent est une erreur bloquante ; ne jamais désactiver la vérification. Le téléchargement garde sa validation SHA-256 complète avant publication sur MAIN ; ne change pas l'inférence XPS.

## v1.6a(114) — Racine UNC Windows

Le dossier `\\\\EZSTUDIO-MAIN\\EZModels` est une racine de partage (`PureWindowsPath.anchor`) et non un dossier final (`Path.name` vide). Vérification stricte de l'égalité au partage autorisé, même après normalisation casse et séparateurs, sans laisser passer des sous-chemins arbitraires. Aucune modification du SHA-256 ou du téléchargement opt-in.

## v1.6a(115) — Transfert résumable et observable

Suite au défaut réel sur XPS : `DOWNLOAD_SHA256_MISMATCH` après un transfert bloqué sur un premier bloc de 4 Mio, le téléchargeur doit requérir des plages HTTP exactes (`206`, `Content-Range`), journaliser la progression, reprendre exclusivement un `.part` sur MAIN et refuser toute publication d'un fichier de taille ou SHA-256 incorrect. Un serveur qui refuse Range provoque une erreur explicite. Les fragments restent sous MAIN à des fins de reprise ; un lock empêche deux téléchargements concurrents. Aucun cache modèle sur XPS, aucun redémarrage d'inférence. Si `.part` est complet mais invalide, arrêter : contrôle manuel nécessaire, jamais contourner le SHA-256.
