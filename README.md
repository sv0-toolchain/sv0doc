# sv0doc -- sv0 language specification

formal specification repository and wiki for the sv0 programming language.

## purpose

sv0doc is the **source of truth** for the sv0 language. the compiler (`sv0c`) and bytecode interpreter (`sv0vm`) implement against the specifications defined here.

## contents

| directory | description |
|---|---|
| `grammar/` | formal grammar in EBNF notation |
| `type-system/` | type inference rules, trait resolution, generic constraints |
| `contracts/` | contract semantics (requires, ensures, loop_invariant, forall, exists) |
| `keywords/` | reserved keyword and operator reference |
| `memory-model/` | ownership, borrowing, borrow elision, borrows() contracts |

## relationship to other subprojects

- **sv0c** implements the grammar, type rules, and contract semantics defined here
- **sv0vm** implements the bytecode format and runtime semantics defined here
- changes to sv0doc require corresponding changes to sv0c and/or sv0vm

## milestone tracking

- [milestone-1-complete.md](milestone-1-complete.md) — what **sv0c** shipped for Milestone 1 versus deferred to M2 (aligned with [sv0c/doc/compiler-passes.md](../sv0c/doc/compiler-passes.md)).

## design document

the specifications here are extracted from the [sv0 compiler vision and design](http://development.sasankvishnubhatla.net/tcowmbh/task/sv0-compiler-vision-and-design.html) document. that document is the original design; sv0doc is the formalized, implementable reference.
