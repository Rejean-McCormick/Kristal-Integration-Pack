# Execution and harmonization plan

| Phase | Current evidence | Next required gate |
|---|---|---|
| Source versions | Framework `draft.3.1` and Kit `3.2.4` inspected in supplied snapshots | Pin exact commits and calculate trusted contract-set SHA for each checkout |
| CLI C5 local | Protocol 1.0/1.1 mock tests; historical live Kompiler 0.8 / Zoology result retained | Re-run live test against current Kompiler with explicit trusted SHA |
| Konstellation HTTP and panel | Snapshot has integration with original patch-manifest hashes, but differs from this overlay | Owner diff and Node >=24.15 build/browser/scope/policy tests; **no reinstall** |
| Generic v9/v10 navigation | Not provided by this pack | Konstellation + Kompiler owner must qualify native semantic reader or clearly report losses |
| GitHub v10 C3 | Public snapshot missing `kristals/index.json` | Manager produces exact read-surface/manifest/index; run C3 in staging; grant separately |
| Local Kit actions | Inspect/check/read-surface delegated; writes require dual opt-in | Owner receipts and backups for any authorized domain changes |
| Shared/multiuser HTTP | Reader-policy binding not proven for Kompiler requests | **BLOCKED** until policy cannot be bypassed |
| Application deployment | Outside pack scope | Publisher deploys Konstellation software only, with explicit approval |

## Recommended sequence

1. Run `python tools/install.py PATH --status`, review report and owner source diffs; only use legacy overlay `--apply` on an **unmodified** compatible checkout with deliberate authorization.
2. Run the CLI, installer and C3 preflight tests; verify the pack SHA manifest.
3. On a protected fixture, confirm `doctor → run → project` against Kompiler. Compare coverage/provenance; do not claim a generic v9 concept conversion.
4. Verify Framework pin via `--contract-set-sha256` before local Zoology C5 live test. No remote GitHub write is performed by these commands.
5. Obtain real Konstellation/Kompiler owner checkouts and run Node 24.15+ build, API scopes, UI tests and Reader Policy denial tests before any multiuser activation.
6. Use owner-controlled Manager/Bootstrap/C3 to qualify a future hosted read-surface. Retain public sync and release blocks until independent C1, C2 and exact-revision gates pass.

## Rollback

The installer refuses rollback when recorded patched files have changed since installation; it does not overwrite new owner changes. Restore only from reviewed, matching backup records on a private copy. A public GitHub push cannot be made private retroactively by a revert.
