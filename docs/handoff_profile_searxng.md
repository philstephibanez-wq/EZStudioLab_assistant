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