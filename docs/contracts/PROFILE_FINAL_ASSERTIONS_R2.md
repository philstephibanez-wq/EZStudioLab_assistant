# PROFILE — R2 : raccordement conservateur des assertions finales dynamiques

## Autorité

`AGENTS.md`, Assistant #11/#12, LAB #17, contrat de développement Orchestrator, et contrat universel PROFILE. L'Assistant ne juge **que** des valeurs musicales finales LAB, jamais ses moteurs, scores scientifiques, modèles ou presets. La base MAIN LAB demeure autorité métier ; Reports est l'archive expurgée, non la base.

## Entrée et comportement

- Le format historique à dix `items` est préservé pour les clients existants.
- Si `final_assertions_schema=ezstudio.profile-final-assertions.v1`, `final_assertions` et `final_assertions_count` sont présents, chaque assertion publique `{id, dimension, value}` est projetée sans champs techniques supplémentaires.
- Identifiants uniques et conformes, cardinalité exacte, valeurs atomiques finies, dimensions musicales connues ; tout inventaire invalide est rejeté avant une recherche. Aucun plafond arbitraire n'est posé à la liste des instruments.
- Les instruments `instruments:N` deviennent des recherches distinctes `instrument:N`, sans prétendre que `instruments` est un instrument unique. Tempo numérique converti en BPM uniquement pour la recherche ; la valeur LAB originale est conservée dans la sortie.
- Les sorties `final_reviews` sont alignées un pour un, dans l'ordre, avec les assertions reçues. Verdict par défaut `non_trouve`, confiance nulle, absence de preuve validée ; les pages simplement découvertes ne sont jamais promues au rang de preuve exacte.
- Les dix `reviews` existantes sont conservées sans altération de schéma. Pour le nouveau chemin, la consultation IA historique limitée à dix champs n'est **pas** appelée : elle ne couvrirait pas correctement l'inventaire dynamique. Recherche documentaire des assertions dynamiques oui ; synthèse IA héritée non, tant qu'elle n'est pas correctement adaptée.
- Si le payload n'expose pas `final_assertions`, l'ancien fonctionnement est conservé. Un inventaire explicitement vide ne lance aucune recherche.

## Validation R2 et limites

Les tests unitaires vérifient cardinalité libre des instruments, identifiants stables, filtrage de données scientifiques, abstention, absence d'invention, préservation legacy et zéro recherche sur liste vide. Un test déterministe ne prouve pas la recherche Web, le lien au bon enregistrement ni la persistance réelle de `final_reviews` dans LAB.

**Non livré :** preuve BON/FAUX fiable par enregistrement, enrichissement IA pour chaque assertion, reconnaissance de dimensions musicales nouvelles hors dictionnaire connu, intégration/UI LAB de `final_reviews`, calibrage, recette HTTP réelle et archivage exhaustif d'un nouveau run. À traiter en tranche distincte sans casser R2.

## Impacts et frontières

Seul Assistant `assistant-main` évolue, version 1.7a14 ; LAB, Orchestrator, Reports, EZScore, STEMS/CHORDS-N/LYRICS, modèles, presets, queues, jobs et services restent intacts. Pas de redémarrage implicite. Toute activation opérationnelle du nouvel échange demeure subordonnée à une recette réelle et à l'acceptation du contrat LAB ; rollback de sources uniquement, aucun nettoyage de rapports.
