# Handoff — PROFILE / SearXNG (23 octobre 2026)

Objectif : assistant XPS, recherche SearXNG sur MAIN, inférence locale GPU1, OCR documents imprimés, verdicts sourcés et persistance LAB. Aucun mock dans le produit.

## État observé
- Bing RSS : 3 morceaux (Supertramp, Pink Floyd, The Art Company) mal recherchés, résultats sans pertinence.
- DuckDuckGo/Bing HTML : erreurs généralisées sur XPS. Ne pas présenter erreur réseau comme NON TROUVÉ.
- Worker GPU/Qwen intégré en code, mais aucune preuve d'inférence GPU1 end-to-end.
- OCR Tesseract conservé ; 0 scan dans le rapport multi-chansons réel.

## Changements publiés (non validés sur XPS)
- app/profile_public_web.py : suppression scrapers Bing RSS, DuckDuckGo/Bing HTML au profit de SearXNG JSON auto-hébergé, configuré par EZS_SEARXNG_URL.
- app/profile_web_investigator.py : identification explicite search_provider=searxng_self_hosted.
- Autres modules et moteurs scientifiques LAB non modifiés. Aucun incrément de VERSION avant recette fonctionnelle.

## Installation et recette restantes
1. Installer SearXNG sur MAIN (LAN uniquement) ; configurer JSON dans search.formats de settings.yml. Sans cela /search?format=json retourne HTTP 403 (https://docs.searxng.org/dev/search_api.html).
2. Configurer EZS_SEARXNG_URL pour le compte du worker XPS et vérifier une réponse JSON réelle.
3. Recharger le worker avec les contrôles de maintenance existants seulement sans job active.
4. Tester les 3 chansons et vérifier que les pages sont de vraies sources musicales.
5. Activer et vérifier OCR réellement utilisé, enrichir les images du Web, inférence GPU1 réelle, contrôle de bonne édition/enregistrement, persistance LAB.
6. Intégrer la recherche itérative Local Deep Researcher ; non fait à ce stade.

## Hygiène et limites
Anciens scrapers retirés du module canonique seulement. Aucun effacement supplémentaire de scripts potentiellement utilisés sans audit de dépendances.
Pas d'installation MAIN/XPS ni d'essais runtime effectués par ces commits. Ne pas annoncer Assistant prêt. Ne pas fabriquer de verdicts.
Le dépôt exige un contrôle des contrats AGENTS.md et REPOSITORY_HYGIENE.md avant livraison définitive.
## Nettoyage complémentaire demandé le 23 octobre 2026
Suppression effective de trois scripts ponctuels dans `scripts/` : `profile_web_research_from_report.py`, `profile_web_multi_song_live.py`, `profile_web_live_preflight.py`. Ce sont des prévols/replays de l'ancien connecteur, contraires à l'hygiène des scripts temporaires. Le moteur applicatif conservé utilise `profile_public_web.py` et `profile_web_investigator.py`. Audit exhaustif de tous les fichiers du dépôt impossible avec les listings GitHub accessibles ici ; ne pas qualifier l'ensemble du dépôt de nettoyé intégralement ni supprimer sans vérification les services de production. Exécutions/compilation non faites sur XPS après retrait. La fonctionnalité SearXNG reste non déployée et non validée.

## Interface Assistant, saisie directe (23/10)
La page dashboard possède un formulaire titre + interprète/compositeur. Les neuf dimensions PROFILE canonique sont interrogées systématiquement, sans case à cocher (exigence explicite). Des valeurs LAB facultatives sont disponibles pour comparaison. API POST /api/profile/direct-research -> runtime/profile_direct_research.py -> SearXNG + module local de lecture IA. Tableau documentaire par item, URLs, diagnostic erreur, état OCR et statut IA ; pas d'écriture LAB par cette voie. Code non compilé ni exécuté sur XPS, endpoint SearXNG requis. VERSION non incrémentée.

## Superseded 23 October 2026: Windows-native search
SearXNG architecture above is superseded: no Docker, no WSL, no Linux, no service installation. `app/profile_public_web.py` now imports `ddgs` directly and runs a real Python metasearch from the existing Windows XPS interpreter. Install in the exact Python interpreter configured by Assistant (not a different global Python): `python -m pip install ddgs`; verify import `python -c "from ddgs import DDGS; print('DDGS_OK')"`. Models remain on H: unchanged. Existing Qwen/GPU1 and OCR integration remain incomplete and require live validation. Do not configure EZS_SEARXNG_URL. This is not a validated release, version unchanged.

## Reprise recherche directe Windows (23/10/2026)
- DDGS 9.16.0 installé et importé sur XPS ; vraie recherche Pink Floyd / Wish You Were Here avec cinq résultats musicaux pertinents fournis dans le journal utilisateur. Ceci valide recherche initiale, PAS chargement pages, OCR, inférence ni UI.
- Commit a1ab277 : pour recherche directe sans valeur LAB, l'IA ne rend jamais BON/FAUX ; elle peut rapporter une valeur externe documentée et reste en abstention de comparaison.
- Commit 2fd739c : formulaire Assistant titre + interprète seulement. Les neuf items canonique PROFILE sont toujours interrogés ; UI corrigée pour afficher DDGS au lieu de SearXNG.
- Attention : endpoint HTTP synchrone 180 s ; neuf recherches suivies d'inférences locales risquent le timeout. Pas encore de mécanisme asynchrone ni de test XPS final. Ne pas présenter le dashboard comme validé.
- Application installée sur C:\EZStudioLab_assistant (XPS), modèles IA inchangés sur H: (MAIN). Aucun Docker, WSL ou sudo.

## 23 octobre — correction timeout PHP confirmée
Sur XPS, POST recherche directe répondait HTML et HTTP 200 ; diagnostic direct PHP 8713 : `Maximum execution time of 30 seconds exceeded` dans `vendor/symfony/process/Pipes/WindowsPipes.php:142`. Ne pas augmenter arbitrairement timeout global PHP. Commits ca7d898/fa78872/74c93a8 : démarrage job Python détaché avec JSON dans `runtime/state/profile-direct`, API POST donne `job_id`, GET poll l'état; UI poll toutes les 2 s. Code publié, tests XPS non encore faits. Aucun changement de l'emplacement H: des modèles. Limite : jobs locaux de consultation non persistés dans LAB et nettoyage des états expirés non automatisé ; finaliser avant qualification production.

## Capture vraie Susanna / The Art Company — 23/10
DDGS fournit plusieurs sources, IA locale exécute des revues, mais non_trouve faute de valeur explicitement étayée. Des réponses sans résultat sont traitées comme erreurs, des pages >600k abandonnées ; OCR direct 0 scan. Commits 72d0ab5, 24c901b, 8e15958 corrigent ces trois points techniques de lecture/statut. Pas de validation instrumentale sur XPS pour ces commits. Prochain chantier : lecture des métadonnées structurées de SongBPM/ChordU et OCR des documents réellement trouvés, puis recette globale.

## Capture The Animals — House of the Rising Sun (23/10)
Résultat réel : 14 pages lues, 4 items avec références citables mais aucune preuve musicale explicite extraite. Requêtes spécifiques sans hits malgré des sources musique accessibles sur les autres items ; la requête instruments contenait littéralement `non déterminé`. Correction commit c139ea4 : recherche commune artiste+titre pour réutiliser un même ensemble de sources entre tous les items, requête instrumentale `instruments credits personnel`, déduplication des URL par item ; échecs de recherche spécifique visibles dans le rapport. Sans verdict automatique sur la seule provenance, OCR toujours non disponible dans recherche directe. Aucun test XPS exécuté sur cette modification.

## Capture John Denver (23/10)
45 pages lues, 5 items déclarés sourcés dans l'UI mais aucune valeur extérieure probante visible ; un `ValueError` IA. Ce nombre était trompeur (URL citée sans preuve musicale). Correctifs 6fa1add/55f3dd5/ff2e735 : compter uniquement citations avec référence extraite ; collecter méta description HTML ; contexte snippet DDGS explicitement non vérifié. Aucune exécution XPS de ces commits ; OCR toujours non disponible et pas de preuve de verdict musical. Le problème d'extraction fiable n'est PAS clos.

## UI cleanup — 23/10
Suppression de la carte `Runtime Python` (PID/job_id/phase/progress) du dashboard Assistant, commit fcddd6b. Télémétrie GPU et consultation PROFILE conservées. OCR direct déjà branché dans les commits 26df3689 et 0a9ba076, mais tests XPS non faits. Ne pas conclure à une installation validée.

## Contre-expertise documentaire — GO 23/10
Ajout `profile_document_candidates.py` : extraction bornée des formulations explicitement présentes de BPM, mesure, tonalité à partir de pages réellement lues, avec contexte court, URL et scope `unverified_external_candidate`. JSON/UI recherche directe : afficher les candidats, sans BON/FAUX ni promotion scientifique. L'IA locale continue sa lecture des mêmes documents. Commits ee8e80c5, cbdd3686, 4cceae0d, dcf20ae8, 712e8cde. Aucun test XPS à cette heure ; ne pas annoncer le résultat musical validé. OCR Tesseract reste limité aux éditions Cover Art Archive identifiées via MusicBrainz ; il n'extrait pas encore les prévisualisations de partitions de sites commerciaux et aucun moteur OMR n'est installé. Modèles H: inchangés, LAB non modifié. Prochaine étape : vérifier extraction réelle, déterminer éditions/enregistrements, envisager OMR uniquement sur matériaux consultables et autorisés, puis mémoriser les assertions approuvées dans LAB.

## Identification œuvre / interprète / version — 23/10
Commits 57f6276, 838e2e2, 8ec02f3 : chaque document de recherche directe porte une qualification `artist_title_matched_recording_unconfirmed`, `arrangement_or_score`, `version_requires_matching`, `work_only` ou `unrelated_or_uncertain`. L'interface indique explicitement que le même titre et artiste ne prouvent pas la version exacte. Une partition officielle d'une adaptation est secondaire pour l'enregistrement de LAB. Aucun verdict officiel promu, liaison LAB laissée désactivée jusqu'à test réel de confrontation. Classification textuelle heuristique, non vérifiée sur XPS ; présence éventuelle d'une mention éditeur n'est pas une certification officielle. Modèles H: inchangés.

## OMR partitions — 23/10/2026 — 1.6a(30)
Module `app/profile_score_omr.py` ajouté (commit e162a978) : adaptateur Audiveris Windows **sur fichier de partition local**, exécution temporaire `-batch -export`, lecture MusicXML compressé et extraction candidats mesure/armure/tempo/pupitres/titre/compositeur, tous non validés pour enregistrement audio. Révision `VERSION` passée de 1.6a(29) à 1.6a(30), commit 8c6d871f. **Limites obligatoires** : aucun lien automatique aux aperçus des pages Web ni à l'interface recherche directe ; Audiveris non vérifié/installé sur XPS, aucun essai runtime réel. OCR Tesseract reste distinct. Aucune écriture scientifique LAB ; ne pas annoncer de lecteur intégré utilisable depuis l'interface. La règle chaque push=VERSION n'a pas été respectée lors des commits préparatoires, dette de livraison à contrôler. Étape suivante : test sur vraie partition et raccordement de documents avec contrôle des versions musicales et du caractère accessible de la source.

## 23/10/2026 — Vues communes LAB et Assistant (1.6a(32) / LAB 1.4a(9))
Contrat : analyse # (public_id), preset # uniquement si réellement enregistré, titre/interprète déclarés incertains, dix items avec valeurs LAB et avis BON/MAUVAIS/INCONNU, explication et sources accessibles. LAB conserve la révision ; Assistant lit la synthèse en lecture seule. Commits LAB 8a77a4b, 03bf217, d6ef221, ff09c35 ; Assistant 340d859, ae0ae83, d89ef0d. Limites : aucun test runtime MAIN/XPS ; aucune validation de valeur musicale, appariement d'identité ou stabilité ; dernière révision persistée globale, pas forcément chanson sélectionnée ; champ numéro preset à confirmer en données réelles ; flux worker historique toujours trop volumineux. Aucun changement moteur/preset scientifique. Étape : tester UI LAB déclenchement, persistance, lecture miroir XPS et comparer les dix verdicts sur le même run. Ne pas annoncer comme validé.
