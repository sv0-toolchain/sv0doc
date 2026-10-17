#!/usr/bin/env python3
"""The `coverage` attribute registry (sv0cov CV-301; SPEC 13.4, 19.2, 19.4;
COV-EXC-007, COV-EXC-008, COV-EXC-012, COV-EXC-019).

``attributes/coverage-attribute.json`` is the single machine-readable
statement of the reserved namespace, the exact argument form, the three
modes and where each may attach, the rejected namespace spellings, and the
diagnostic for each rejection. This script writes it and renders the two
tables of ``attributes/coverage.md`` from it (between the GENERATED
markers), or checks that both are current. sv0c's attribute validation
(CV-302, CV-305) is tested against this registry.

    python3 scripts/gen_coverage_attribute.py          # check
    python3 scripts/gen_coverage_attribute.py --write
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "attributes" / "coverage-attribute.json"
PAGE = ROOT / "attributes" / "coverage.md"
MARKS = {
    "modes": ("<!-- BEGIN GENERATED: coverage modes (scripts/gen_coverage_attribute.py) -->\n", "<!-- END GENERATED: coverage modes -->\n"),
    "diagnostics": ("<!-- BEGIN GENERATED: coverage attribute diagnostics (scripts/gen_coverage_attribute.py) -->\n",
                    "<!-- END GENERATED: coverage attribute diagnostics -->\n"),
}


def registry() -> dict:
    return {
        "diagnostics": [
            {"code": "COV1021", "title": "Unsupported coverage attribute placement",
             "when": "the attribute is not followed by an item or statement (an expression, a match arm, a field, a variant, a parameter, "
                     "`else`, a lone `;`, a closing `}`, a `use` or `module` declaration, the end of the file), or its mode cannot apply to "
                     "the construct it attaches to"},
            {"code": "COV3201", "title": "Invalid coverage exclusion",
             "when": "the content is not exactly `coverage(<mode>, reason = \"<text>\")`: no argument list, an `= literal` form, an unknown "
                     "or differently cased mode, the mode not first, a missing mode, a duplicate or extra argument, a nested argument list, a "
                     "reason that is not a string literal or is longer than 1,024 bytes; or a rejected namespace spelling"},
            {"code": "COV3202", "title": "Conflicting coverage exclusions",
             "when": "an attribute and a comment directive give the same construct different policy"},
            {"code": "COV3203", "title": "Redundant coverage exclusion",
             "when": "one construct has the same mode twice, or `off` together with `branch_off`; or an exclusion lies inside the subtree "
                     "of an enclosing `off` whose effect already includes it"},
            {"code": "COV3207", "title": "Coverage exclusion has no reason",
             "when": "the `reason` argument is missing, or its string is empty"},
        ],
        "form": {
            "arguments": ["mode", "reason"],
            "example": "#[coverage(off, reason = \"platform-specific failure path\")]",
            "reason": {"literal": "string", "max_bytes": 1024, "min_bytes": 1},
        },
        "modes": [
            {"attaches_to": "a `fn`, or an `impl` or `trait` with at least one function body, or any statement",
             "effect": "excludes the ordinary coverage (function, region, derived line, branch) of the construct and its whole ordinary "
                       "subtree; contract clauses stay measured",
             "name": "off"},
            {"attaches_to": "an `if`, `while`, `for`, `loop` or `match` statement",
             "effect": "excludes only the outcomes the decision owns directly; its region, line, body and nested decisions stay ordinary",
             "name": "branch_off"},
            {"attaches_to": "a `fn` that owns at least one contract clause",
             "effect": "removes the clauses the function owns directly from contract-coverage denominators; enforcement, proof disposition "
                       "and ordinary coverage are unchanged",
             "name": "contract_off"},
        ],
        "namespace": "coverage",
        "rejected_namespaces": {
            "examples": ["Coverage", "COVERAGE", "sv0cov", "Sv0cov", "sv0::coverage", "tool::coverage"],
            "rule": "any attribute path other than exactly `coverage` whose single segment, or last segment, equals `coverage` or `sv0cov` "
                    "when compared without regard to ASCII case",
        },
        "schema": "sv0.coverage-attribute",
        "version": "1.0",
    }


def encode(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def tables(reg: dict) -> dict[str, str]:
    modes = ["| Mode | Attaches to | Effect |", "|---|---|---|"]
    modes += [f"| `{m['name']}` | {m['attaches_to']} | {m['effect']} |" for m in reg["modes"]]
    diags = ["| Code | Title | When |", "|---|---|---|"]
    diags += [f"| `{d['code']}` | {d['title']} | {d['when']} |" for d in reg["diagnostics"]]
    return {"modes": "\n".join(modes) + "\n", "diagnostics": "\n".join(diags) + "\n"}


def render_page(text: str, reg: dict) -> str:
    for key, body in tables(reg).items():
        begin, end = MARKS[key]
        head, rest = text.split(begin, 1)
        _, tail = rest.split(end, 1)
        text = head + begin + body + end + tail
    return text


def main() -> int:
    reg = registry()
    data = encode(reg)
    page = render_page(PAGE.read_text(encoding="utf-8"), reg)
    if "--write" in sys.argv:
        REGISTRY.write_bytes(data)
        PAGE.write_text(page, encoding="utf-8")
        print("coverage attribute: written")
        return 0
    stale = [p.name for p, want in ((REGISTRY, data), (PAGE, page.encode("utf-8"))) if not p.is_file() or p.read_bytes() != want]
    if stale:
        print("coverage attribute registry stale: " + ", ".join(stale), file=sys.stderr)
        return 1
    print("coverage attribute: current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
