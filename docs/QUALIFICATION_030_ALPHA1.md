# Integration Pack 0.3.0-alpha.1 — qualification locale d'écosystème

**Date : 17 octobre 2026.** Ce document qualifie une intégration candidate **de lecture**, pas une release de production ou une migration de canon.

## Versions concernées

| Composant | Profil |
|---|---|
| Integration Pack | `0.3.0-alpha.1` |
| Kristal Framework | `11.0.0-draft.4`, **13 fichiers épinglés SHA-256** |
| diK | `1.0.0-alpha.7`, format de sortie attendu `dik.large-import/1.0-candidate` |
| Kristal Authoring Kit | `4.0.0-draft.3`, sélection explicite `import-dik-catalog` / `select-v11-catalog` |
| Arketype | `1.6.0`, constructeur de modèles, **aucune autorité de registre** |
| Konstellation / Kompiler | Historique v6/v10 conservé, aucun redéploiement |

## Tests exécutés

- Python **29 tests réussis** avec `KRISTAL_FRAMEWORK_ROOT` épinglé et `KRISTAL_AUTHORING_KIT_ROOT` local. Comprend les tests d'installation historique, de C3, les 13 scénarios du lecteur v11 et les cas de précontrôle diK/Kit.
- Node **15 tests réussis** contre le Framework draft.4, avec contrôle de vue dérivée, routage CLI en liste blanche, compatibilité structurelle de vue draft.3 et vérification CLI réelle du Framework.
- Précontrôle en lecture du catalogue v11 réel de l’exemple Framework : couverture française canadienne avec repli, namespace, sources/crosswalks et SHA-256 vérifiés; **aucune activation**.
- Vérification du refus des couches `curated` dans un catalogue entrant réservé à Wikidata, corruption du hash d'une couche, namespace incohérent, absence de mode Kit pour un reçu alpha.7, reçu de version non reconnue et tentative d'écrasement d'une sortie.
- Scénario croisé **réel avec l'Authoring Kit 4.0.0-draft.3** sur une **copie temporaire** de `demo-semantic-v11` : précontrôle Framework draft.4 → `import-dik-catalog --register` → `select-v11-catalog` → `check-v11`, intégrité du graphe avant/après confirmée.
- Le profil de projection dérivée `kristal.integration.read-view/v11.0-draft.1` est conservé ; ses métadonnées signalent désormais Framework draft.4. Les vues antérieures portant draft.3 restent structurellement lisibles par le consommateur JS.

## Ce qui n'a pas été testé ou établi

- **La sortie exacte d'une exécution binaire de diK alpha.7 n'a pas été produite dans cette qualification.** Le contrôle de son reçu `dik-job.json` repose sur un test synthétique de forme, de hachage et de clé d'idempotence conforme au contrat documenté, pas sur un dump local réel.
- Aucune installation Konstellation, compilation Astro/Svelte, navigateur, routage HTTP public, Reader Policy C1/C2 ou déploiement Kubernetes/GitHub vérifié.
- Aucune nouvelle qualification de l'API Kompiler 0.8 ou de projections historiques sur un serveur distant.
- Aucun dump Wikidata massif, aucune gouvernance multi-utilisateur signée, aucune restauration après panne système et aucun TCK diK complet exécuté.
- L'Authoring Kit draft.3 conserve son pin d'origine draft.3 ; sa mise à jour propre à draft.4 reste un travail du dépôt Kit. Les schémas v11 utilisés ne changent pas de contenu entre ces deux drafts.

## Conclusions et décisions

Le Pack 0.3 est **aligné sur les contrats de lecture de Framework draft.4** et ajoute une porte de contrôle explicite entre les résultats lexicaux diK et le Kit. Il n’est ni éditeur canonique ni autorité d'approbation. Le dispositif s’arrête à un rapport `preflight_pass` : seule une opération distincte du Kit peut enregistrer puis sélectionner une nouvelle révision, après revue.

Les tests utilisent les artefacts de référence fournis localement. Une release stable exige encore tests croisés à partir des binaires distribués, politiques d'accès, utilisation réelle avec des jeux de données représentatifs et qualification sur l'hôte Konstellation cible.
