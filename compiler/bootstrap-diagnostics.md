# bootstrap compiler — compile-time diagnostics (sv0-in-sv0)

This note is **normative for the self-hosting compiler work** tracked under **`task/sv0-toolchain-milestone-3-self-host.Rmd`**. It does **not** redefine end-user language semantics in `grammar/` or `type-system/`; it pins the **interface contract** between the **SML bootstrap** story and the **sv0 transliteration** so Track C (`raise` → `Result`) can proceed without inventing behavior in code alone.

## scope

- **In scope:** how compile-time failures are **represented**, **propagated**, and **surfaced** in the **sv0** compiler sources under **`sv0c/lib/`** (and related **`lexer/`** / **`parser/`**), and how that relates to existing **span** and **diagnostic** seeds.
- **Out of scope (deferred):** exact **stdlib** names and signatures for **`read_file` / `write_file` / `read_dir`** and related runtime hooks — those are specified under slice **M3-S-015** (T0-8) once **`sv0doc/`** and bytecode/runtime notes are updated together.

## failure representation (no exceptions in sv0)

The sv0 language does **not** provide `try` / `catch` for compiler control flow. Transliterated compiler modules **must** use **`Result<T, E>`** / **`Option<T>`** / **`?`** for recoverable paths and for the primary **non-local exit** story.

**Unified carrier:** implementations introduce a single **`CompileError`** value type (name stable for tasks and transliteration plans). Until the **sv0-emitted C** backend fully supports arbitrary **enum tuple payloads**, the bootstrap seed may use a **`struct CompileError { message: string; span: Span; }`** carrying the same information; a single-variant **`enum`** is an equivalent surface once codegen is ready.

The type must subsume both:

- legacy **`raise Fail "E0ddd: …"`**-style messages, and
- structured **`Diagnostic.Diag`**-style payloads from the SML compiler,

converging on **one** error value type for pipeline composition (**`M3-S-041`**).

**Minimum payload:** every **`CompileError`** value carries at least:

1. a **human-readable message** (`string`), and  
2. a **source span** (`Span` — file path plus start/stop line/column/offset), matching the flattened **`Span`** model already used in **`lib/span.sv0`**.

Implementations may add variants later (codes, related spans, help text) without breaking this minimum.

## mapping from SML bootstrap (informative)

The milestone task file **`task/sv0-toolchain-milestone-3-self-host.Rmd`** § **exception and error translation strategy** tables the dominant SML patterns (`raise Fail`, speculative `handle Fail`, diagnostic bridging, top-level handlers). That table is **authoritative for sequencing**; this document states the **target shape** only:

| SML pattern (informative) | sv0 target |
|---------------------------|------------|
| `raise Fail msg` | `Err(CompileError::…)` with message + best-known span |
| `handle Fail _ => NONE` | return **`Option`** / `Ok` / `None` at API boundary |
| `handle Fail msg => Diagnostic…` | construct **`CompileError`** (possibly a dedicated variant later) |

## relationship to user-facing diagnostics

Today’s bootstrap **`lib/diagnostic.sv0`** seed models **severity**, formatting helpers, and future **`report` / `reportAll`** I/O. **`CompileError`** is the **semantic** failure value carried through **`Result`**; formatting for stderr / IDE integration may **consume** **`CompileError`** and existing diagnostic formatters together — exact merge is implementation detail in **`sv0c/`** as long as the **message + span** contract holds.

## revision discipline

Any change here that alters the **minimum payload** or the **deferred I/O boundary** should:

1. update **`task/sv0-toolchain-milestone-3-self-host.Rmd`** refinement log (slice **M3-S-001** / **M3-S-015** as appropriate), and  
2. run **`./scripts/sv0 test-guards`** (and **`./scripts/sv0 test`** when **`sv0c/lib/`** goldens move).
