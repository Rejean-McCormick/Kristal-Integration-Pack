# Security and authorization boundaries

The bridge permits only local loopback HTTP (`127.0.0.1`, `localhost`, or `[::1]`) with no URL credentials/path or redirects. The CLI caps response bodies at 8 MB and the Konstellation overlay caps them at 2 MB by default; both enforce request timeouts and an explicit endpoint allowlist.

Konstellation's route adapter requires **both** `read` and `kompiler` scopes where installed, along with its existing origin/auth/rate-limit checks. The local-scoped feature is opt-in (`KONSTELLATION_ENABLE_KOMPILER_LOCAL=true`). A remote/shared deployment must **not** enable it until the principal's Reader Policy and allowable upstream targets are bound **unavoidably** to every Kompiler request. The bridge does not currently prove this mapping.

- Never forward a Konstellation principal's wide service token into Kompiler as an implicit right to all sources.
- Protect Context Packs, JSON projections, receipts and source metadata. They may contain confidential content even if the state is described as a “derived view.”
- `/v1/projections/v6` creates a derived representation only when a compatible v7 Surface is available, and cannot certify or publish a Kristal state.
- CLI authoring is limited to named Kit actions; `build-v9`/`publish-v9` require `KRISTAL_ALLOW_WRITE=1` plus exactly matching `--confirm`. This does not substitute for owner authorization or a transaction rollback service.
- C3 `scan` / `validate-index` checks local **structure**, not independent qualification, consent, release, publication, or activation.
- No scripts in this pack write to `kristal-public`, `kristal-private`, Manager, Bootstrap, or GitHub. `GitSink.bat` is a legacy utility that is **not** invoked by the integration workflow.
- Backups are checksummed and rollback refuses upstream drift; existing Konstellation integrations differing from the packaged overlay are **not overwritten**.

### Negative tests to retain

Unsupported protocol/version, fake target ID, nonloopback origin, redirect, unauthorized endpoint, oversized response, unknown CLI option, existing output directory, modified owner bridge, wrong contract-set SHA, missing public C3 index, unauthorized reader scope.
