# sv0doc -- sv0 language specification

formal specification repository and **documentation hub** entry for the sv0 programming language and toolchain.

## purpose

sv0doc is the **source of truth** for the **sv0 language** (grammar, types, contracts, memory model, keywords) and for **bytecode** consumed by `sv0vm`. the compiler (**sv0c**) and bytecode interpreter (**sv0vm**) implement against the specifications defined here.

**Hub role (parent repo [sv0-toolchain](https://github.com/sv0-toolchain)):** this repo is the primary place for **language** and **bytecode** normative docs. for **compiler internals**, see **sv0c** (`doc/`, README). for **VM internals**, see **sv0vm** README. for **MCP server setup, graph schema, and Cursor integration**, see **sv0-mcp** README (operational docs live there; this file links them for discoverability).

## canonical design document

All normative prose goals, philosophy, use cases, and high-level compiler architecture live in the **[sv0 compiler vision and design](http://development.sasankvishnubhatla.net/tcowmbh/task/sv0-compiler-vision-and-design.html)** document. **sv0doc** is the formal, implementable extraction (grammar, type rules, contracts, memory model, keywords). **Bytecode** layout and opcodes are specified under [`bytecode/`](bytecode/) for the VM backend described in that document.

## roadmap alignment (vision document ↔ task files)

The [vision implementation roadmap](http://development.sasankvishnubhatla.net/tcowmbh/task/sv0-compiler-vision-and-design.html#implementation-roadmap) names milestones 0–6. In the **sv0-toolchain** meta-repository (submodule parent), **`task/`** milestones map as follows:

| Vision milestone (design doc) | Task file / deliverable |
|-------------------------------|-------------------------|
| **0** — language specification (design narrative) | Source narrative in the design doc; **formal** spec extraction is **`task/sv0doc-milestone-0.Rmd`** → this repo’s `grammar/`, `type-system/`, `contracts/`, `memory-model/`, `keywords/` |
| **1** — bootstrap compiler (SML) | **`task/sv0c-milestone-1.Rmd`** → **sv0c** (C backend) |
| **2** — self-hosting preparation (test, fmt, doc, **bytecode VM**, …) | **`task/sv0vm-milestone-2.Rmd`** covers the **bytecode VM + VM backend** slice; other M2 items (full `sv0 test`, `sv0 fmt`, `sv0 doc`) are not required to be done before VM work proceeds |
| **3+** — self-hosting, verification, LLVM, kernel | Future **task/** milestones |

## contents

| directory | description |
|---|---|
| `grammar/` | formal grammar in EBNF notation |
| `type-system/` | type inference rules, trait resolution, generic constraints |
| `contracts/` | contract semantics (requires, ensures, loop_invariant, forall, exists) |
| `keywords/` | reserved keyword and operator reference |
| `memory-model/` | ownership, borrowing, borrow elision, borrows() contracts |
| `bytecode/` | `.sv0b` container and stack instruction set (VM / VM backend) |

## relationship to other subprojects

- **sv0c** implements the grammar, type rules, and contract semantics defined here (see also [sv0c/doc/compiler-passes.md](../sv0c/doc/compiler-passes.md)); small runnable **`.sv0`** walkthroughs live under [sv0c/examples/learn/](../sv0c/examples/learn/) (compile with **`./scripts/sv0 vm-compile`** from the parent **sv0-toolchain** root — paths are relative to **`sv0c/`**)
- **sv0vm** implements the bytecode format and runtime semantics defined under `bytecode/`
- **sv0-mcp** indexes spec entities, compiler phases, VM components, and `task/` workflow in a Neo4j graph for AI-assisted development; it does not replace this spec — see [sv0-mcp/README.md](../sv0-mcp/README.md)
- changes to normative sv0doc content typically require corresponding updates in **sv0c** and/or **sv0vm**; graph sync in **sv0-mcp** is updated separately via its sync pipeline

**Workspace index:** [task/sv0-toolchain-workspace.Rmd](../task/sv0-toolchain-workspace.Rmd) in the parent **sv0-toolchain** repo lists all four submodules and aggregate commands.

## milestone status

- **Milestone 0 (task `sv0doc-milestone-0`): complete** — deliverables present: `grammar/sv0.ebnf`, `type-system/rules.md`, `contracts/semantics.md`, `memory-model/ownership.md`, `keywords/reference.md`, plus **bytecode anchors** `bytecode/format.md` and `bytecode/instructions.md` (shared with **sv0c** VM backend and **sv0vm**). The parent **sv0-toolchain** repo runs **`scripts/verify_sv0doc_baseline.py`** inside **`./scripts/sv0 test`** so these paths (and the other required **sv0doc** files) must exist and be non-empty in CI. Review notes: [milestone-0-review.md](milestone-0-review.md).
- **Milestone 1 (task `sv0c-milestone-1`): complete** — see [milestone-1-complete.md](milestone-1-complete.md) and [sv0c/doc/compiler-passes.md](../sv0c/doc/compiler-passes.md).

## known deltas (shipped toolchain vs design doc)

- **IR shape:** The design document’s compiler architecture describes **sv0-IR in SSA form** for optimization and multi-backend lowering. **sv0c (Milestone 1)** currently lowers to an **imperative IR** with labeled blocks (`Ir.program` in sv0c); SSA remains a planned evolution, not a mismatch in intent for the bootstrap path.
- **Backends:** The vision names **C**, **bytecode VM**, and **LLVM** backends from sv0-IR. **Milestone 1** ships the **C** backend; **Milestone 2 (complete)** adds **bytecode** + **sv0vm** per `task/sv0vm-milestone-2.Rmd`.

## design document

The specifications here are extracted from the [sv0 compiler vision and design](http://development.sasankvishnubhatla.net/tcowmbh/task/sv0-compiler-vision-and-design.html) document. That document is the original design; sv0doc is the formalized, implementable reference.
