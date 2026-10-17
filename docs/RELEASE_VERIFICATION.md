# Integration Pack 0.1.0-alpha.2 — local verification

**Candidate update, 2026-10-12.** This report records exact checks performed on an extracted copy of the supplied Integration Pack snapshot. It does not claim an approved release or remote GitHub deployment.

## Checked locally

- JavaScript CLI/overlay checks: `node --test tests/*.test.mjs` — **9/9 PASS** with Node 22.16.0. The target Konstellation release requires Node 24.15+, so this is **not** a full application release test.
- Python installer and C3 delegation safety checks: `python -m unittest discover -s tests -p 'test_*.py' -v` — **6/6 PASS** with Python 3.13.5.
- Candidate overlay Node syntax and Python syntax checks — **PASS**.
- Konstellation snapshot source comparison — existing bridge and panel recorded hashes match its own `.kristal-integration-backup/patched.sha256.json`, while **both candidate overlays differ**; `tools/install.py --status` reports `DO_NOT_REINSTALL_EXISTING_INTEGRATION` and no file changes were applied.
- Projection sample passes `jsonschema` against both supplied Framework v6 and Konstellation v6 upstream schemas — **PASS**. The sample is synthetic, not a real domain assertion.
- The real owner C3 `scan` on the supplied `kristal-public` snapshot returns **BLOCKED**, because `kristals/index.json` is missing. This is expected. The helper propagates this refusal; it does not construct an index or grant authorization.
- SHA-256 file manifest and ZIP CRC verified after packaging. Checksums identify local bytes, not logical Kristal commitments.

## Still blocked / not evaluated

- Konstellation production build, UI/browser tests and live HTTP policy-bound requests under Node 24.15+.
- Current Kompiler 0.8 runtime live test and confirmed Framework pin on the user's computer. The C5 local interoperability from October 8 is **historical evidence**, not a new test result.
- Manager sync surface / C1 independent qualification / C2 authorization / C3 real release / public GitHub round-trip.
- Multiuser enabling of Kompiler routes without enforceable Reader Policy binding.
- Reapplying the candidate overlay to the supplied installed Konstellation snapshot. **Not attempted; intentionally refused by compatibility guard**.
- Actions CI run on an actual GitHub commit. Workflow is provided, but its execution status has not been checked remotely.

## Compatibility, identity and safety

No Kristal canonical artifact, State Commitment, state identity, collection, GitHub repository, Konstellation runtime, or external service was modified. The pack is a source/tooling overlay, not a normative Kristal.

## Integration Pack 0.3.0-alpha.1 — nouvelle qualification locale (2026-10-17)

Le statut de cette version et les résultats actuels figurent dans [QUALIFICATION_030_ALPHA1.md](QUALIFICATION_030_ALPHA1.md). Le rapport historique 0.1 ci-dessus est conservé comme trace, sans réutiliser ses succès comme tests de la 0.3.

```bash
KRISTAL_FRAMEWORK_ROOT=/chemin/vers/Kristal-Framework-v11.0.0-draft.4 \
KRISTAL_AUTHORING_KIT_ROOT=/chemin/vers/Kristal-Authoring-Kit-4.0.0-draft.3 \
  python -m unittest discover -s tests -p 'test_*.py' -v
KRISTAL_FRAMEWORK_ROOT=/chemin/vers/Kristal-Framework-v11.0.0-draft.4 \
  node --test tests/*.test.mjs
python tools/verify_manifest.py
```

Le Pack ne contacte pas Wikidata ni les hôtes Konstellation lors de ces tests et n'effectue aucune installation. L'exécution de la CI distante, la qualification de Kompiler réseau et le navigateur final restent séparés.
