# Lot 1 — Authoring Kit draft.4 consumer alignment (2026-10-27)

- Framework target: `11.0.0-draft.4` (unchanged).
- Kit candidate: `4.0.0-draft.4`, with an **identical byte-for-byte** `contracts/v11-framework-pin.json`.
- Integration Pack version: `0.3.0-alpha.1` (unchanged). Existing 13 SHA-256 digests and read-only controls are preserved.

The matching pins can be verified with `python -m json.tool contracts/v11-framework-pin.json` and the independent Kit `qualify-v11` command with the real Framework and Pack checkouts. A real diK binary receipt, Windows deployment, and publication authorization remain out of scope.
