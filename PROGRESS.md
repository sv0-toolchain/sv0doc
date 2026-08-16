# sv0doc — progress

**Live status is tracked in one place:** the parent workspace's
[`task/sv0-toolchain-progress.md`](../task/sv0-toolchain-progress.md). When this
tree is the `sv0doc/` submodule of **sv0-toolchain**, that file is authoritative.

## current state

- **Milestone 0 complete** — the formal specification is in place: `grammar/`,
  `type-system/rules.md`, `contracts/semantics.md`, `memory-model/ownership.md`,
  `keywords/reference.md`, and the `bytecode/` anchors. The parent CI enforces
  these paths via `scripts/verify_sv0doc_baseline.py`.
- `compiler/bootstrap-*.md` carry the normative bootstrap deferrals (diagnostics,
  host I/O, generics policy, deferred surface) referenced by the sv0c self-host
  work. See [`README.md`](README.md) for the full contents map and hub role.

_Historical note: the detailed edit log lives in git history and the parent
progress rollup; it is not duplicated here to keep a single source of truth._
