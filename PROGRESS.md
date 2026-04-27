# sv0doc — progress (submodule)

**Meta-repo rollup:** when this tree is the `sv0doc/` submodule of **sv0-toolchain**, the parent copies this file’s **`%`** into `task/sv0-toolchain-progress.md`. **Standalone clone:** keep this file authoritative here; reconcile on the next meta-repo integration.

**Last updated:** 2026-04-26 ( **`compiler/bootstrap-diagnostics.md`** — M3 **G0** compile-time failure + `CompileError` contract; T0-8 I/O names deferred to **M3-S-015** )

## Checklist (local source of truth)

| ID | Item | Done (0/1) |
|----|------|------------|
| DOC-1 | Formal spec layout lives under this repo and is linked from parent `task/` roadmap | 1 |
| DOC-2 | Grammar + normative semantics sections maintained as implementation evolves | 1 |
| DOC-3 | Bytecode / VM-facing spec sections aligned with `sv0vm` where applicable | 1 |
| DOC-4 | Cross-links from milestone tasks (`task/sv0doc-milestone-0.Rmd`, etc.) stay valid | 1 |

## Completion

- **Done:** count rows with `Done = 1` above.
- **Total:** row count of the checklist (increase only when adding rows; decrease with rationale in meta **run log**).
- **%:** `Done / Total * 100` (or leave blank if `Total = 0`).

## Notes

- 2026-04-10: Reconciled with `task/sv0doc-milestone-0.Rmd` (`state: complete`). All DOC items reflect M0 baseline closure: grammar (EBNF), type system, contracts, memory model, keywords, bytecode anchors under `bytecode/`. `verify_sv0doc_baseline.py` enforces required paths in `./scripts/sv0 test`.
- Normative spec evolves with implementation; DOC-2/DOC-4 are **continuing** obligations but satisfied at M0 closure.
