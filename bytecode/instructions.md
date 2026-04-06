# Bytecode instruction set (sv0)

This document is the **sv0doc** index for **individual opcodes**. Opcode numeric values, stack effects, and runtime behavior are defined by the **sv0vm** interpreter and the **sv0c** VM code generator; keep this file in sync when adding or renaming ops.

## Conventions

- Operands are encoded as in the SML `Bytecode` module under **sv0vm**.
- Contract and runtime intrinsics that exist only in the C backend may not have VM op analogues; call that out here when relevant.

## See also

- `sv0doc/bytecode/format.md` — container layout.
- `task/sv0vm-milestone-2.Rmd` — VM milestone criteria and tests.
