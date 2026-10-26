# Back-office Assistant Docker MAIN v1.6a(134)

Accès : `http://127.0.0.1:18713/backoffice`.

- `GET /api/backoffice/inference` consulte le moteur llama.cpp sur `host.docker.internal:18720/health` et `/v1/models`. **Limite de réseau** : selon le binding loopback Docker Desktop, le port hôte peut ne pas être accessible depuis le conteneur Web ; la recette réelle est obligatoire et aucun état READY n'est revendiqué avant validation.
- `GET /api/backoffice/recordings?title=...&artist=...` interroge une adresse MusicBrainz fixe, filtre les candidats titre + artiste et refuse d'en déduire un verdict musical.
- `/backoffice` présente les résultats avec liens externes sécurisés.
- Aucune écriture en base Assistant, aucun secret transmis, aucune recherche Web sur une URL arbitraire.
- Aucun run LAB acheminé : le workflow LAB → Orchestrator → Assistant → LAB, l'identification exacte et les verdicts documentaires restent **non livrés**.
- Aucun changement au GPU, LAB, EZScore, au service historique de la page `/` ni au backend Orchestrator.

Sur MAIN :
```powershell
cd H:\EZStudioLab_assistant
git pull --ff-only origin assistant-main
docker compose -f docker/main/compose.yaml --profile smoke build assistant-web-smoke
docker compose -f docker/main/compose.yaml --profile smoke up -d --no-deps --force-recreate --no-build assistant-web-smoke
Invoke-RestMethod http://127.0.0.1:18713/api/backoffice/inference | ConvertTo-Json
```
Puis ouvrir `http://127.0.0.1:18713/backoffice` et lancer une recherche. Seul le Web est reconstruit ; CUDA n'est pas redémarré.
