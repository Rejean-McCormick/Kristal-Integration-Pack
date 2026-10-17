# Kristal v10 interoperability alignment — integration ownership

**Track:** IP-01 through IP-04 in the 2026-10-12 multi-repository harmonization plan.  
**Baseline inspected:** Kristal Framework `10.0.0-draft.3.1` (draft), Authoring Kit `3.2.4`, historical Konstellation `1.0.0-rc.2`, and Kompiler local C5 `0.8.0-alpha.1` (previous evidence).  
**Status of this pack:** candidate integration helper; no remote synchronization, qualification, publication, or activation.

## What this repository owns

- A narrow CLI bridge for Kompiler capabilities, queries and optional **derived** v6 projection from a compatible v7 Surface.
- A version-constrained, **opt-in** legacy Konstellation overlay with a status inspector and rollback that refuses unknown modifications.
- Simulated/protocol tests, read-only local C3 diagnostic delegation, and qualification guidance.

It does **not** own Kristal state identity, v9 Logical or State Commitments, public/private collections, Konstellation's reader, Manager's registry, Kompiler's backend, C1/C2 approvals, C3 qualification, or GitHub deployment. It must not create a second Kristal explorer: Konstellation navigates both the fleet (when Manager provides safe inventory) and the content inside a selected Kristal.

## Contracts and exact-revision gates

| Produced/consumed interface | Producer → consumer | Status / boundary |
|---|---|---|
| `kompiler.capabilities/1.0` or `1.1` | Kompiler → CLI and Konstellation bridge | Strict protocol/version and target ID check in CLI; local mock tested |
| `kompiler.context-pack/1.0` or `1.1` | Kompiler → CLI | Strict protocol/version/basic payload check, provenance remains derived |
| v6 state projection | Kompiler `POST /v1/projections/v6` → Konstellation | **Only when compatible v7 Surface exists**, never a generic v9/v10 decoder |
| `kristal.state/9.0` and v10 host profile | Framework/Local Kit → external consumers | No mutation or commitment creation in this pack |
| GitHub collection index and sync manifest v10 | Manager/C3 → Konstellation/Kompiler | `tools/check_c3_readiness.py` **delegates** to C3; does not recreate verifier |
| C1 independent evidence / C2 visibility grant | Qualified independent owners → publication/sync controllers | **Not implemented** by the integration pack; no public sync allowed here |

**Pinned contract set:** Operators must select a trusted `contracts/contract-set.json` SHA-256 for the actual Framework checkout. The historical `fd8add31…` checksum in the C5 report records an earlier test only, not a universal production pin. `tests/live_c5_zoology.py` now fails closed without an explicitly supplied trusted pin matching the local Framework file.

## Concrete source review against the provided Konstellation snapshot

The 2026-10-12 `Code_snapshot_Konstellation(1).zip` already contains the integration in `server/index.mjs`, `server/config.mjs`, `Explorer.svelte`, and a Kompiler bridge/panel, and has a `.kristal-integration-backup/patched.sha256.json` with matching recorded hashes. The bridge and panel **differ** from the candidate files supplied in this pack.

`python tools/install.py KONSTELLATION_ROOT --status` reports:

- `existing_integration = true`
- `recorded_patch_matches = true`
- `pack_overlay_matches_installed = false`
- `recommendation = DO_NOT_REINSTALL_EXISTING_INTEGRATION`

**Do not run `--apply` on that already-integrated checkout.** Any upstream merge must happen in the **Konstellation-owned repository** after a human diff, exact SHA baseline, tests, and rollback plan. The old overlay still supports preview/apply/rollback on independently verified **unmodified** Konstellation `1.0.0-rc.2` source only.

## Road to qualification

1. Check out real current Konstellation and Kompiler at exact commits. Confirm Node **24.15+** for Konstellation and dependencies installed.
2. Examine owner bridge/panel changes and supported `kompiler.capabilities/1.1` and `kompiler.context-pack/1.1` schemas. Avoid overwriting an existing installed bridge.
3. Test owner Konstellation routes with `read` + `kompiler` scopes, Reader Policies, origin checks, response limits and async cancellation. The current proxy does **not** intrinsically bind a Konstellation reader's policy to every Kompiler request: **multiuser enablement remains blocked**.
4. Run the exact Framework pin and a **non-sensitive** local Kristal through Kompiler and inspect provenance, coverage, omitted artifacts, and the optional projection.
5. Validate a local GitHub collection with C3 **only after Manager has generated the correct index/manifests**. No C3 structural check implies independent C1, C2 grants, or a remote release.
6. Only after repository-owner tests, consider forwarding reviewed fixes as Konstellation/Kompiler pull requests; the integration pack never pushes.

## Files introduced or changed in this update

- `tools/kristal-bridge.mjs`: allowlisted options, clearer protocol errors, transactional local output directory, unchanged loopback/shell safeguards.
- `overlay/server/integrations/kompiler-bridge.mjs`: English diagnostics and loopback validation for explicitly provided URLs.
- `overlay/src/components/KompilerPanel.svelte`: English UI strings; **not installed** into the existing Konstellation checkout.
- `tools/install.py`: read-only `--status`, durable rejection of existing differing files, portable rollback tests.
- `tools/check_c3_readiness.py`: delegates `scan` / `validate-index` to the owner's local read-only C3 verifier.
- `tests/live_c5_zoology.py`: trusted Framework hash required before starting a local live API.
- tests, English documentation, updated integrity manifest and changelog.
