# Changelog

## 0.3.0-alpha.1 — 2026-10-17 — Framework v11 draft.4 et échanges diK/Kit

- Verrou Framework exact révisé pour `11.0.0-draft.4` (13 fichiers : 8 schémas v11, `VERSION` et 4 outils ; contrats et validations existants conservés). 
- Ajout de `tools/v11_handoff.py`, contrôle en lecture seule des catalogues et de la provenance SHA de l'import diK alpha.7, fondé sur le vrai `tools/v11/interop_preflight.py` épinglé.
- Commande Node `v11-handoff` avec liste explicite d’options autorisées ; aucun accès réseau, aucun import, sélection ou activation automatique.
- Adaptateur d'affichage Node : vues source Framework draft.3 et draft.4 admises ; nouveaux read-view émis avec la référence draft.4, profil de projection inchangé.
- Tests de refus et d'intégration avec Framework draft.4 et Authoring Kit draft.3 dans un workspace temporaire ; aucune modification des originaux.
- Overlay Kompiler v6/v10, installateur, politique de non-réinstallation Konstellation et commandes historiques préservés ; aucune qualification production implicite.

## 0.2.0-alpha.1 — 2026-10-16 — Framework v11 read interoperability

- Adds pinned, **read-only** v11 semantic adapter (`tools/v11_integration.py`) for registry/graph/crosswalk/catalog validation, diK-compatible coverage and separately labeled read views.
- Adds `v11` to the strictly allowlisted Node CLI without changing legacy Kompiler 1.0/1.1 / derived-v6 commands.
- Adds a non-installed read-view consumer guard (`overlay/server/integrations/kristal-v11-read-view.mjs`).
- Enforces KQ/KP source references, audited Wikidata exact matches, deterministic language fallback, lexical layers and explicit Framework draft.3 SHA pinning.
- Adds tests and exact-scope qualification documentation. No automatic install, public sync, semantic conversion or publication.

## 0.1.0-alpha.2 — historical v10 candidate

The source 0.1.0-alpha.2 is preserved as the pre-v11 baseline. Details in `docs/ALIGNMENT_V10.md` and `docs/QUALIFICATION.md`.
