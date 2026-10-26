# Contrat des assertions musicales finales — 1.6a(132)

Entrée : enregistrement (titre, artiste, version, identifiant) et liste dynamique de valeurs finales musicales. Les métadonnées scientifiques internes sont exclues par liste blanche stricte. Aucun nombre d'instruments ou de caractéristiques n'est figé.

Sortie : une ligne par assertion. La valeur absente est `sans_valeur_lab` ; sinon `non_trouve` tant qu'aucun fournisseur de preuves documentaires indépendantes n'est relié. Aucune URL transmise par un appelant ne suffit à prouver un enregistrement, et aucune sortie Qwen ne devient automatiquement une référence. `confidence_pct` demeure `null`, `reference_value` demeure `null`, `evidence` demeure vide ; aucun BON ou FAUX n'est émis sans validation documentaire réelle.

Limites : recherche Web, contrôle de l'enregistrement, extraction de preuves, recoupement, tolérance tempo ×2/÷2, persistance LAB, UI et recette E2E **non livrés**. Ce socle ne démarre aucun moteur et ne modifie ni LAB, ni EZScore, ni XPS.

Recette MAIN : `python -m unittest discover -s tests -p test_musical_contract.py` depuis `H:\EZStudioLab_assistant`.
