# Kristal Integration Pack — Konstellation × Kompiler × Local Kit

**Version de base : 0.1.0-alpha.1 — 8 octobre 2026**

**Mise à jour C5 (non publiée) :** le CLI accepte et vérifie les protocoles Kompiler 1.0/1.1 ; essais dédiés sur Kompiler `0.8.0-alpha.1` et Framework `10.0.0-draft.3.1`. L’overlay historique concerne **Konstellation**, pas Konstellation Light. Voir `docs/C5_KOMPILER_08.md`.

Pack d'intégration **non monolithique**, construit à partir des archives fournies :
Konstellation `1.0.0-rc.2`, Kompiler `0.7.0-alpha.3`, Kristal Framework
`10.0.0-draft.3`, Local Kit `3.2.4`, et prototype SemantiK français v3.

## Ce que ce pack fait vraiment

- Un **panneau Kompiler** s'ajoute à l'interface Konstellation existante.
- Le serveur Konstellation expose quatre routes de pont :
  `GET /api/kompiler/capabilities`, `POST /api/kompiler/validate`,
  `POST /api/kompiler/run`, `POST /api/kompiler/projection`.
- La passerelle REST est restreinte à l'API Kompiler locale, avec contrôle de scope `read` + `kompiler`, validation d'origine héritée de Konstellation, taille/temps limités.
- Le CLI exécute une requête **Kompiler** puis demande une projection v6 lorsque le Context Pack contient une Surface v7 appropriée. Il génère une **configuration Konstellation épinglée par SHA-256** et un reçu de provenance dans un dossier neuf.
- Le CLI peut appeler les fonctions **réelles** de Local Kit pour inspecter/valider; `build-v9` et `publish-v9` sont bloquées sans double opt-in explicite.
- L'installateur conserve les originaux et permet une restauration.

### Limitations cruciales

- `POST /v1/projections/v6` de Kompiler matérialise une **Surface v7**. Il **ne convertit pas tout état Kristal v9/v10 en document v6**. Kompiler peut lire certains états/pubs v9/v10 via ses adaptateurs, mais un lecteur/projeteur général Konstellation v9/v10 reste à qualifier.
- Les Context Packs sont des **lectures dérivées**, et une projection v6 n'est pas une preuve de vérité ou une republication de l'état engagé. Toute perte de couverture doit être consultée dans le Context Pack original.
- L'intégration n'ajoute **aucun** nouveau droit d'accès ; ne pas donner à Kompiler accès à un corpus plus large que le lecteur autorisé. En mode local, elle doit être activée explicitement ; en réseau, fournir des comptes et scopes dédiés.
- Alfresco n'est **pas** branché ; SemantiK et l'intégration Manager/Bootstrap complète ne sont **pas** inclus. Konstellation a déjà des points d'intégration SemantiK, mais le profil français candidat n'est pas un runtime de production qualifié.
- Installation UI testée par patch et syntaxe, **pas** qualifiée par un build Astro/Svelte complet (Node v24.15+ et dépendances absents de cet environnement).

## Structure du pack

```text
overlay/server/integrations/kompiler-bridge.mjs  API locale
  overlay/src/components/KompilerPanel.svelte    panneau dans Konstellation
  tools/install.py                               pose et restauration du patch
  tools/kristal-bridge.mjs                       CLI de passage entre outils
  examples/kristall-surface.query.json           requête de référence
  examples/kompiler-v7-projection-demo.json      véritable projection obtenue du runtime
  examples/demo-backend.json                     backend Konstellation de démonstration
  tests/                                        tests API/CLI/patch/schema
  docs/                                         qualification, sécurité, feuille de route
```

## 1. Pré-requis

- Un checkout **Konstellation `1.0.0-rc.2`** extrait de `SmartSnap(20261008-190258).zip`.
- Kompiler `0.7.0-alpha.3` installé avec l'option API (`python -m pip install -e '.[api]'` depuis son dépôt).
- Node.js **>=24.15** pour exécuter Konstellation. Le CLI est testable avec Node 22+.
- Framework v10 draft.3 (pour Kompiler) et Local Kit 3.2.4 si authoring voulu.

Sur le Framework exact fourni, le SHA-256 de `contracts/contract-set.json` est :

```text
1e516dd026bce754fd4f22b874ba2d603f64954831a1b5c754ecbb475d29020f
```

**Recalculer le hash sur ta copie** avant utilisation. Par exemple :

```powershell
(Get-FileHash 'C:\mycode\Kristal\Kristal-Framework\contracts\contract-set.json' -Algorithm SHA256).Hash.ToLower()
```

Configurer Kompiler (PowerShell) :

```powershell
$env:KOMPILER_KRISTAL_STANDARD_ROOT = 'C:\mycode\Kristal\Kristal-Framework'
$env:KOMPILER_KRISTAL_CONTRACT_SET_SHA256 = '1e516dd026bce754fd4f22b874ba2d603f64954831a1b5c754ecbb475d29020f'
# dans le checkout Kompiler
python -m kompiler serve --host 127.0.0.1 --port 7788
```

Dans un autre terminal :

```powershell
# Aperçu sans modification
python .\tools\install.py 'C:\mycode\Konstellation'
# Appliquer le pont
python .\tools\install.py 'C:\mycode\Konstellation' --apply

$env:KONSTELLATION_KOMPILER_URL = 'http://127.0.0.1:7788'
$env:KONSTELLATION_ENABLE_KOMPILER_LOCAL = 'true'
# pour Kompiler avec jeton, le passer par variable d'environnement seulement
# $env:KONSTELLATION_KOMPILER_TOKEN = 'secret local'

cd 'C:\mycode\Konstellation'
npm install
npm run build
npm start
```

Pour retirer le pont :

```powershell
python .\tools\install.py 'C:\mycode\Konstellation' --rollback
```

**Attention :** les chemins sont illustratifs ; adapte-les au répertoire réel des sources.

## 2. Essai CLI — parcourir un Kristal jusqu'à Konstellation

`doctor` interroge les capacités réellement offertes, notamment les identifiants de cibles.
La requête d'exemple est illustrative : adapter son `target` et ses paramètres à la cible annoncée.

```powershell
$env:KOMPILER_URL = 'http://127.0.0.1:7788'
node .\tools\kristal-bridge.mjs doctor
node .\tools\kristal-bridge.mjs run --query .\examples\kristall-surface.query.json --out .\resultats\context-pack.json
node .\tools\kristal-bridge.mjs project --pack .\resultats\context-pack.json --out .\resultats\projection

$env:KONSTELLATION_BACKEND_CONFIG = 'C:\...\Kristal-Integration-Pack\resultats\projection\konstellation-backend.json'
# redémarrer Konstellation : la sélection du backend est chargée au démarrage
```

La projection échoue normalement si le pack ne contient pas la Surface requise. Le CLI **n'invente jamais** des assertions manquantes.

### Démonstration sans requête Kompiler

Le fichier `examples/kompiler-v7-projection-demo.json` a été construit par le **vrai Kompiler** avec son fixture officiel v7. Il valide les schémas v6 Konstellation et Framework.

```powershell
$env:KONSTELLATION_BACKEND_CONFIG = 'C:\...\Kristal-Integration-Pack\examples\demo-backend.json'
# lancer Konstellation
```

Son contenu est **illustratif**, pas un corpus métier. L'absence de node_modules de Konstellation a empêché une vérification de rendu navigateur dans notre environnement.

## 3. Pilotage prudent du Local Kit

```powershell
node .\tools\kristal-bridge.mjs author --tool 'C:\mycode\Kristal\Kristal-Authoring-Kit\tools\kristal.py' --workspace 'C:\mycode\Kristal\Mon-Kristal' --action inspect
node .\tools\kristal-bridge.mjs author --tool 'C:\mycode\Kristal\Kristal-Authoring-Kit\tools\kristal.py' --workspace 'C:\mycode\Kristal\Mon-Kristal' --action check
```

Les opérations `build-v9` et `publish-v9` exigent **simultanément** `KRISTAL_ALLOW_WRITE=1` et `--confirm build-v9` ou `--confirm publish-v9`. Elles agissent sur ton vrai workspace, sont **désactivées par défaut** et doivent être précédées d'une sauvegarde. Le CLI appelle le Local Kit sans `shell` et n'introduit pas de nouvelle mécanique de publication.

## 4. Tester

```powershell
node --test .\tests\bridge.test.mjs
python -m unittest discover -s tests -p 'test_installer.py' -v
python .\tests\check_schemas.py --konstellation 'C:\mycode\Konstellation' --framework 'C:\mycode\Kristal\Kristal-Framework'
```

Le test d'installateur est exécuté pleinement quand la sauvegarde de checkout utilisée pour sa qualification est présente ; sinon il est marqué *skip*.

## 5. Suite logique

Lire `docs/PLAN_EXECUTION.md` et `docs/QUALIFICATION.md` pour distinguer les opérations terminées, partielles et non exécutées. Maintenir les dépôts séparés ; le pack contient des ajouts et des adaptateurs ciblés, pas une copie de tous les projets ni d'Alfresco.
#   K r i s t a l - I n t e g r a t i o n - P a c k  
 