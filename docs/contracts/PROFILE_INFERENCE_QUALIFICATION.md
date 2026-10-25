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
