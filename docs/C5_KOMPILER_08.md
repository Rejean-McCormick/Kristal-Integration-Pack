# C5 — Kompiler 0.8 local interoperability record

**Status:** historical local compatibility evidence; **GitHub v10 public read path NOT qualified**.

This supplements the separate historical Konstellation/Kompiler 0.7 / Framework `draft.3` record. The tests originally reported on 2026-10-08 ran Kompiler `0.8.0-alpha.1` with Kristal Framework `10.0.0-draft.3.1`, and used local Zoology v9 as a read-only source.

| Aspect | Previous record | C5 record |
|---|---|---|
| Kompiler | `0.7.0-alpha.3` | `0.8.0-alpha.1` |
| API | `/v1/` query and projection | `kompiler.capabilities/1.1` and `kompiler.context-pack/1.1` validated by CLI |
| Framework | `10.0.0-draft.3` | `10.0.0-draft.3.1` |
| Contract-set SHA observed then | historical `draft.3` digest | `fd8add31bb0a20159fd2e6c6c3175863a8195c9840e0b9f6a8cc388e57176c92` **historical evidence only** |
| Source | v7 demonstration | **local** Zoology v9 Context Pack and source reference |
| Hosted GitHub collection | not covered | Kompiler adapter described; **not verified on a qualified public release** |
| Konstellation UI | original overlay | installed in Konstellation snapshot but overlay differs, full build/browser E2E not proven |

## Reproducing on a local machine

1. Obtain exact current Kompiler, Framework and an authorized non-sensitive local Zoology workspace.
2. Approve the real Framework baseline SHA independently. Compute SHA-256 for **that** `contracts/contract-set.json` and pass it as `--contract-set-sha256`.
3. Run (local-only):

```powershell
node --test .	estsridge.test.mjs
python .	oolserify_manifest.py
python .	ests\live_c5_zoology.py --kompiler 'C:\mycode\Kristal\Kompiler' --framework 'C:\mycode\Kristal\Kristal-Framework' --zoology 'C:\mycode\Kristal\locals\Kristal-Zoology' --contract-set-sha256 '<TRUSTED_64_HEX_SHA256>'
```

The live test starts a loopback Kompiler API, invokes CLI `doctor/run`, writes local temporary files, and stops the server. It **does not** publish or activate any Kristal.

## C3 / remote GitHub exclusion

`examples/zoology-github-collection.query.json` is a **proposed** request that assumes the Kompiler adapter can discover a qualified GitHub collection. The supplied `kristal-public` snapshot lacks `kristals/index.json`, so this request cannot establish a real qualified hosted read path. To check offline without implementing a duplicate C3 verifier:

```powershell
python .	ools\check_c3_readiness.py --collection 'C:\mycode\Kristal\kristal-public' --mode scan
```

Even a later C3 structural PASS must not be confused with independent C1 evidence, a C2 public authorization grant, a remote release or production readiness.
