# Visualisation du pipeline — v1.6a(136)

L'accueil `/` affiche les huit étapes contractuelles, le journal des événements réellement observés dans le navigateur, les ensembles/intersections (vides en l'absence de documents qualifiés) et le tableau d'assertions (vide sans entrée finale LAB). Les identités candidates MusicBrainz sont strictement distinguées des preuves musicales. Aucune donnée de démonstration ne prétend provenir de LAB, aucun verdict BON/FAUX n'est inventé. Le journal de session est volatil, explicitement signalé.

**Limites bloquantes** : la recherche Web ouverte et la théorie des ensembles calculée à partir de documents réels, les run LAB, le pipeline orchestré et le retour LAB restent à implémenter. La présente version livre exclusivement la **visualisation initiale et ses états vides honnêtes**. Elle ne constitue pas une contre-expertise complète.

Recette MAIN : `python -m unittest discover -s tests -p test_pipeline_ui_contract.py`, puis reconstruire et recréer uniquement le Web via Docker Compose smoke. Vérifier `http://127.0.0.1:18713/`. Ne pas redémarrer CUDA ou LAB.
