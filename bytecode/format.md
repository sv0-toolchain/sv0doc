# sv0 bytecode file format (`.sv0b`)

Binary artifacts produced by sv0c’s VM backend and consumed by sv0vm. This format implements the **bytecode VM backend** described in the [sv0 compiler vision and design](http://development.sasankvishnubhatla.net/tcowmbh/task/sv0-compiler-vision-and-design.html) document (compiler architecture — VM backend, toolchain `sv0 build --target=vm`). All multi-byte integers are **little-endian** unless noted.

The reference encoder and decoder live in the **sv0vm** submodule: `src/bytecode/bytecode.sml`.

## Header

| Field      | Size   | Description                                      |
|-----------|--------|--------------------------------------------------|
| `magic`   | 4      | ASCII `S` `V` `0` `B` (`0x53 0x56 0x30 0x42`)   |
| `version` | `u16`  | Format version; current value **1**              |

## Sections (version 1)

Sections follow the header in order. Each section starts with a `u32` **payload byte length** (excluding this length field), then payload bytes.

1. **String pool** — sequence of `u32` **count**, then `count` entries: each entry is `u32 byte_len` followed by UTF-8 bytes (no NUL terminator).
2. **Function table** — `u32` **count**, then `count` records:
   - `u32 name_index` — index into string pool (function name / symbol).
   - `u32 arity` — number of parameters.
   - `u32 local_count` — total local slots (params + locals), stack frame size contract for the interpreter.
   - `u32 code_offset` — byte offset into the **code blob** (see below), from 0.
   - `u32 code_length` — length in bytes of this function’s instruction stream.
3. **Code blob** — raw instruction bytes for all functions, concatenated. Offsets in the function table refer into this blob.

## Debug info (optional, version 1)

If present after the code blob, a trailer may be introduced in a future revision. For milestone 2, debug mappings (source span per instruction) are **optional** and not part of the version-1 required layout; tools should accept files that end after the code blob.

## Endianness and alignment

Instruction streams are byte-oriented; there is no padding requirement between functions inside the code blob. Decoders must use explicit little-endian loads for multi-byte immediates.

## Compatibility

Implementations must reject files with unknown `magic`, unsupported `version`, or inconsistent section lengths (e.g. function entry pointing outside the code blob).

See [instructions.md](instructions.md) for opcode and operand layouts inside the code blob.
