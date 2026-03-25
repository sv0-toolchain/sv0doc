# sv0 bytecode instructions

sv0vm is a **stack machine** aligned with the bytecode / `sv0vm` role in the [sv0 compiler vision and design](http://development.sasankvishnubhatla.net/tcowmbh/task/sv0-compiler-vision-and-design.html) document. Unless stated otherwise, operands are popped in **left-to-right** source order (second operand on top of stack after the first). Comparisons and arithmetic push a single result.

Opcodes are encoded as a single `u8`. Multi-byte immediates are **little-endian** (`u16`, `u32`, `i32`, `i64`, IEEE-754 `f64`).

## Control and stack

| Opcode (`u8`) | Mnemonic        | Operands (immediates) | Effect |
|----------------|-----------------|------------------------|--------|
| `0x00`         | `HALT`          | —                      | Stop execution (normal completion if stack empty or per ABI). |
| `0x01`         | `POP`           | —                      | Pop and discard one value. |
| `0x02`         | `DUP`           | —                      | Duplicate TOS. |
| `0x03`         | `PUSH_UNIT`     | —                      | Push unit `()`. |

## Literals

| Opcode | Mnemonic      | Operands | Effect |
|--------|---------------|----------|--------|
| `0x04` | `PUSH_I32`    | `i32`    | Push 32-bit integer. |
| `0x05` | `PUSH_I64`    | `i64`    | Push 64-bit integer. |
| `0x06` | `PUSH_F64`    | `f64`    | Push IEEE-754 double. |
| `0x07` | `PUSH_BOOL`   | `u8`     | `0` = false, non-zero = true. |
| `0x08` | `PUSH_STRING` | `u32`    | Push string constant from pool (index). |

## Integer arithmetic (`i32` / `i64`)

For each width, opcodes are grouped: add, sub, mul, div, mod, neg.

| `i32` range | `i64` range | Mnemonic pattern |
|-------------|-------------|------------------|
| `0x10`–`0x14` | `0x20`–`0x24` | `ADD`, `SUB`, `MUL`, `DIV`, `MOD` (binary; pop 2, push 1) |
| `0x15`      | `0x25`      | `NEG` (unary) |

Division and modulo follow language rules (division by zero is a runtime error).

## Floating point (`f64`)

| Opcode | Mnemonic   | Effect |
|--------|------------|--------|
| `0x30`–`0x33` | `ADD_F64` … `DIV_F64` | Binary. |
| `0x34` | `NEG_F64` | Unary. |

## Comparison and logic

| Opcode | Mnemonic | Effect |
|--------|----------|--------|
| `0x40` | `EQ`  | Pop two values; push bool (typed comparison per runtime tagging or static pairing). |
| `0x41` | `NEQ` | |
| `0x42` | `LT`  | |
| `0x43` | `GT`  | |
| `0x44` | `LTE` | |
| `0x45` | `GTE` | |
| `0x50` | `AND` | Boolean AND. |
| `0x51` | `OR`  | Boolean OR. |
| `0x52` | `NOT` | Boolean NOT. |

## Bitwise

| Opcode | Mnemonic   | Effect |
|--------|------------|--------|
| `0x58` | `BIT_AND`  | |
| `0x59` | `BIT_OR`   | |
| `0x5A` | `BIT_XOR`  | |
| `0x5B` | `BIT_NOT`  | Unary. |
| `0x5C` | `SHL`      | |
| `0x5D` | `SHR`      | |

## Locals

| Opcode | Mnemonic      | Operands | Effect |
|--------|---------------|----------|--------|
| `0x60` | `LOAD_LOCAL`  | `u32` slot | Push local slot. |
| `0x61` | `STORE_LOCAL` | `u32` slot | Pop into local slot. |

## Control flow

| Opcode | Mnemonic       | Operands | Effect |
|--------|----------------|----------|--------|
| `0x70` | `JUMP`         | `i32` offset | Add offset to IP (from **next** instruction). |
| `0x71` | `JUMP_IF`      | `i32` offset | Pop bool; jump if true. |
| `0x72` | `JUMP_IF_NOT`  | `i32` offset | Pop bool; jump if false. |
| `0x73` | `CALL`         | `u32` func_index, `u32` arg_count | Call function by index in function table. |
| `0x74` | `RETURN`       | —        | Legacy: single return value (same as `RETURN_SLOTS` with count 1). |
| `0x75` | `CALL_BUILTIN` | `u32` id | Invoke built-in by id (see runtime). |
| `0x76` | `RETURN_SLOTS` | `u8` n   | Pop **n** stack cells as return values (`n = 0` for `void`); restore caller. Emitted by sv0c VM backend for multi-slot / void returns. |

## Heap: structs and arrays

| Opcode | Mnemonic           | Operands | Effect |
|--------|--------------------|----------|--------|
| `0x80` | `ALLOC_STRUCT`     | `u32` type_index | Allocate struct; fields popped from stack. |
| `0x81` | `GET_FIELD`        | `u32` field_index | |
| `0x82` | `SET_FIELD`        | `u32` field_index | |
| `0x83` | `ALLOC_ARRAY`      | `u32` count | |
| `0x84` | `GET_INDEX`        | — | Bounds-checked read. |
| `0x85` | `SET_INDEX`        | — | Bounds-checked write. |

## Variants (tagged unions)

| Opcode | Mnemonic              | Operands | Effect |
|--------|-----------------------|----------|--------|
| `0x90` | `CONSTRUCT_VARIANT`   | `u32` type_index, `u32` variant_index, `u32` field_count | |
| `0x91` | `GET_TAG`             | — | Push variant tag. |
| `0x92` | `GET_VARIANT_FIELD`   | `u32` index | |

## Contracts and casting

| Opcode | Mnemonic         | Operands | Effect |
|--------|------------------|----------|--------|
| `0xA0` | `CONTRACT_CHECK` | `u32` message_index | Pop bool; if false, abort with pool message / debug info. |
| `0xA1` | `CAST`           | `u16` from_ty, `u16` to_ty | Coerce top of stack (encoding of types TBD per constant pool). |

Exact numeric opcode assignments in `bytecode.sml` must match this table; the reference implementation is the toolchain source.
