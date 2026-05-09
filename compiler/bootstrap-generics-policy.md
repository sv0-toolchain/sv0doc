# bootstrap compiler — generics and user monomorphization (**T0-2d** / **M3-S-054**)

This note is **normative for milestone 3 bootstrap work** (`task/sv0-toolchain-milestone-3-self-host.Rmd`, slice **M3-S-054**). It **does not** replace the long-range language model in [`type-system/rules.md`](../type-system/rules.md) §5 (*generics* / §5.6 *monomorphization*); it records **what the shipped bootstrap compilers guarantee today** versus **what remains intentionally deferred**.

## scope

- **In scope:** policy for **user-written generics** (`fn foo<T>(…)`, `struct Bar<T>`, …) on the **SML bootstrap** path and the **sv0 transliteration** under `sv0c/lib/` … — checker expectations, lowering/IR expectations, and corpus obligations.
- **Out of scope:** full trait-bound dispatch, GATs, const-generic evaluation, and other items already called out as future milestones in [`milestone-0-review.md`](../milestone-0-review.md).

## language intent (informative)

Full-language intent remains: generics are ultimately realized via **monomorphization** — specialized copies per concrete instantiation — as summarized in [`type-system/rules.md`](../type-system/rules.md) §5.6.

## bootstrap decision — **T0-2d deferred**

**Slice:** **M3-S-054** closes by **formal deferral** (not by implementing a lowering-side generic expansion pass).

**Deferred work:** a dedicated **lowering / IR monomorphization** pass that **duplicates** generic item bodies per concrete type argument set at **definition granularity** (template-style expansion beyond what the current pipelines already do). Call this **“user generic monomorphization in lowering”** (**T0-2d**).

**What is already landed (not deferred):**

- **Parser / AST / resolver:** generic parameter lists on items and generic type applications in type positions (**T0-2a**–**b** class work — see milestone refinement log in `task/sv0-toolchain-milestone-3-self-host.Rmd`).
- **Checker:** type parameters as **TyVar**-like slots; **unification** at use sites so concrete calls and struct/enum uses carry **fully substituted** types before lowering (**T0-2c** class work).

**Bootstrap invariant:** for programs accepted by the checker, the **SML** and **sv0** compilers target the **same** lowering + codegen contracts as today: lowering consumes **already-constrained** types for each fragment it emits. Adding **new** transliteration features must preserve parity with the **SML** backend for the **same** surface, not assume a future **T0-2d** pass exists.

## corpus and compiler sources obligation

Bootstrap **compiler sources** (`sv0c/lib/*.sv0`, …) and **curated** integration / vm-parity corpora **must** restrict generic use to patterns **already supported end-to-end** by both backends. If a pattern requires **per-instantiation duplicated IR** that neither backend produces today, it is **out of scope** until **T0-2d** (or a narrower substitute slice) is promoted.

## promoting **T0-2d** later

Un-deferring **T0-2d** is a **new implementation slice**, not an implicit part of **M3-S-054**. When implemented:

1. Update [`type-system/rules.md`](../type-system/rules.md) §5.6 or this file to remove or narrow the deferral.
2. Refresh **`sv0c/doc/transliteration-plan.md`** and lowering inventory rows.
3. Run full **`./scripts/sv0 test`** + parity refresh as required by that slice.

## related

- [`bootstrap-deferred-surface.md`](bootstrap-deferred-surface.md) — **M3-S-055** (closures, `impl`, VM micro-optimizations).
- [`bootstrap-diagnostics.md`](bootstrap-diagnostics.md) — error carrier contract (**Track C**).
