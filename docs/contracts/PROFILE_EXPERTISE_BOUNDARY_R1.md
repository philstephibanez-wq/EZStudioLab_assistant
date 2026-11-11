# PROFILE — tranche P0 R1 : frontière des assertions finales

## Autorité

`AGENTS.md`, Assistant #11/#12 et LAB #17 priment sur les anciens plans d'audit des modules. L'Assistant contre-expertise **les seules valeurs musicales finales proposées par LAB**, jamais les moteurs, scores internes, presets scientifiques ou la manière dont LAB calcule ses résultats.

## Écart constaté dans le code publié

À `assistant-main` version `1.7a12`, `build_assertions()` laissait passer des objets JSON sous `items`, alors que les champs métier doivent être des valeurs musicales scalaires ou une liste d'instruments. `runtime/profile_verify_push.py` déclenchait des recherches même pour les champs `null`, sans proposition LAB. L'absence de proposition ne doit produire ni recherche par item, ni verdict musical.

## Décision R1

- Filtrage strict à la frontière métier : `None`, `bool` et les sentinelles `possible` / `not_scored` / `inconclusive` ne sont pas des assertions ; les valeurs finies scalaires sont admises ; **seul `instruments` peut contenir une liste de valeurs atomiques**. Objets imbriqués, autres listes et nombres non finis sont rejetés explicitement avant toute recherche.
- Aucun moteur, preset scientifique, score ou diagnostic privé ajouté aux requêtes.
- `verify()` ne recherche que les items réellement proposés ; lorsqu'aucun item n'est proposé, aucune recherche documentaire n'est déclenchée et les dix retours existants restent `sans_valeur_lab`.
- Les sources consultées ne deviennent pas automatiquement des preuves, l'identité d'enregistrement reste non confirmée en l'absence de preuve ; aucun `BON` ni `FAUX` ajouté par cette tranche.
- La forme historique des dix `reviews` et la persistance LAB ne sont pas modifiées.

## Limites et suite

**Non résolu par R1 :** l'inventaire dynamique `final_assertions` fourni par LAB n'est pas encore parcouru intégralement par le vérificateur ; en particulier les instruments doivent être jugés individuellement. Une tranche distincte doit ensuite connecter cet inventaire à des recherches par item, identifier le bon enregistrement, établir des preuves indépendantes puis valider le retour persistant et le rendu LAB sur un run réel. La CI et les tests de sécurité de R1 ne prouvent pas la validité musicale.

Aucune modification STEMS, CHORDS/N, LYRICS, EZScore, moteurs, presets, jobs, services, token ou stockage historique. Aucune activation ou redémarrage implicite.
