# 1.6a(102) — Convention de versionnement atomique

## Contexte
Les contrats de commit des trois dépôts étaient contradictoires et les versions n'étaient pas affichées en tête des commits.

## Modifications
Harmonisation des clauses existantes d'AGENTS.md ; convention `[vVERSION] type(périmètre): résultat` ; incrément `VERSION` dans le même commit.

## Validation
Contrôle statique des clauses et versions GitHub ; aucun test runtime effectué ni déclaré.

## Impact
Aucune modification des calculs, jobs ou moteurs. Seul le contrat de développement change.

## Limites / risques
Les commits historiques restent inchangés. Les prochaines livraisons doivent respecter cette règle dès leur création.
