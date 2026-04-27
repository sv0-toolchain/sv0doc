# bootstrap compiler — host filesystem I/O (T0-8 / M3 G2)

This note is **normative for the self-hosting compiler work** tracked under **`task/sv0-toolchain-milestone-3-self-host.Rmd`** (slices **M3-S-015 … M3-S-021**). It pins the **stdlib-style surface** the transliterated **`sv0c/lib/*.sv0`** driver, linker, include expander, and diagnostics may call for **host** filesystem access. It does **not** redefine end-user language semantics in **`grammar/`**; it documents **compiler-only** builtins wired through the same **`modEnvFromProg`** / lowering path as **`println`** and the string/vec intrinsics.

## scope

- **In scope:** three **free functions** exposed to bootstrap **`lib/`** sources with the exact spellings below; **C runtime** symbols backing the C backend; **VM `CALL_BUILTIN`** ids (see **`sv0vm`** interpreter + **`sv0c/lib/vm_codegen.sv0`**); error behavior on host failure.
- **Out of scope:** full **`Result<CompileError>`** threading for I/O failures (**`compiler/bootstrap-diagnostics.md`**); arbitrary binary blobs beyond UTF-8–oriented text (use **`write_file`** for opaque bytes only where the C runtime documents binary-safe behavior); Windows-specific path APIs (toolchain targets POSIX-like hosts today).

## builtins (normative names and types)

All three are **ordinary** identifier calls (same lexical rules as user functions). They are **not** keywords.

| Name | Type (surface) | Semantics |
|------|------------------|-----------|
| **`read_file`** | `(path: string) -> string` | Read the entire file at **`path`** using host OS semantics. **`path`** is a host path string (absolute or relative to the process working directory). Returns the file contents as a **`string`**. On failure (missing file, permission, etc.), the **C backend** calls **`sv0_panic`** with a short message; the **VM backend** raises **`Fail`** with a short message. *(A later slice may widen this to **`Result<string, string>`** once **`M3-S-041`** unifies pipeline errors.)* |
| **`write_file`** | `(path: string, contents: string) -> ()` | Create or truncate **`path`** and write **`contents`** (byte-oriented write of the **`string`** payload). Returns **`()`**. On failure, same panic / **`Fail`** policy as **`read_file`**. |
| **`read_dir`** | `(dir: string) -> string` | Enumerate **non-hidden** entries under **`dir`** recursively (skip names whose first character is **`.`**, matching the SML **`Link.walkSv0`** intent). Collect every regular file whose name ends with **`.sv0`**, using **`/`** as the separator when joining directory + name. Sort the resulting **full paths** lexicographically (byte **`strcmp`** / **`String.compare`** order) and return **one** **`string`** containing all paths separated by a **single `\n` (U+000A)** with **no** trailing newline after the last path. An empty directory yields **`""`**. On failure opening **`dir`**, panic / **`Fail`**. |

### relationship to SML bootstrap

The SML compiler uses **`TextIO`** / **`OS.FileSys`** directly. The transliterated **`sv0`** sources call **`read_file`**, **`write_file`**, and **`read_dir`** instead; lowering maps them to **`sv0_read_file`**, **`sv0_write_file`**, and **`sv0_read_dir`** in IR, then to C runtime helpers or VM **`CALL_BUILTIN`** opcodes.

### revision discipline

Any change that alters names, arities, **`read_dir`** encoding, or panic vs **`Result`** policy should:

1. update this file and **`task/sv0-toolchain-milestone-3-self-host.Rmd`** refinement log (slices **M3-S-015** / **M3-S-021** as appropriate), and  
2. run **`./scripts/sv0 test-guards`**; run **`./scripts/sv0 test`** when **`sv0c/lib/`**, **`sv0vm/`**, or vm-parity goldens move.

## related

- **`compiler/bootstrap-diagnostics.md`** — compile-time error carrier; defers I/O names until this document.  
- **`bytecode/`** — opcode **`117`** (`CALL_BUILTIN`) carries a **`u32`** builtin id; ids **15–17** are reserved for **`read_file` / `write_file` / `read_dir`** in the **`sv0vm`** interpreter shipped with this toolchain (see interpreter sources for the authoritative dispatch table).
