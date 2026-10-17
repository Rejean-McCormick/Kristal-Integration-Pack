# diK alpha.7 → Integration Pack 0.3 → Authoring Kit draft.3

## Périmètre et autorités

**Framework v11 draft.4** : source de vérité pour les identifiants KQ/KP/KA/KS, les schémas, audits, lexiques et preuves de correspondances `accepted + exactMatch`.

**diK 1.0.0-alpha.7** : fabrique des snapshots lexicaux et des propositions de correspondances. Le nouveau `sync import-large` produit `catalog.json`, des couches JSONL et `dik-job.json` (source SHA-256, crosswalk, registre, paramètres d'import). Un hash local n'authentifie pas la provenance des octets Wikidata.

**Integration Pack 0.3.0-alpha.1** : **consommateur non canonique en lecture seule**. Son précontrôle appelle `tools/v11/interop_preflight.py` épinglé, puis vérifie facultativement le reçu alpha.7. Le Pack ne réécrit aucun dictionnaire, ne transforme aucun mot en identité, ne publie ni n'active de catalogues.

**Authoring Kit 4.0.0-draft.3** : valide à nouveau le catalogue du projet, enregistre une nouvelle révision en tant qu'artefact logique et n'en change la sélection active que par commande explicite. Les corrections curatées historiques restent séparées des nouveaux lexiques Wikidata.

## 1. Précontrôle de lecture sur un catalogue v11 déjà existant

```bash
FW=/chemin/vers/Kristal-Framework-v11.0.0-draft.4
S="$FW/examples/v11"
python tools/v11_handoff.py --framework "$FW" \
  --catalog "$S/dictionaries/catalog.json" \
  --registry "$S/identity-registry.example.json" \
  --crosswalk "$S/external-crosswalk.example.json" \
  --graph "$S/semantic-graph.example.json" --locales fr-CA,en
```

Aucun des quatre originaux n’est modifié. Sans graphe, omettre `--graph` et `--locales`, et le rapport valide simplement les métadonnées de provenance et les dictionnaires.

## 2. Précontrôle strict d'un nouvel import diK alpha.7

```bash
python tools/v11_handoff.py --framework "$FW" \
  --catalog /nouveau-import/catalog.json \
  --registry /projet/registry.json \
  --crosswalk /projet/crosswalk.json \
  --kit-import-candidate \
  --dik-job /nouveau-import/dik-job.json \
  --out /rapports/dik-kit-preflight.json
```

Ce mode exige un catalogue contenant **uniquement des couches entrantes de type `wikidata`**, et compare les SHA-256 du reçu avec celui du catalogue, du registre et du crosswalk. Il refuse les entrées à hash modifié, namespace incohérent et couches non admises. La source Wikidata et l'approbation effective de `exactMatch` doivent être vérifiées au-delà de ce reçu.

Pour passer par Node : `node tools/kristal-bridge.mjs v11-handoff --framework ... --catalog ... --registry ... --crosswalk ... --kit-candidate yes --dik-job ...`.

## 3. Adoption explicite **uniquement par l'Authoring Kit**

Après revue, dans le dépôt du Kit :

```bash
python tools/kristal.py import-dik-catalog /workspace \
  --catalog /nouveau-import/catalog.json --revision revison-humaine-001 \
  --register --artifact-id urn:review:001 --contract-id projet.dictionary.v11
python tools/kristal.py select-v11-catalog /workspace \
  --catalog <chemin-retourne-par-import-dik-catalog>
python tools/kristal.py check-v11 /workspace
```

Les chemins, droits et artefacts doivent être contrôlés par l'opérateur. Les commandes sont présentées comme un exemple de workflow, **pas** déclenchées par le Pack. En cas de crash Kit, utiliser les modes `recover-v11 status|finish|rollback` selon le journal; ne pas improviser une réparation à la main.

## Sécurité et version

- Le Pack verrouille **exactement Framework `11.0.0-draft.4`** et 13 fichiers du contrat/outillage v11 par SHA-256. Il rejette un Framework inattendu au lieu d'exécuter du code d'une autre version.
- Les schémas v11 et les outils de lecture utilisés gardent les octets observés en draft.3 ; le précontrôle draft.4 est un ajout. Le Kit draft.3 conserve son pin Framework draft.3, ce qui demande une nouvelle qualification lorsqu'il évoluera.
- Le lecteur Node accepte les vues `read-view/v11.0-draft.1` générées depuis Framework draft.3 ou draft.4, **sans** confondre cette vérification structurelle avec une validation canonique.
- Pas de réseau, de téléchargement de dump, d'agent partagé, de fusion de KQ, d'équivalence par libellé ni de modification Konstellation.
- Le Pack **ne réinstalle pas** les overlays historiques sur une instance Konstellation déjà intégrée. Son installateur reste strict.

## Qualification requise avant une release stable

Déploiement autonome sur un Konstellation de test; politiques de lecteur C1/C2; intégration réelle avec un binaire diK alpha.7 et ses gros dumps; authentification des réviseurs; conditions de panne et concurrence Kit; TCK Framework complet; compatibilité Node/Astro/Svelte sous les versions d'exploitation cibles.
