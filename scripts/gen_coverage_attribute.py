#!/usr/bin/env python3
"""The `coverage` attribute and comment-directive registry (sv0cov CV-301,
CV-304; SPEC 13.4, 19.2, 19.3, 19.4; COV-EXC-002, COV-EXC-007, COV-EXC-008,
COV-EXC-012, COV-EXC-019).

``attributes/coverage-attribute.json`` is the single machine-readable
statement of the reserved namespace, the exact argument form, the three
modes and where each may attach, the rejected namespace spellings, the
comment-directive grammar, and the diagnostic for each rejection. This script writes it and renders the two
tables of ``attributes/coverage.md`` from it (between the GENERATED
markers), or checks that both are current. sv0c's attribute validation
(CV-302, CV-305) and directive scan (CV-304) are tested against this
registry.

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
                     "the construct it attaches to; an `ignore-next` directive with no code after it in its file, or whose next code is not "
                     "an item, a statement, or an `if` or `match` expression; an `ignore-start` region with no code; in a coverage build, "
                     "an exclusion that takes nothing the coverage planner planned, and `contract_off` until contract coverage exists "
                     "(sv0cov CV-306)"},
            {"code": "COV3201", "title": "Invalid coverage exclusion",
             "when": "the content is not exactly `coverage(<mode>, reason = \"<text>\")`: no argument list, an `= literal` form, an unknown "
                     "or differently cased mode, the mode not first, a missing mode, a duplicate or extra argument, a nested argument list, a "
                     "reason that is not a string literal, is longer than 1,024 bytes, or holds a NUL, CR or LF (or an escape above `0x7e`); "
                     "or a rejected namespace spelling; a comment "
                     "directive that is not spelled exactly as section 6 says (not alone on its line, a block or doc comment, another "
                     "spacing or case, an unknown action, a reason not written `reason=\"...\"`, unclosed or longer than 1,024 bytes, text "
                     "after it); an `ignore-end` without a start, or an `ignore-start` never closed in its file; an `ignore-start` region "
                     "that does not begin and end between the items or statements of one block"},
            {"code": "COV3202", "title": "Conflicting coverage exclusions",
             "when": "a comment directive and an `off` or `branch_off` attribute name the same construct"},
            {"code": "COV3203", "title": "Redundant coverage exclusion",
             "when": "one construct has the same mode twice, or `off` together with `branch_off`; or an exclusion lies inside the subtree "
                     "of an enclosing `off` (or comment directive) whose effect already includes it; a directive inside an open "
                     "`ignore-start` region, or between an `ignore-next` and its construct"},
            {"code": "COV3207", "title": "Coverage exclusion has no reason",
             "when": "the `reason` argument (or a directive's `reason=`) is missing, or its string is empty"},
        ],
        "directives": {
            "actions": ["ignore-next", "ignore-start", "ignore-end"],
            "attempt": "a line or block comment whose text, after the comment opener and spaces or tabs, starts with `sv0cov:` "
                       "compared without regard to ASCII case",
            "end_form": "// sv0cov: ignore-end",
            "form": "// sv0cov: <ignore-next|ignore-start> reason=\"<text>\"",
            "nesting": "none: a directive inside an open region, or between an ignore-next and its construct, is redundant",
            "prefix": "// sv0cov:",
            "reason": {"escapes": "string literal", "forbidden": ["NUL", "CR", "LF"], "max_bytes": 1024,
                       "max_escape_byte": 126, "min_bytes": 1},
            "resolution": {"ignore-next": "the next item, statement, or if/match expression after attributes, use/module "
                                          "declarations and items with no code",
                           "region": "between the items or statements of one block"},
            "separator": "one or more spaces or tabs; only spaces or tabs after the last part",
            "unit": "one source file",
        },
        "form": {
            "arguments": ["mode", "reason"],
            "example": "#[coverage(off, reason = \"platform-specific failure path\")]",
            "reason": {"forbidden": ["NUL", "CR", "LF"], "literal": "string", "max_bytes": 1024, "max_escape_byte": 126,
                       "min_bytes": 1},
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
        "version": "1.2",
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
