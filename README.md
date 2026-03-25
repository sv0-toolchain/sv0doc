# sv0doc -- sv0 language specification

formal specification repository and wiki for the sv0 programming language.

## purpose

sv0doc is the **source of truth** for the sv0 language. the compiler (`sv0c`) and bytecode interpreter (`sv0vm`) implement against the specifications defined here.

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

- **sv0c** implements the grammar, type rules, and contract semantics defined here
- **sv0vm** implements the bytecode format and runtime semantics defined here
- changes to sv0doc require corresponding changes to sv0c and/or sv0vm

## milestone status

- **Milestone 0 (task `sv0doc-milestone-0`): complete** — deliverables present: `grammar/sv0.ebnf`, `type-system/rules.md`, `contracts/semantics.md`, `memory-model/ownership.md`, `keywords/reference.md`. Review notes: [milestone-0-review.md](milestone-0-review.md).
- **Milestone 1 (task `sv0c-milestone-1`): complete** — see [milestone-1-complete.md](milestone-1-complete.md) and [sv0c/doc/compiler-passes.md](../sv0c/doc/compiler-passes.md).

## known deltas (shipped toolchain vs design doc)

- **IR shape:** The design document’s compiler architecture describes **sv0-IR in SSA form** for optimization and multi-backend lowering. **sv0c (Milestone 1)** currently lowers to an **imperative IR** with labeled blocks (`Ir.program` in sv0c); SSA remains a planned evolution, not a mismatch in intent for the bootstrap path.
- **Backends:** The vision names **C**, **bytecode VM**, and **LLVM** backends from sv0-IR. **Milestone 1** ships the **C** backend only; **Milestone 2 (in progress)** adds **bytecode** + **sv0vm** per `task/sv0vm-milestone-2.Rmd`.

## design document

The specifications here are extracted from the [sv0 compiler vision and design](http://development.sasankvishnubhatla.net/tcowmbh/task/sv0-compiler-vision-and-design.html) document. That document is the original design; sv0doc is the formalized, implementable reference.
