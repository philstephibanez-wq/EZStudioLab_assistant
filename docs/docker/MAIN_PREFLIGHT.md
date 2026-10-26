# Assistant Docker MAIN — tranche Web smoke v1.6a(127)

## Portée

MAIN est la cible Docker décidée le 26 octobre 2026. Branche `assistant-main` uniquement ; `main` reste la lignée XPS. Ce premier emballage est **un smoke-test Web Symfony**, pas une migration complète de l'Assistant : aucun worker, guardian, Qwen, GPU, Caddy ni flux métier LAB ne démarre. Le contrat métier reste Assistant #11/#12 : les seules assertions musicales finales de LAB sont vérifiées indépendamment ; aucune expertise des moteurs.

## Préflight

Depuis la copie MAIN de la branche `assistant-main` :

```powershell
docker version
docker compose -f docker/main/compose.yaml --profile smoke config
docker compose -f docker/main/compose.yaml --profile smoke build assistant-web-smoke
```

Ce build peut télécharger des images publiques et des dépendances Composer ; il ne modifie pas les services en cours. Avant de démarrer, vérifier que `127.0.0.1:18713` est libre.

## Démarrage volontaire, sans bascule

```powershell
docker compose -f docker/main/compose.yaml --profile smoke up -d assistant-web-smoke
docker compose -f docker/main/compose.yaml --profile smoke ps
Invoke-WebRequest http://127.0.0.1:18713/ -UseBasicParsing
docker compose -f docker/main/compose.yaml --profile smoke logs --tail 80 assistant-web-smoke
```

Une réponse HTTP autre que 200 peut refléter une configuration Symfony manquante ; analyser les logs et ne pas conclure à un service métier fonctionnel. Le port `18713` est local, distinct de `8712/8713`, `8700`, `8501/8502/8702`. Ne pas utiliser les tokens réels pour ce smoke-test.

Arrêt ciblé :

```powershell
docker compose -f docker/main/compose.yaml --profile smoke down
```

## Contraintes et limites

- Aucune base métier sur MAIN ; persistance des vérifications reste dans LAB.
- Modèles maîtres sur MAIN sans copie en image ; GPU/Vulkan non implémenté et non revendiqué.
- Aucun montage SMB/UNC ou secret DPAPI dans un conteneur Linux à cette étape.
- `APP_SECRET` défini ici n'est **que** pour l'instance de test isolée ; aucun accès LAB, aucun usage production.
- Aucun conteneur lancé ni test MAIN exécuté par cette publication. La validation en environnement Windows/Docker reste à faire.
- Bascule, networking Caddy, services Python, singleton, authentification, stockage, IA et rollback à traiter dans les tranches suivantes après validation de cette étape.
