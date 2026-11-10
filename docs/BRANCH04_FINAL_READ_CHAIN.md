# Pack-derived v11 reader producer — Branch 04 final-system integration

**Scope:** `TARGET_DESIGN` plus named local tests; not a public release, current Git HEAD or production assertion.

The Pack is the **producer** of `kristal.integration.read-view/v11.0-draft.1`. Its `tools/v11_integration.py` delegates input and lexical validation to the exact pinned Framework 11.0.0-draft.4 checkout. It returns stable KQ/KP/KA/KS references, original assertions, source SHA-256s, `direct/fallback/missing` lexical statuses and accepted Wikidata exactMatch annotations. `derived_only: true` is mandatory.

**Consumer evidence (scope-specific):** Kompiler 0.8.0-alpha.1 already pins the Pack tool and Framework pin hashes, calls a local-only view on explicit consent, then creates a Context Pack. In this branch an independent EncyKlopedia private Node preflight also checks the actual Pack output against the same four source files. It reports `STRUCTURALLY_VERIFIED_NOT_PUBLIC` rather than creating a public article. The Pack itself is unmodified; its existing hashed release manifest remains valid.

**Do not add:** public release flags, auto-approval of lexical candidates, a new Framework registry owner, implicit conversion to a v6 Context Pack, or an EncyKlopedia public-serving route.

**Verification:** `KRISTAL_FRAMEWORK_ROOT=... python -m unittest tests.test_v11_integration -v`; Kompiler's `test_v11_cross_reader_preflight.py` with three explicit repository roots; EncyKlopedia's `npm run verify`. The actual Framework checkout was available only as a separate, supplied snapshot and was not modified by this branch.

