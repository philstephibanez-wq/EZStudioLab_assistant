# Écart bloquant contrat #11 — v1.6a(137)

Le formulaire de recherche MusicBrainz est retiré de l'accueil : il donnait l'impression d'une recherche documentaire ouverte alors que l'endpoint ne consultait qu'un catalogue. L'endpoint technique `/api/backoffice/recordings` subsiste pour rétrocompatibilité mais n'est pas appelé par l'accueil. Le moteur Web ouvert, les ensembles réellement calculés et les verdicts ne sont PAS implémentés. Ce correctif retire une interface trompeuse et **ne résout pas** l'écart métier canonique. Les données du LAB et CUDA ne sont pas modifiées.
