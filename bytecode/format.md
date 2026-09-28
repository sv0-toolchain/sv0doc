# Bytecode container format (sv0)

This document is the **sv0doc** anchor for the bytecode **file layout**. The authoritative wire format and version bytes are defined alongside the reference interpreter in **sv0vm** (see `sv0vm/src/` and milestone-2 task notes).

> **Planned normative extraction.** Per
> `project-specs/sv0vm-implementation-expand/SPEC.md` (GOV-001, Phase 0), this
> file becomes the complete `.sv0b` v1 container contract (primitive
> encodings, sections, 20-byte function records, canonicality), and the v2
> typed container is frozen here before independent VM implementations
> start. Until then, the audited `sv0c` encoder, native VM emitter, `sv0vm`
> decoder, and parity corpus are the provisional baseline. Planning: parent
> repo `task/sv0vm-multi-implementation.Rmd` (VMX-002, VMX-005).

## Scope

- **Magic / version**: fixed header bytes accepted by the loader.
- **Sections**: code pool, constant pool, entry symbol (if any), and alignment rules as implemented by `sv0c --target=vm` emission and `sv0vm` load.

## Relationship to the toolchain

- **Emit**: `sv0c` VM backend writes `*.sv0b` under `sv0c/build/vm/`.
- **Execute**: `sv0vm` loads the same layout; integration tests exercise round-trips.

## Coverage

The coverage revision (`coverage.md`) does not change the v1 layout: coverage
metadata for `sv0vm-v1-coverage` lives in an explicit, digest-bound companion
file, never in or after the `.sv0b` bytes.

When the on-disk layout changes, update this file and the **instructions** reference together.
