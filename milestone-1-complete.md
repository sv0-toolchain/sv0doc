# Milestone 1 (sv0c bootstrap compiler) — aligned with `task/sv0c-milestone-1.Rmd`

**Status: complete** (task `sv0c-milestone-1` in `task/sv0c-milestone-1.Rmd` is `state: complete`).

This document tracks **Milestone 1** against the **original task bullets** in [`task/sv0c-milestone-1.Rmd`](../task/sv0c-milestone-1.Rmd). Implementation detail: [`sv0c/doc/compiler-passes.md`](../sv0c/doc/compiler-passes.md).

## Rmd acceptance criteria

| Criterion | Status |
|-----------|--------|
| Compile simple programs (bindings, functions, control flow, pattern matching, basic types, contracts) to C | **Met** — see `make test`, `make e2e`, `make integration` |
| Runtime contract checks as C assertions | **Met** — `sv0_requires` / `sv0_ensures` / runtime helpers |
| Module system resolves imports within a project | **Met (scoped)** — `sv0c --project <dir>` loads all `*.sv0`; `module m;` + `use a::item;`; symbols mangled as `mod__name`; C entry remains `fn main` |
| Error reporting with source spans and highlighted snippets | **Partial** — `Diagnostic.Diag` + `Diagnostic.format` for resolver `E0300` / `E0301`; other passes still mostly `Fail` strings; multi-file compile uses `format NONE` (location line, no snippet) |
| Test suite covers each compiler pass | **Met (as in Rmd)** — lexer/parser/resolver/checker/e2e/golden/pipeline in `test/test_runner.sml`; contract analyzer remains minimal |
| Phase 5 integration (Rmd §5) | **Met** — `task/sv0c-milestone-1/02-integration-test.sh` + `sv0c/test/integration/*`; **generics** path uses monomorphic placeholder until `<T>` typing exists; **methods** covered as struct + free function (no `impl` dispatch) |

## Commands

- `make test` — full in-process suite (including golden).
- `make e2e` — compile generated C, run binary (exit 42).
- `make integration` — heap image + Rmd integration scenarios.

## Intentional limitations (post–Milestone 1)

- Parametric generics (`<T>`), trait/impl method dispatch, NLL, closures, heap `String`, etc. remain future milestones unless added to a new task file.
- Single-file compile (`sv0c file.sv0`) does **not** merge sibling `.sv0` files (so golden dirs with many fixtures stay safe). Use `--project <dir>` for multi-file work.

## Related

- [`milestone-0-review.md`](milestone-0-review.md)
- [`sv0c/doc/compiler-passes.md`](../sv0c/doc/compiler-passes.md)
