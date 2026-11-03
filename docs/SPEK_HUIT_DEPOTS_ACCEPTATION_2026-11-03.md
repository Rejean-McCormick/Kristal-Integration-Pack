# Spek : recette coordonnée huit dépôts — 2026-11-03

## Livrable

`tools/spek_ecosystem_readiness.py` exécute les vrais exécutables locaux des
huit dépôts et rend un rapport machine sans publier ni modifier les sources.
Un succès de contrat n'est **pas** une preuve de génération de texte GF/PGF.

Cette passe crée un échange privé `spek.private-editorial-handoff/1.0` :
la composition et les demandes SemantiK doivent partager les mêmes assertions.
Une table v6→v11 explicite est requise lorsque les identités diffèrent.

## Résultats du test sur les archives fournies

- **Agriculture original (51 champs)** : verrou refusé car
  `limites.portee` ne référence aucune assertion.
- **Variante source-bound (50 champs)** : Spek verrouille 3 templates et
  50 demandes, Manager vérifie les 25 identités par table v6→v11,
  Architect valide les 50 requêtes avec ses contrats propres.
- **RuntimeSet Agriculture** : bloqué car profil non activé et `.pgf`
  réel absent.
- **Arketype** : 19 archétypes et 57 correspondances candidates
  rhétoriques, vérifiées contre les 62 définitions Spek.
- **Framework** : schéma privé séparé du canon.
- **kristal-public** : présence de la frontière de publication ; aucun
  test d'autorisation signé n'a été engagé dans ce scénario.

## Interdictions

Ni cet outil, ni le verrou, ni un test de recette ne peuvent choisir des
faits, attester des relations argumentatives, approuver C1/C2/C3, créer des
phrases de substitution, activer un RuntimeSet ou déclencher GitHub.
