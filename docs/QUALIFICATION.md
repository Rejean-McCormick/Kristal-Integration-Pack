# Qualification record — evidence, gaps and scope

## Inherited results from 2026-10-08 (not rerun as part of the current update)

- Kompiler `0.7.0-alpha.3` was reportedly loaded with Framework `10.0.0-draft.3` and a then-pinned contract-set checksum.
- A real local demo `Kristall:kristall-main` produced a Kompiler Context Pack and a v6 derived projection, validated against the Konstellation and Framework v6 schemas.
- Historical `tests/bridge.test.mjs`: 4/4; overlay installer preview/apply/reapply/rollback on original files; Python compile/Node syntax checks passed.
- Two upstream Kompiler integration-test mismatches expected Framework `draft.2` despite the supplied `draft.3` baseline; upstream tests were **not** modified to conceal this divergence.
- No complete Astro/Svelte browser build, real Konstellation HTTP-to-Kompiler authorization round-trip, or multiuser/privacy qualification was established.

## C5 2026-10-08 supplement

Kompiler `0.8.0-alpha.1`/Framework `10.0.0-draft.3.1` local Zoology test with `capabilities/1.1` and `context-pack/1.1`. See `C5_KOMPILER_08.md` for that historical evidence and its checksum. No remote v10 collection qualification resulted.

## Changes in this Integration Pack candidate

- CLI rejects unknown options and invalid capabilities target IDs; local projection output uses staging and refuses existing directories.
- English diagnostics and UI strings; loopback validation also covers injected bridge URLs.
- `tools/install.py --status` inspects actual installed source without writing. Current supplied Konstellation snapshot reports `DO_NOT_REINSTALL_EXISTING_INTEGRATION` because installed files differ from the candidate overlay.
- Portable synthetic installer tests exercise preview, idempotency, backup, rollback, modifications and version refusal.
- Read-only `tools/check_c3_readiness.py` delegates to the existing C3 script and never builds an index itself.
- Live C5 script refuses an absent or mismatched trusted Framework SHA.

## Not proven by this update

**NOT QUALIFIED:** a full Konstellation build on Node 24.15+, browser tests, actual upstream Konstellation route install of the updated overlay, real Kompiler 0.8 API replay on the user's PC, independent C1 validation and C2 authorization, remote C3 GitHub release, semantic generic v9/v10 concept decoding, or Reader Policy binding for shared environments.

Use `docs/ALIGNMENT_V10.md` and `docs/PLAN_EXECUTION.md` for the owner reviews and acceptance gates. Passing local pack tests does not elevate this candidate to a v10 normative component.
