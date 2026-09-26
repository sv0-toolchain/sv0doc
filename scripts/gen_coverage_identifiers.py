#!/usr/bin/env python3
"""Coverage identifier registry (CV-102; sv0cov SPEC COV-VM-017, COV-VM-019, COV-VM-020).

``bytecode/coverage-identifiers.json`` is the single source for the opcode
and string identifiers that sv0doc, sv0c, sv0vm, and sv0cov must agree on.
This script renders the reserved-identifier table in
``bytecode/coverage.md`` from it (between the GENERATED markers). sv0c and
sv0vm carry byte-identical copies checked by their own test suites, and the
sv0-toolchain root guard checks every copy against this file.

    python3 scripts/gen_coverage_identifiers.py          # check
    python3 scripts/gen_coverage_identifiers.py --write
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "bytecode" / "coverage-identifiers.json"
PAGE = ROOT / "bytecode" / "coverage.md"
BEGIN = "<!-- BEGIN GENERATED: coverage identifiers (scripts/gen_coverage_identifiers.py) -->\n"
END = "<!-- END GENERATED: coverage identifiers -->\n"


def registry() -> dict:
    return {
        "identifiers": [
            {"name": "coverage_capability", "scope": "v1 companion and v2 section", "value": "sv0cov.coverage.v1"},
            {"name": "plan_capability", "scope": "v1 companion and v2 section", "value": "sv0cov.plan.v1"},
            {"name": "v1_profile", "scope": "companion `profile`", "value": "sv0vm-v1-coverage"},
            {"name": "v2_profile", "scope": "v2 container with the coverage capability (R1)", "value": "sv0vm-v2-typed"},
            {"name": "v2_section_tag", "scope": "unique v2 section tag (R1)", "value": "COVR"},
            {"name": "vm_binding_schema", "scope": "`.sv0covbind.json` `schema`", "value": "sv0cov.vm-binding"},
            {"name": "vm_binding_version", "scope": "`.sv0covbind.json` `version`", "value": "1.0"},
        ],
        "opcodes": [{"encoded_length": 5, "name": "COVER_HIT", "opcode": 119, "operand": "u32le", "stack_effect": "none"}],
        "schema": "sv0.coverage-identifiers",
        "version": "1.0",
    }


def encode(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def table(reg: dict) -> str:
    rows = ["| Identifier | Exact representation | Scope |", "|---|---|---|"]
    for op in reg["opcodes"]:
        rows.append(f"| `{op['name']}` | opcode {op['opcode']} (`0x{op['opcode']:02x}`), `{op['operand']}` operand, {op['encoded_length']} bytes | every profile, every container version |")
    for ident in reg["identifiers"]:
        extra = " (ASCII `43 4f 56 52`)" if ident["value"] == "COVR" else ""
        rows.append(f"| {ident['name']} | `{ident['value']}`{extra} | {ident['scope']} |")
    return "\n".join(rows) + "\n"


def render_page(text: str, reg: dict) -> str:
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    return head + BEGIN + table(reg) + END + tail


def main() -> int:
    reg = registry()
    data = encode(reg)
    page = render_page(PAGE.read_text(encoding="utf-8"), reg)
    if "--write" in sys.argv:
        REGISTRY.write_bytes(data)
        PAGE.write_text(page, encoding="utf-8")
        print("coverage identifiers: written")
        return 0
    stale = [p.name for p, want in ((REGISTRY, data), (PAGE, page.encode("utf-8"))) if not p.is_file() or p.read_bytes() != want]
    if stale:
        print("coverage identifiers stale: " + ", ".join(stale), file=sys.stderr)
        return 1
    print("coverage identifiers: current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
