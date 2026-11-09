# Autorité des branches Assistant — v1.6a(166)

## État audité

- `assistant-main` est la référence de développement et de déploiement MAIN pour EZStudioLab_assistant. À l'ouverture de ce dossier, sa base est le commit `8918767` (`1.6a(165)`), dont le cycle WinSW/FrankenPHP/Llama a été validé sur MAIN.
- `main` est encore la branche GitHub par défaut, à `60fe05bb` (`1.6a129`) lors de l'audit. Elle **ne doit pas être utilisée** pour livrer le runtime MAIN, ni être confondue avec la branche opérationnelle.
- Les branches divergent : 41 commits propres à `assistant-main`, 9 propres à `main`, merge-base `09845a40`. Les 9 commits propres à `main` concernent les contrats, les instructions et les versions, pas l'exécution métier.
- Les documents `AGENTS.md` et `CONTRAT DE DÉVELOPPEMENT.md` divergent entre les branches. Le contrat `EZS_STACK_V1_PLATEFORME_UNIFIEE.md` et le standard d'interface transversale existent dans `main` ; ils ne sont **pas implicitement adoptés** par `assistant-main` via ce dossier.

## Règles de travail immédiates

1. Toute lecture ou écriture GitHub concernant le runtime Assistant sur MAIN doit préciser **`ref=assistant-main`** ; ne pas utiliser implicitement la branche par défaut.
2. Les futures livraisons opérationnelles ciblent `assistant-main`, avec `VERSION` incrémentée, un commit cohérent et tests adaptés. Les changements locaux non committés sont protégés.
3. Interdits sans recette et accord explicite du mainteneur : merge, rebase, reset, force-push, suppression de branche, synchronisation automatique de `main`, changement de branche par défaut.
4. Pour une éventuelle consolidation, comparer les deux `AGENTS.md`, les deux contrats et les documents propres à `main` ; résoudre les contradictions **avant** la modification des références Git.
5. Contrôler les clones, workflows et outils qui suivent la branche par défaut avant de changer `default_branch`. Conserver l'historique des 9 commits et une voie de restauration.
6. Ne pas confondre nettoyage du dépôt et modification du cycle Windows. Aucun script historique, modèle, donnée scientifique, job, secret ou fichier runtime n'est supprimé par cette note.

## Validation de cette livraison

Modification documentaire seulement : ajout de cette politique et incrément de VERSION ; aucun fichier PHP, Python, PowerShell, Twig, configuration de service ou modèle modifié. Comparaison GitHub des deux branches et revue des 9 commits historiques effectuées. **Aucun test Windows / PHPUnit / Python exécuté pour cette note**. Aucun changement d'exécution attendu.

## Action ultérieure

Consolider les clauses réellement encore applicables de la branche `main` dans `assistant-main` par un chantier documentaire distinct, puis décider de la branche par défaut après vérification des consommateurs. En attendant, la référence opérationnelle reste `assistant-main`.
