# Bytecode coverage revision (v1): `COVER_HIT` and `sv0vm-v1-coverage`

Status: **normative, partly implemented.** This is the authoritative
bytecode-contract change that sv0cov SPEC §15.1–15.3 and §16.8 require before
the toolchain emits or executes coverage instrumentation. sv0c emits
`COVER_HIT` as of `CV-117` (`sv0 vm-native-compile --coverage=instrument`;
`bytecode.sv0` encodes, sizes and disassembles it) and writes the §4
companion, `<stem>.sv0covbind.json`, as of `CV-118`. sv0vm decodes,
disassembles and executes `COVER_HIT` and rejects an unbound or
out-of-range one at load as of `CV-119`, and loads the companion
(`sv0 vm-run --coverage-binding <path>`, `SV0B_COVERAGE_BINDING` for
`sv0vm/scripts/run_sv0b.sml`) as of `CV-120`; the raw profile is `CV-121`,
and the pre-coverage decoder pin `CV-122` (`task/sv0cov-checklist.Rmd`). The typed-v2 inline form (`COVR` section,
profile `sv0vm-v2-typed` with the coverage capability) is staged to sv0cov R1
(SPEC §15.4, §15.6) and is specified in a later revision of this page.

## 1. The instruction

| Field | Value |
|---|---|
| Name | `COVER_HIT` |
| Opcode | 119 (`0x77`) |
| Operand | `local_counter_index`: `u32`, little-endian |
| Encoded length | 5 bytes, always |
| Stack effect | none (pops 0, pushes 0) |
| Source form | none: no sv0 syntax, builtin, or intrinsic produces it |

```text
offset  size  field
0       1     opcode = 0x77
1       4     local_counter_index (u32le)
```

Semantics: increment the coverage counter `local_counter_index` of the
running program by one, saturating at 2⁶⁴−1 and recording saturation (sv0cov
SPEC §14.2). Nothing else is observable: it calls no user-visible builtin,
allocates no user memory, touches no local or operand-stack cell, cannot fault
at run time (the index was validated at load, §3), and falls through to the
next instruction.

Opcode 119 is reserved exclusively for `COVER_HIT` in every profile and every
container version. No other instruction may ever use it.

### 1.1 Sizing and jumps

Every encoder size table, byte-offset computation, decoder boundary, verifier,
and disassembler treats `COVER_HIT` as exactly five bytes. Jump displacements
(`JUMP` 112, `JUMP_IF` 113, `JUMP_IF_NOT` 114) stay byte-relative to the end
of the jump instruction, so every hit placed between a jump and its target
widens the displacement by five bytes in that direction. Producers compute
offsets after hit placement; tests pin forward and backward jumps across hit
boundaries (`CV-117`).

### 1.2 Disassembly

```text
COVER_HIT <index>
```

`<index>` is the operand in decimal with no sign or leading zeros, e.g.
`COVER_HIT 0`, `COVER_HIT 4194303`. Disassemblers print it like any other
instruction; they do not resolve the index to a source location (that needs
the coverage map, which is not part of the bytecode).

## 2. Profiles

| Profile | Container | Coverage metadata | `COVER_HIT` |
|---|---|---|---|
| `sv0vm-v1-core` | `.sv0b` format v1 | none | unknown opcode: rejected at load |
| `sv0vm-v1-coverage` | `.sv0b` format v1, byte-for-byte unchanged | explicit companion `<program>.sv0covbind.json` (§4) | executed |
| `sv0vm-v2-typed` + `sv0cov.coverage.v1` | `.sv0b` format v2 | inline `COVR` section | staged to sv0cov R1 |

`sv0vm-v1-coverage` changes nothing in the v1 container: same magic `SV0B`,
format version `1`, string, function, and code sections, and no trailing
bytes. Coverage metadata is never appended to a v1 file. A program is
instrumented exactly when its code contains at least one `COVER_HIT`, and it
then runs only with a valid companion.

Uninstrumented v1 bytecode is identical to what a toolchain without this
revision produces, and a coverage-capable VM runs it unchanged (with or
without a companion; see §4.3).

## 3. Loading and validation

A coverage-capable VM performs these steps, in order, before executing any
user instruction or host effect:

1. Decode the container and every function exactly as for `sv0vm-v1-core`,
   recognising opcode 119 as `COVER_HIT` with its `u32le` operand.
2. If any function contains `COVER_HIT` and no companion was supplied
   explicitly, reject the program.
3. If a companion was supplied, validate it (§4.2), including its binding to
   these exact bytecode bytes.
4. Require every `COVER_HIT` operand to be `< program_counter_count`.
5. Require consistency: `program_counter_count > 0` if and only if at least one
   `COVER_HIT` is present.
6. Allocate `program_counter_count` zeroed counters and the saturation record.

The reference sv0vm checks a supplied companion against the raw file bytes
(step 3's length and SHA-256) before decoding them, so changed bytecode is
reported as `COV2202` rather than as whatever decoding the changed bytes
would raise. The outcome for valid input is the same in either order.

Steps 4 and 5 are all the VM can check about the count. A companion edited
to a larger `program_counter_count` still passes them (every operand stays
in range); the companion is not authenticated (§4.2), and a raw profile
written against the wrong count is rejected later by the raw-profile reader,
which checks it against the map.

A failure at any step rejects the program with a diagnostic (sv0cov registry
codes `COV2201` invalid binding, `COV2202` bytecode/binding mismatch) and runs
nothing.

### 3.1 Older VMs

A VM without this revision never misdecodes `COVER_HIT`: the reference sv0vm
decodes every function while loading and fails with `unknown opcode 119`
before execution starts (`Bytecode.decodeInsnVec`, via `decodeFile` → `decodeAll`; the `| _ => raise Fail
("unknown opcode ...")` arm). The `sv0vm-implementation-expand` profiles
likewise fail every unlisted opcode as `ELOAD_UNKNOWN_OPCODE`. `CV-122` pins
this behaviour with a regression test against the pre-coverage decoder.

## 4. The v1 companion binding

### 4.1 Schema

`sv0cov.vm-binding` version `1.0`, a closed canonical JSON object (sorted
keys, no insignificant whitespace, exactly one final LF, no BOM) with exactly
eleven properties:

| Property | Rule |
|---|---|
| `bytecode_length` | integer `1..18446744073709551615`, the exact `.sv0b` byte length |
| `bytecode_sha256` | lowercase hex SHA-256 of those exact bytes |
| `capabilities` | exactly `["sv0cov.coverage.v1"]` |
| `compiler_identity` | 1..128 bytes `0x21..0x7e`, equal to the map's compiler identity |
| `map_id` | lowercase hex of the assembled program map's 32-byte ID |
| `plan_capability` | exactly `"sv0cov.plan.v1"` |
| `profile` | exactly `"sv0vm-v1-coverage"` |
| `program_counter_count` | integer `0..4294967295`, the map's total counter count |
| `raw_profile_version` | exactly `"1.0"` |
| `schema` | exactly `"sv0cov.vm-binding"` |
| `version` | exactly `"1.0"` |

The authoritative schema and validator are sv0cov's
`schemas/sv0cov.vm-binding-1.0.schema.json` and `sv0cov.formats.vmbinding`.

### 4.2 Authority and checks

- The companion is supplied explicitly, e.g. `sv0vm --coverage-binding
  <path> <program.sv0b>`. A file sitting next to the bytecode confers no
  authority.
- A VM rejects a companion larger than 4096 bytes before parsing (the largest
  valid companion is about 500 bytes).
- The VM checks the closed schema, the exact constants, and that
  `bytecode_length` and `bytecode_sha256` match the loaded bytes. Tampered,
  transplanted, or wrong-neighbour companions therefore fail before execution.

### 4.3 Zero counters

A companion with `program_counter_count = 0` is valid only for bytecode with no
`COVER_HIT` (an empty program map). The VM still initialises coverage and
publishes a complete empty profile after orderly execution. A positive count
without any hit, or any hit with a zero count, is rejected (§3 step 5).

## 5. Limits

- `program_counter_count` is at most `4294967295` by encoding. The effective
  bound is the selected raw-profile tier (sv0cov SPEC §16.4): `standard`
  admits 4,194,304 counters, `large` 16,777,216, `custom` as configured. A
  producer refuses to emit a program over its tier; a VM refuses to load one.
- A companion is at most 4096 bytes (§4.2).
- `COVER_HIT` adds no section to v1, so v1 section-size limits are unchanged.

## 6. Deterministic encoding

For the same source, compiler revision, and coverage plan, a producer emits
byte-identical bytecode and byte-identical companion JSON. Hits are placed
exactly where the plan's instrumentation points are (one `COVER_HIT` per
planned counter placement, local index from the plan); the same plan drives
generated C, so VM and native counts agree (sv0cov SPEC COV-VM-001).

## 7. Reserved identifiers

<!-- BEGIN GENERATED: coverage identifiers (scripts/gen_coverage_identifiers.py) -->
| Identifier | Exact representation | Scope |
|---|---|---|
| `COVER_HIT` | opcode 119 (`0x77`), `u32le` operand, 5 bytes | every profile, every container version |
| coverage_capability | `sv0cov.coverage.v1` | v1 companion and v2 section |
| plan_capability | `sv0cov.plan.v1` | v1 companion and v2 section |
| v1_profile | `sv0vm-v1-coverage` | companion `profile` |
| v2_profile | `sv0vm-v2-typed` | v2 container with the coverage capability (R1) |
| v2_section_tag | `COVR` (ASCII `43 4f 56 52`) | unique v2 section tag (R1) |
| vm_binding_schema | `sv0cov.vm-binding` | `.sv0covbind.json` `schema` |
| vm_binding_version | `1.0` | `.sv0covbind.json` `version` |
<!-- END GENERATED: coverage identifiers -->

The table is generated from the machine-readable registry
[`coverage-identifiers.json`](coverage-identifiers.json). sv0c and sv0vm keep
byte-identical copies that their test suites check against their encoders
and decoders, and the sv0-toolchain root guard checks every copy and sv0cov's
constants against this file (CV-102). Comparisons are byte-exact and
case-sensitive; no aliases, prefixes, normalisation, or case folding.
