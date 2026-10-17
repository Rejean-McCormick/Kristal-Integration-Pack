> **Historique uniquement :** ce rapport concerne Integration Pack **0.2.0-alpha.1** avec Framework draft.3 et Kit draft.1. Pour la nouvelle version, consulter [QUALIFICATION_030_ALPHA1](QUALIFICATION_030_ALPHA1.md).

# Qualification de la candidate 0.2.0-alpha.1 — édition 2026-10-16

## Base testée

- Integration Pack à partir de `0.1.0-alpha.2` conservé, puis ajout séparé v11.
- Framework `11.0.0-draft.3` fourni par snapshot ZIP, empreintes de ses contrats et trois validateurs/outils vérifiées via `contracts/v11-framework-pin.json`.
- Authoring Kit `4.0.0-draft.1` consulté pour la répartition des responsabilités, **sans qualifier un déploiement conjoint complet**.
- diK `0.1.0` n'est pas requis pour faire fonctionner `view` et `coverage`, car le Pack consomme les contrats de référence du Framework.

## Résultats exécutés

- JS `node --test tests/*.test.mjs` avec checkout Framework exact : **13 réussis, zéro échec, zéro ignoré**.
- Python tests de base C3 + installateur : **6 réussis**.
- Python tests v11 avec checkout Framework exact : **13 réussis**.
- Exemple synthétique Framework v11 : `check`, rapport de complétude `fr-CA,en`, lecture en français canadien, repli explicite, déclaration `missing` pour KP absent, référence externe exacte `Q8018` uniquement pour KQ1001.
- Vérification que les champs de prédicat textuels, les couches lexicales corrompues, les alignements Wikidata non approuvés et les sorties préexistantes sont refusés.

## Limites explicites

Les tests ci-dessus ne prouvent PAS que les routes réelles de Konstellation, les politiques de lecture, l'exécution Kompiler C5 distante, l'installation GitHub, les migrations de Kristals historiques, un dump Wikidata massif ou 300 langues ont été qualifiés. Les contrôles du consommateur JavaScript sont structurels : seule la validation Framework épinglée traite les références et preuves canoniques. Toute intégration hôte exige une revue de son propriétaire et une nouvelle qualification de bout en bout.

L'exécution regroupée de toute la suite Python avec l'environnement d'intégration activé a été interrompue dans l'environnement d'exécution ; les deux sous-suites (6 + 13 tests) ont ensuite été exécutées **séparément** avec succès. Il serait inexact de présenter le premier essai groupé comme réussi.
