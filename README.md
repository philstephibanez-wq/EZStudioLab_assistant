# EZStudioLab Assistant

## Architecture Web 1.3

Assistant XPS = Caddy + Symfony + Twig + Monolog + jQuery + Python.

- REST uniquement avec LAB.
- SMB uniquement pour les modèles IA.
- Aucune base de données Assistant.
- Toute persistance métier appartient à LAB.
- Racine d'installation XPS : `C:\EZStudioLab_assistant`.

Démarrage canonique depuis `EZStudioLab_assistant` : `./scripts/start.cmd`.
Interface : `http://EZSTUDIO-XPS:8712/`.
