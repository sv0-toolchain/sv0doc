# Milestone 1 complete (sv0c bootstrap compiler)

This document records what the **sv0c** bootstrap compiler shipped for **Milestone 1** versus what is explicitly **deferred to Milestone 2**, so the broad “in scope” language in older planning docs does not overstate the current implementation.

**Authoritative implementation detail:** [sv0c/doc/compiler-passes.md](../sv0c/doc/compiler-passes.md).

## Acceptance criteria (met)

- Compiler pipeline through **C99** codegen and **host `cc`** is exercised by **`make test`** and **`make e2e`** in **sv0c**.
- **Phases 1–6** and **Phase 9** of the internal milestone plan are done; **Phase 7–8** (traits/generics/methods and modules) are **not** required for calling M1 complete.
- Golden file tests live under **sv0c/test/data/golden/** (`fail/` and `pass/`).

## Shipped in Milestone 1

- **Lexer / parser / AST** for the supported surface (see compiler-passes).
- **Name resolution** with intrinsics (**`println`**, **`old`**, **`forall`**, **`exists`**, **`no_alias`**); enum variant paths (**`Enum::Variant`**); single-file / single-module assumptions for cross-module paths (qualified `module::item` remains future work).
- **Type checker** for the vertical slice: integrals, **`bool`**, **`unit`**, **`TyString`** (string literals), structs and enums, **`match`** on enum / **`bool`** / **`i32`**, **`as`** between **integral** types only, **`println("literal")`**, **`?`** on **user-defined** enums with **`Ok(T)`** / **`Err(E)`** single-field variants when the function returns that same enum, loops and **`break`** / **`continue`**, contracts (**`requires`**, **`ensures`**, **`loop_invariant`** on **`while`**) with runtime lowering.
- **Contract builtins (Phase 9):** **`result`**, **`old(x)`**, **`forall` / `exists`** over **`i32`** half-open ranges, **`no_alias`**, **`&` / `&mut`** in contract positions; diagnostics with **E05xx** codes and **`(hint: …)`** where applicable.
- **IR lowering** and **C codegen** including struct/enum carriers, **`sv0_runtime.h`** helpers (**`sv0_requires`**, **`sv0_println`**, **`sv0_no_alias`**, etc.).

## Reconciliation: original “in scope” wording vs reality

The milestone compiler plan listed a wide bootstrap subset. Below maps each theme to **M1 shipped**, **M1 partial**, or **M2** (not in the shippable M1 slice).

| Theme | Status | Notes |
|--------|--------|--------|
| Primitives (numeric, **`bool`**, **`unit`**, string literal type) | **M1 shipped** | No full heap **`string`** / **`String`** value API. |
| **`let` / `mut`**, functions, **`if` / else** | **M1 shipped** | |
| **`match`**, **`while`**, **`for`** over **`lo..hi`**, **`loop`**, **`break` / `continue`** | **M1 shipped** | |
| Structs, enums, field access, enum constructors | **M1 shipped** | |
| **`as` casts** | **M1 partial** | Integrals only (**E0440** for others). |
| **`?` operator** | **M1 partial** | User enums shaped **Ok/Err** only; not a generic **`Try`** trait. |
| **`println`** | **M1 shipped** | String **literal** argument only (**E0444**). |
| **`print`**, format strings | **M2** | |
| Contracts + runtime checks + Phase 9 builtins | **M1 shipped** | Analyzer pass is minimal; checking/lowering carry the weight. |
| **Operators / patterns** | **M1 partial** | Match what the checker and parser accept today; not “all” Rust-like forms. |
| **Generics** (type params, substitution, bounds) | **M2** | |
| **Traits / `impl` / method dispatch** | **M2** | |
| **`Option` / `Result` / `Vec` / `Box`** as compiler builtins | **M2** | Enum **`?`** pattern is ad hoc, not prelude types. |
| **Modules (`module` / `use`)**, qualified paths, core prelude | **M2** | Single translation unit / single-file style for M1. |

## Explicitly deferred (Milestone 2 and beyond)

- **Trait and generic** typing, **method calls**, **monomorphization or vtables** (internal **m1-p7**).
- **Cross-file modules**, **`use`**, **`module::`** value/type paths, implicit **core** prelude (internal **m1-p8**).
- **Heap `string`**, **`Vec` / `Box`**, generic **`Option`/`Result`**, **`print`**, full operator/pattern surface, **NLL**, **closures**, and items listed under **Deferred** in the compiler vision (GATs, **`impl Trait`**, **`unsafe`**, etc.) unless and until added to a later milestone plan.

## Related documents

- [milestone-0-review.md](milestone-0-review.md) — design questions and early scope.
- [sv0c/doc/compiler-passes.md](../sv0c/doc/compiler-passes.md) — pass-by-pass behavior and error codes.
