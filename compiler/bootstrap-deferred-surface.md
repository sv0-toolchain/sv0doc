# bootstrap compiler — deferred surface (**T0-7**, **T0-9**, VM loop sugar / **M3-S-055**)

This note is **normative for milestone 3 policy closure** (`task/sv0-toolchain-milestone-3-self-host.Rmd`, slice **M3-S-055**). It records **explicit deferrals** for language and backend sugar so **G9** cutover and **self-hosted** builds do not imply these features exist.

## **T0-7 — closures / higher-order functions**

**Status:** **deferred** for bootstrap milestone.

**Rationale:** capture semantics, environment layout, and borrow interactions are not required for the current transliteration strategy; SML list idioms are replaced with **explicit `Vec` loops** and **named functions**.

**Authoritative deferral table:** [`milestone-0-review.md`](../milestone-0-review.md) (“closures → milestone 2+”).

**Idioms:** see **`task/sv0-toolchain-milestone-3-self-host.Rmd`** § language surface gap (explicit loops over `Vec`, free functions).

## **T0-9 — `impl` blocks / method syntax**

**Status:** **deferred** for bootstrap milestone.

**Rationale:** transliteration and parity work use **structs + fields + free functions** (e.g. `vec_len(v)`) rather than inherent **`impl Type { fn … }`** dispatch sugar.

**Authoritative deferral table:** [`milestone-0-review.md`](../milestone-0-review.md) (methods vs struct + free function baseline for milestone 1 completeness narrative).

**Promotion:** adding **`impl`** is a **future slice** touching **`sv0doc/`** grammar + type rules + checker + lowering + backends.

## **`continue` inside `for` — VM / codegen optimizations**

**Status:** **correctness** for **`continue`** in **`while`** / **`loop`** / **`for`** is **in scope** wherever the grammar permits it and the backends emit sound control flow.

**Deferred:** **micro-optimizations** that rewrite **`for`** loops with **`continue`** into alternate bytecode patterns (e.g. duplicating loop headers, fusing increments) **purely for performance or size**. Such transforms remain **implementation-defined** until a slice promotes them with corpus + golden discipline.

**Normative bytecode semantics** remain under [`bytecode/`](../bytecode/) as extended elsewhere; this bullet only pins **policy**: no requirement to land fancy **`for`+`continue`** fusion for **M3** closure.

## promoting deferred items

Each of **T0-7**, **T0-9**, or a concrete **`for`/`continue`** optimization package becomes a **new `M3-S-###` slice** (or post-M3 milestone) with spec edits, tasks, tests, and parity expectations — **not** an implicit follow-on from **M3-S-055**.

## related

- [`bootstrap-generics-policy.md`](bootstrap-generics-policy.md) — **M3-S-054** / **T0-2d**.
- [`milestone-0-review.md`](../milestone-0-review.md) — milestone-scoped deferrals.
