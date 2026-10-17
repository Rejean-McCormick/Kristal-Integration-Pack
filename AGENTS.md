# Integration Pack — responsabilités et règles de sécurité

- Cible de lecture : Framework v11 **11.0.0-draft.4** verrouillé avec SHA-256. Ne jamais affaiblir `verify_framework` ni accepter un checkout inattendu.
- `tools/v11_integration.py` produit uniquement des projections dérivées; les termes restent dans `presentation`, jamais dans KQ/KP/KA/KS.
- `tools/v11_handoff.py` vérifie des échanges **en lecture seule** ; il ne doit jamais lancer `import-dik-catalog`, `select-v11-catalog`, des migrations ou des routes HTTP d'autorité.
- diK alpha.7 gère les dictionnaires ; l'Authoring Kit draft.3 gère le canon, l'enregistrement et la sélection du catalogue ; Konstellation est le navigateur, Manager le registre d'instances.
- Un reçu `dik-job.json` est un contrôle d'intégrité ; même un SHA-256 correct n'est pas une signature Wikidata ni une approbation sémantique.
- Ne pas réinstaller l'overlay Kompiler historique sur une Konstellation déjà intégrée ; conserver le refus `DO_NOT_REINSTALL_EXISTING_INTEGRATION`.
- Avant toute release : tests Node et Python avec et sans le checkout Framework épinglé, manifest SHA-256 exact, ZIP vérifié après extraction.
- Toute modification de contrat normatif nécessite validation, nouvelle version et décision humaine ; ne jamais inventer un `exactMatch` par lexique.
