# Bytecode container format (sv0)

This document is the **sv0doc** anchor for the bytecode **file layout**. The authoritative wire format and version bytes are defined alongside the reference interpreter in **sv0vm** (see `sv0vm/src/` and milestone-2 task notes).

## Scope

- **Magic / version**: fixed header bytes accepted by the loader.
- **Sections**: code pool, constant pool, entry symbol (if any), and alignment rules as implemented by `sv0c --target=vm` emission and `sv0vm` load.

## Relationship to the toolchain

- **Emit**: `sv0c` VM backend writes `*.sv0b` under `sv0c/build/vm/`.
- **Execute**: `sv0vm` loads the same layout; integration tests exercise round-trips.

When the on-disk layout changes, update this file and the **instructions** reference together.
