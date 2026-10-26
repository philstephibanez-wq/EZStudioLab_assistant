# Première recherche documentaire indépendante — v1.6a(133)

`runtime/recording_discovery.py` interroge l'API publique MusicBrainz (catalogue externe indépendant de LAB) sur le titre et l'artiste, avec requête encodée, délai 20 s et limite de réponse. La correspondance normalisée produit **des enregistrements candidats**, avec MBID et URL sur MusicBrainz. **Ni un MBID, ni un match titre/artiste ne prouvent que la version/enregistrement analysé est le même** : pas de jugement sur la tonalité, tempo, instruments, etc. Aucune note de confiance fabriquée.

Module volontairement non raccordé automatiquement au worker : ne pas envoyer des requêtes vers MusicBrainz à chaque test ni faire tourner plusieurs instances. Test unitaire avec faux client réseau, aucun trafic sortant pendant les tests.

Pour valider sur MAIN :
```powershell
cd H:\EZStudioLab_assistant
git pull --ff-only origin assistant-main
python -m unittest discover -s tests -p test_recording_discovery.py
```

**Non livré** : rapprochement sûr de la version exacte (ISRC/release/audio), recherche d'autres sources, récupération et analyse de pages, preuves par assertion, verdicts BON/FAUX, persistance LAB et UI. Le moteur LAB et son architecture scientifique restent hors de portée de l'Assistant. Aucune modification de Docker ou des services.
