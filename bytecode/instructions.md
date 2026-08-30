# Bytecode instruction set (sv0)

This document is the **sv0doc** index for **individual opcodes**. Opcode numeric values, stack effects, and runtime behavior are defined by the **sv0vm** interpreter and the **sv0c** VM code generator; keep this file in sync when adding or renaming ops.

## Conventions

- Operands are encoded as in the SML `Bytecode` module under **sv0vm**.
- Contract and runtime intrinsics that exist only in the C backend may not have VM op analogues; call that out here when relevant.

## Width classes: i32 / i64 / f64

The `.sv0b` container has always defined `PUSH_I64` (op 5), `PUSH_F64` (op 6),
`ADD_I64`…`NEG_I64` (32–37) and `ADD_F64`…`NEG_F64` (48–52). As of the
`sv0c-vm-float-parity` work (`task/sv0c-vm-float-parity.Rmd`, 2026-08-29):

- **`sv0c` VM emitter** (native mega-TU, `build/sv0-megatu-vm-native`): picks
  the width-specific arithmetic opcode from the combined operand category
  (i32 / i64 / f64), tracked through the slot env (param / `DeclNamed` /
  spilled-temp / call-result). Float literals lower to `PUSH_F64` with the
  IEEE-754 bit pattern produced by a pure-integer decimal→double converter
  (the toolchain has no float type of its own). Wide integer literals lower
  to `PUSH_I64`.
- **`sv0vm` interpreter**: `cell` gained `CF64 of real` and `CI64 of Int64.int`.
  `ADD_F64`…`NEG_F64` run IEEE-754 arithmetic; `ADD_I64`…`NEG_I64` wrap mod
  2⁶⁴ (`Word64`) with truncate-toward-zero div/mod. The polymorphic
  comparisons (`EQ`/`NEQ`/`LT`/`GT`/`LTE`/`GTE`) dispatch on the operand cell
  kind, coercing a plain `CInt` literal in an f64/i64 context — matching the C
  backend's implicit promotion. Real comparisons use `Real.<`/`Real.==` (IEEE:
  NaN ⇒ false), never `Real.compare`.

The legacy **SML `--target=vm`** path (`sml-legacy/backend/vm/`) still raises on
`FloatLit` and only ever emits `ADD_I32`; it is frozen. Use the native VM
emitter for f64 / i64 (`./scripts/sv0 vm-native-compile`).

## See also

- `sv0doc/bytecode/format.md` — container layout.
- `task/sv0vm-milestone-2.Rmd` — VM milestone criteria and tests.
