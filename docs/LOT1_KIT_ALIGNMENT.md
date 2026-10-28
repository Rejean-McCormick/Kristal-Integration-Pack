# Lot 1 — Authoring Kit draft.4 consumer alignment (2026-10-27)

**Status:** documented alignment; independent Kit draft.4 qualification is not included in this Integration Pack snapshot.

## Baselines

- Integration Pack source: **`0.3.0-alpha.1`** (unchanged).
- Required Kristal Framework checkout: **`11.0.0-draft.4`**, pinned by **13** file-level SHA-256 digests in `contracts/v11-framework-pin.json` (unchanged).
- Documented Authoring Kit lot-1 candidate: **`4.0.0-draft.4`**. The October 27 lot-1 record reports a **byte-for-byte identical** Framework draft.4 pin file to the Pack's file; Kit source was not provided here for independent verification.
- Historical cross-repository qualification on October 17 used **Authoring Kit `4.0.0-draft.3`** with a separate draft.3 pin, using an isolated temporary demo workspace. That test result must **not** be represented as a fresh draft.4 run.

## Read-only verification on actual local checkouts

After obtaining the correct, approved Kit source, compare its pin file to the Pack's pin **as bytes**, not just as valid JSON:

```bash
# From the Integration Pack repository root, with KIT pointing to the approved Kit checkout:
export KIT=/absolute/path/to/Kristal-Authoring-Kit-4.0.0-draft.4
python -c 'from pathlib import Path; import os; kit=Path(os.environ["KIT"]); p=Path("contracts/v11-framework-pin.json"); k=kit/p; assert k.is_file() and k.read_bytes() == p.read_bytes(), "Framework pin files differ"; print("Framework pins match byte-for-byte")'
```

The `export` command above is for Bash. On Windows PowerShell, set `$env:KIT = "C:\path\to\Kristal-Authoring-Kit-4.0.0-draft.4"` instead; then run the Python comparison from the Pack root. Alternatively compare SHA-256 digests of the two files in your shell. `python -m json.tool` checks syntax only and **cannot** prove file equality.

Then run the **Kit's own** documented `qualify-v11` workflow with approved Framework, Pack, and Kit checkouts, and record its actual output. The Pack itself only performs read-only validation (`check`, `coverage`, `view`, `v11-handoff`); it never registers or selects a catalog. The Framework source pin, executable code, and Pack version are unchanged by this documentation alignment.

## Evidence not yet established by this snapshot

- Independent comparison against an actual `4.0.0-draft.4` Kit checkout.
- Fresh Kit draft.4 end-to-end test and restore/recovery evidence.
- Real diK alpha.7 executable receipt, Windows/host deployment and publication authorization.

For the tested historical record, see [Qualification 0.3.0-alpha.1](QUALIFICATION_030_ALPHA1.md). For the read-only handoff, see [diK → Kit v11](DIK_KIT_HANDOFF_V11.md).
