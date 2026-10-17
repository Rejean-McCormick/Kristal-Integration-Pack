# Alignement Kristal Framework v11 / diK / Authoring Kit — Integration Pack 0.3.0-alpha.1

**Statut :** adaptateur de lecture v11 en candidat, **non publié dans Konstellation**. Ce travail étend le Pack 0.1.0-alpha.2 en conservant le pont Kompiler historique v6/v10, son installateur et ses garanties. Il ne change ni l'autorité sémantique ni les règles d'accès des applications hôtes.

## Propriétés garanties par l'adaptateur

1. **Identités canoniques** : un graphe source contient uniquement des KQ/KP/KA/KS dans les champs d'identité, avec `(namespace_id, id)` comme clé logique. Les Q/P Wikidata sont uniquement des correspondances externes `accepted + exactMatch` contrôlées par le Framework.
2. **Lexique hors graphe** : toutes les étiquettes sont dans `presentation[].lexical` du fichier *dérivé*, jamais substituées aux identifiants du graphe. Citations et littéraux d'assertions restent des valeurs de données.
3. **Souveraineté des dictionnaires** : le Framework v11 draft.3 audite catalogue, SHA-256 de toutes les couches, sources Wikidata autorisées, provenances, priorité et replis linguistiques explicites. Le Pack délègue cette responsabilité et n'invente pas un nouveau résolveur d'identité.
4. **Complétude** : la commande `coverage` appelle directement le rapport de référence `kristal_dik_coverage_report` du Framework, sans fusionner repli et traduction directe.
5. **Provenance et pinning** : `contracts/v11-framework-pin.json` lie cette candidate à la version `11.0.0-draft.4` et aux empreintes exactes des schémas et outils consommés, dont `interop_preflight.py`. Les schémas v11 conservent leurs octets depuis draft.3. Tout changement doit être revu et repinné explicitement.
6. **Lecture seule** : `check`, `coverage` et `view` ne modifient jamais un graphe, registre, crosswalk, catalogue ou couche lexicale. `--out` crée un *nouveau* fichier par création exclusive (échec s'il existe).
7. **Aucune automatisation de la migration** : les plans diK et l'application de conversions appartiennent à diK / Authoring Kit, pas à ce Pack. `closeMatch`, `candidate` et les égalités de mots ne deviennent pas des identités.

## Contrats produits et consommés

| Entrée ou sortie | Autorité | Usage |
|---|---|---|
| `kristal_semantic_graph`, `kristal_identity_registry` | Framework v11 | Entrées canon, validées en lecture |
| `kristal_external_crosswalk` | Framework v11 | Références Wikidata externes, preuve `KS` |
| `kristal_dictionary_catalog` + couches | Framework v11 / diK | Lecture de labels, priorités, hash et repli |
| `kristal_dik_coverage_report` | Framework v11 | Sortie de `coverage`, certitude de couverture lexicalement bornée |
| `kristal.integration.read-view/v11.0-draft.1` | Ce Pack | **Projection non canonique** de présentation, assertions KQ/KP intactes |
| `kompiler.context-pack/1.0-1.1` / projection v6 | Kompiler | Compatibilité historique, **pas** un décodeur générique v11 |

## CLI depuis le dépôt du Pack

Prérequis : Python 3.11+ avec `jsonschema` (comme Framework v11), Node 22+ pour le point d'entrée Node ; prévoir Node 24.15+ pour les environnements historiques de Konstellation.

```bash
export KRISTAL_FRAMEWORK_ROOT=/chemin/vers/kristal-11.0.0-draft.4
S="$KRISTAL_FRAMEWORK_ROOT/examples/v11"
COMMON=(--framework "$KRISTAL_FRAMEWORK_ROOT" \
  --registry "$S/identity-registry.example.json" \
  --graph "$S/semantic-graph.example.json" \
  --crosswalk "$S/external-crosswalk.example.json" \
  --catalog "$S/dictionaries/catalog.json")
python tools/v11_integration.py check "${COMMON[@]}"
python tools/v11_integration.py coverage "${COMMON[@]}" --locales fr-CA,en --out ./coverage-report.json
python tools/v11_integration.py view "${COMMON[@]}" --locale fr-CA --out ./view-fr-CA.json
node tools/kristal-bridge.mjs v11 --operation view "${COMMON[@]}" --locale fr
```

### Garantie de la projection dérivée

- `source`: namespace, graph ID, empreintes SHA-256 des quatre entrées, version exacte du Framework.
- `presentation`: KQ et KP distincts, status `direct`/`fallback`/`missing`, termes résolus et provenance de couche ; référence Wikidata uniquement si correspondance exacte acceptée.
- `assertions`: assertions source **inchangées**, références KQ/KP/KA/KS ou valeurs typées.
- `derived_only: true`: ne vaut ni engagement v9, ni nouveau graphe v11, ni preuve d'identité ou d'autorisation.

Le consommateur Node `overlay/server/integrations/kristal-v11-read-view.mjs` effectue une **vérification structurelle défensive** du format `read-view`; il ne remplace PAS la validation Framework et ne vérifie pas les fichiers canoniques sous-jacents. Il n'est pas activé automatiquement comme une route réseau.

## Régression et protocole de qualification

```bash
node --test tests/*.test.mjs
python -m unittest discover -s tests -p 'test_*.py' -v
# Validation réelle du Framework (pas exécutée automatiquement par CI sans checkout explicite)
KRISTAL_FRAMEWORK_ROOT=/chemin/kristal-11.0.0-draft.4 node --test tests/v11.test.mjs
KRISTAL_FRAMEWORK_ROOT=/chemin/kristal-11.0.0-draft.4 python -m unittest tests.test_v11_integration -v
python tools/verify_manifest.py
```

**Refus testés** : propriété textuelle, Q Wikidata utilisé comme KQ, couches modifiées après hachage, Wikidata sans exactMatch accepté, mauvais namespace, conflit lexical, écrasement de sortie, dérive des outils/schémas Framework, entrée/projection invalide.

**Non qualifié / hors périmètre** : installation sur un Konstellation existant, build Astro/Svelte, parcours navigateur, politique de lecture multiutilisateur, authentification C1/C2, publication distante, migration diK/Authoring Kit, performance de 300 langues en production. L'overlay v10 ne doit pas être réinstallé sur une application Konstellation déjà intégrée.


## Handoff diK alpha.7 → Authoring Kit draft.3

Le précontrôle additionnel `tools/v11_handoff.py` lit les vrais contrats épinglés du Framework draft.4 et refuse les couches non Wikidata si `--kit-import-candidate` est sélectionné. Son contrôle facultatif de `dik-job.json` confirme l'association entre le catalogue, le registre et le crosswalk approuvés. **Le reçu ne prouve pas une approbation humaine ou l'origine Wikidata.**

Les commandes `import-dik-catalog`, `select-v11-catalog` et `recover-v11` demeurent des opérations de l'**Authoring Kit**. Ce Pack ne les exécute jamais automatiquement et ne modifie pas le graphe canonique. Le profil dérivé `kristal.integration.read-view/v11.0-draft.1` reste inchangé ; le lecteur Node admet les anciennes vues draft.3 ainsi que les vues draft.4.

Voir [DIK_KIT_HANDOFF_V11](DIK_KIT_HANDOFF_V11.md) et [Qualification alpha.3](QUALIFICATION_030_ALPHA1.md) pour la preuve réellement exécutée et les limitations.
