# Kristal Integration Pack

**Version:** `0.3.0-alpha.1`  
**Status:** Integration candidate — tested locally, not production-qualified  
**Framework target:** `11.0.0-draft.4`

The **Kristal Integration Pack** connects the Kristal ecosystem without merging its tools or changing their responsibilities. It provides a read-only Framework v11 reader, a guarded handoff from diK to the Kristal Authoring Kit, and a separate compatibility bridge for historical Kompiler/Konstellation workflows.

It is **not** a semantic authority, a dictionary approval service, a publisher, or a replacement for Framework validation.

## Compatibility at a glance

| Component | Supported or documented baseline | Integration scope |
| --- | --- | --- |
| Kristal Framework | **11.0.0-draft.4** | Exact checkout required; 13 contract/tool files pinned by SHA-256 |
| Kristal Authoring Kit | **4.0.0-draft.4** (lot 1 candidate) | Separate, explicitly approved catalog import and selection |
| diK | **1.0.0-alpha.7** | Read-only validation of incoming catalogs and optional import receipts |
| Arketype | **1.6.0** | Ecosystem compatibility reference; no runtime integration claimed |
| Kompiler | Historical **0.8.0-alpha.1** compatibility profile | Context Pack and eligible v7 Surface → v6 projection |
| Konstellation | Historical **1.0.0-rc.2** overlay target | Opt-in legacy installation only on a verified, unmodified checkout |

The Authoring Kit draft.4 lot-1 candidate now uses this exact 13-file Framework draft.4 pin. Earlier Kit draft.3 packages remain pinned to draft.3 and are not silently upgraded. The Pack never registers, selects, activates, or publishes authoring changes.

## What the Pack provides

- **Framework v11 validation:** `check` validates canonical graph identifiers, identity registry, approved Wikidata crosswalks, catalog metadata, and lexical layers through the pinned Framework tools.
- **Language coverage:** `coverage` keeps *direct*, *fallback*, and *missing* terms distinct.
- **Derived reading views:** `view` creates a non-canonical presentation for a selected locale, preserving KQ/KP identity references and source assertions.
- **diK → Authoring Kit preflight:** `v11-handoff` checks an incoming catalog and, optionally, a diK alpha.7 `dik-job.json` receipt; it does **not** register, select, activate, or publish anything.
- **Historical Kompiler bridge:** guarded Context Pack creation and v6 projection when an appropriate v7 Surface exists.
- **Legacy Konstellation overlay:** inspect, preview, and conditionally install or roll back an integration on an eligible historical checkout. **Never force-reinstall over an already integrated Konstellation.**

## Requirements

- **Python 3.11+**, with `jsonschema` available for the Framework v11 tools.
- An **exact Kristal Framework 11.0.0-draft.4 checkout** for v11 commands. The Pack checks its `VERSION` and the digests in [`contracts/v11-framework-pin.json`](contracts/v11-framework-pin.json).
- **Node.js 22+** for the standalone Node bridge. The historical Konstellation release environment requires **Node.js 24.15+**.
- The Authoring Kit checkout only when an operator actually performs an approved catalog import or selection; the Pack does not distribute it.
- An explicitly authorized **local Kompiler service** only for historical `doctor`, `run`, and `project` commands. No network access is needed for the v11 reader or preflight.

## Quick start: validate a Framework v11 project

Run these commands from the **Integration Pack repository root**. Replace `FW` with the absolute path to the exact Framework checkout.

```bash
FW=/absolute/path/to/Kristal-Framework-v11.0.0-draft.4
S="$FW/examples/v11"

python tools/v11_integration.py check \
  --framework "$FW" \
  --registry "$S/identity-registry.example.json" \
  --graph "$S/semantic-graph.example.json" \
  --crosswalk "$S/external-crosswalk.example.json" \
  --catalog "$S/dictionaries/catalog.json"
```

The command reads and validates the inputs; it never edits the original canonical graph or dictionary layers. The Framework checkout must match the reviewed SHA-256 pin or the command refuses to proceed.

### Check language coverage

```bash
python tools/v11_integration.py coverage \
  --framework "$FW" \
  --registry "$S/identity-registry.example.json" \
  --graph "$S/semantic-graph.example.json" \
  --crosswalk "$S/external-crosswalk.example.json" \
  --catalog "$S/dictionaries/catalog.json" \
  --locales fr-CA,en --out ./coverage-fr-CA-en.json
```

### Build a derived reading view

```bash
python tools/v11_integration.py view \
  --framework "$FW" \
  --registry "$S/identity-registry.example.json" \
  --graph "$S/semantic-graph.example.json" \
  --crosswalk "$S/external-crosswalk.example.json" \
  --catalog "$S/dictionaries/catalog.json" \
  --locale fr-CA --out ./view-fr-CA.json
```

For these commands, `--out` creates a **new file only**: an existing destination will not be overwritten. The resulting `read-view/v11.0-draft.1` is a **derived display artifact**, not a new semantic graph, identity assignment, or publication record.

## diK alpha.7 → Authoring Kit draft.4 (lot 1): guarded handoff

Use the Pack to perform an independent, read-only preflight before an approved catalog is considered for import into the Authoring Kit.

### Preflight an existing Framework example catalog

```bash
python tools/v11_handoff.py \
  --framework "$FW" \
  --catalog "$S/dictionaries/catalog.json" \
  --registry "$S/identity-registry.example.json" \
  --crosswalk "$S/external-crosswalk.example.json" \
  --graph "$S/semantic-graph.example.json" \
  --locales fr-CA,en
```

### Preflight a real diK alpha.7 import candidate

Replace the paths with the **matching outputs of one reviewed import job**. The `--kit-import-candidate` mode accepts only incoming Wikidata layers, not mixed-in curated layers.

```bash
python tools/v11_handoff.py \
  --framework "$FW" \
  --catalog /path/to/dik-import/catalog.json \
  --registry /path/to/project/identity-registry.json \
  --crosswalk /path/to/project/external-crosswalk.json \
  --kit-import-candidate \
  --dik-job /path/to/dik-import/dik-job.json \
  --out ./dik-kit-preflight.json
```

The optional diK receipt is checked against the catalog, source pins, registry, crosswalk, transformation profile, and idempotency key. A digest match protects consistency; **it does not prove the origin of Wikidata data, semantic equivalence, or human approval**.

Node users can call the same guarded workflow with `node tools/kristal-bridge.mjs v11-handoff ...`; see [`docs/DIK_KIT_HANDOFF_V11.md`](docs/DIK_KIT_HANDOFF_V11.md) for the exact allowlisted arguments.

**Approval and adoption are separate actions performed by the Authoring Kit**, using `import-dik-catalog`, `select-v11-catalog`, and, if needed, `recover-v11`. The Integration Pack never runs those commands automatically and never renumbers or merges KQ/KP identities.

## Historical Kompiler and Konstellation workflows

These commands are **separate from Framework v11**. A Kompiler Context Pack or v6 projection must not be mistaken for a canonical v11 semantic graph.

### Local Kompiler CLI

Start an authorized Kompiler instance on loopback, then use:

```bash
export KOMPILER_URL=http://127.0.0.1:7788
node tools/kristal-bridge.mjs doctor
node tools/kristal-bridge.mjs run \
  --query examples/kristall-surface.query.json \
  --out ./results/context-pack.json
node tools/kristal-bridge.mjs project \
  --pack ./results/context-pack.json \
  --out ./results/projection
```

Inspect the capabilities returned by `doctor`: the example does **not** guarantee that a suitable v7 Surface is available. Projection fails rather than fabricating missing assertions. The bridge restricts the local service URL and supported CLI options.

### Inspect an old Konstellation overlay before installing

The integration overlay was designed for a verified, **unmodified historical** Konstellation checkout. The supplied already-integrated Konstellation snapshot must **not** be overlaid again.

```bash
python tools/install.py /path/to/Konstellation --status
python tools/install.py /path/to/Konstellation
```

Only if the owner verifies the checkout is eligible, an explicit installation can be considered:

```bash
python tools/install.py /path/to/Konstellation --apply
```

Rollback is a separate, deliberate action:

```bash
python tools/install.py /path/to/Konstellation --rollback
```

Treat `DO_NOT_REINSTALL_EXISTING_INTEGRATION` as a **stop condition**, not permission to override safety checks. No overlay deployment, production Astro/Svelte build, or browser-level Konstellation qualification is claimed for this release. Multiuser access remains blocked until the host binds its reader authorization policies to the upstream requests.

### Local Kit write safeguards

Historical `build-v9` and `publish-v9` operations require **both** `KRISTAL_ALLOW_WRITE=1` and the action's explicit matching confirmation. Back up the target workspace first. Neither the v11 reader nor the handoff grants write permission or bypasses the Kit's governance.

## Repository layout

```text
contracts/v11-framework-pin.json                 Reviewed Framework v11 version and SHA-256 pins
tools/v11_integration.py                          Read-only check, coverage, and derived views
tools/v11_handoff.py                              diK-to-Authoring-Kit preflight
tools/kristal-bridge.mjs                          Node CLI: legacy bridge and v11 entry points
tools/install.py                                 Guarded historical overlay installer and rollback
tools/check_c3_readiness.py                      Delegated local collection readiness check
overlay/server/integrations/kompiler-bridge.mjs   Historical Konstellation API integration
overlay/server/integrations/kristal-v11-read-view.mjs  Defensive derived-view format guard
overlay/src/components/KompilerPanel.svelte      Historical Konstellation UI panel
examples/                                        Sample queries and JSON output formats
tests/                                           Python and Node regression tests
docs/                                            Security, alignment, handoff, and qualification evidence
MANIFEST.sha256.json                              Source-file integrity manifest
```

## Verification and tests

Run the local regression suites from the repository root:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
python tools/verify_manifest.py
python tools/release_package.py verify
```

For the pinned v11 tests, provide the exact local Framework checkout:

```bash
export KRISTAL_FRAMEWORK_ROOT=/absolute/path/to/Kristal-Framework-v11.0.0-draft.4
python -m unittest discover -s tests -p 'test_v11*.py' -v
node --test tests/v11.test.mjs
```

The **0.3.0-alpha.1 local qualification** recorded **29 passing Python tests and 15 passing Node tests**, including a temporary Authoring Kit draft.3 example-workspace handoff. This does **not** establish a production release. The diK alpha.7 receipt tests used a synthetic receipt structure; the exact binary output of a real diK import was not independently qualified here.

See [`docs/QUALIFICATION_030_ALPHA1.md`](docs/QUALIFICATION_030_ALPHA1.md), [`docs/QUALIFICATION_V11.md`](docs/QUALIFICATION_V11.md), and [`docs/RELEASE_VERIFICATION.md`](docs/RELEASE_VERIFICATION.md) for executed evidence and remaining gaps.

## Security and ownership rules

1. **Canonical identity is immutable to this Pack.** Kristal Framework defines the contract; KQ/KP/KA/KS references cannot be replaced by words or raw Wikidata Q/P identifiers.
2. **Wikidata is external evidence.** Only reviewed `accepted + exactMatch` correspondences may be used as exact identity references. `candidate`, `closeMatch`, label similarity, redirects, and missing pages do not confer equivalence.
3. **diK produces lexical snapshots and review proposals**, not automatic semantic revisions.
4. **The Authoring Kit owns authoring and explicit catalog adoption**; the Pack's preflight does not register or activate artifacts.
5. **Konstellation and Kompiler remain independent.** Konstellation is a navigator, Kompiler produces derived Context Packs/projections, and neither is made a new publishing authority by this bridge.
6. **No implicit host installation or publication.** Keep integrations local and scope-bound; do not enable shared HTTP access without the host's explicit reader policies.

## Documentation

- [Framework v11 read-only alignment](docs/ALIGNMENT_V11.md)
- [diK → Authoring Kit handoff](docs/DIK_KIT_HANDOFF_V11.md)
- [Framework/Kit qualification](docs/QUALIFICATION_030_ALPHA1.md)
- [Legacy Kompiler compatibility](docs/C5_KOMPILER_08.md)
- [Security boundaries](docs/SECURITE.md)
- [Execution plan](docs/PLAN_EXECUTION.md)
- [Release verification](docs/RELEASE_VERIFICATION.md)

## Current limitations

This alpha release has **not** been validated on a complete production Konstellation deployment, through Astro/Svelte browser flows, under live multiuser Reader Policies, or against a real large-scale Wikidata import from the diK executable. Full end-to-end restore/recovery, signatures and approvals, C1/C2 host authorization, and final cross-repository conformance remain open.

**Release principle:** validate and explain interoperability; never silently merge identities, overwrite canonical data, install an existing overlay, or imply approval from a successful preflight.

### Lot 1 alignment verification (2026-10-27)

See [`docs/LOT1_KIT_ALIGNMENT.md`](docs/LOT1_KIT_ALIGNMENT.md). This repository remains Integration Pack `0.3.0-alpha.1`; its normative pins and runtime semantics were not modified.
