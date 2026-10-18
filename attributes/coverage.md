# the `coverage` attribute

normative for sv0 source. `#[coverage(...)]` marks code whose coverage is
deliberately left out of the measurement, with a reason that stays visible in
every report. it is defined here, once, for every compiler and backend; the
coverage tool (sv0cov) consumes the result. machine-readable form:
[`coverage-attribute.json`](coverage-attribute.json), generated with the
tables below by `scripts/gen_coverage_attribute.py`.

sources: sv0cov SPEC 13.4, 19.2, 19.4 (COV-EXC-007, -008, -012, -013, -014,
-016, -019..-024); grammar: [`grammar/sv0.ebnf`](../grammar/sv0.ebnf) section 12.

```sv0
#[coverage(off, reason = "platform-specific failure path")]
fn abort_on_unsupported_host() -> i32 {
    return 1;
}

fn decode_known_tag(tag: i32) -> i32 {
    #[coverage(branch_off, reason = "validated decoder state proves the false outcome impossible")]
    if tag < 0 {
        return fallback();
    };
    return tag;
}
```

## 1. the reserved namespace

the top-level attribute path `coverage` is reserved for toolchain-wide
coverage semantics. it is not a plugin namespace of one tool, and its meaning
does not change with the language or engine that produces reports. no other
attribute may give `coverage` another meaning.

spelling is exact and ASCII case-sensitive. `Coverage`, `COVERAGE`,
`sv0cov`, and prefixed forms such as `sv0::coverage` are not aliases: any
attribute path other than exactly `coverage` whose single or last segment is
`coverage` or `sv0cov`, compared without regard to ASCII case, is rejected
(`COV3201`).

## 2. placement and attachment

attributes may precede items and statements:

```ebnf
attributed_item      = { attribute } , item ;
attributed_statement = { attribute } , statement ;
```

this covers top-level items, items nested in blocks, `impl` and `trait`
members, and every statement of a block (`let`, assignment, expression
statement including `return`, `break`, `continue`, `if`, `while`, `for`,
`loop`, `match`, and an explicit `{ ... }` block).

an attribute attaches to exactly the next item or statement. only whitespace,
comments (including doc comments), and further attributes may come between
them. attachment never follows line numbers, indentation, or textual
proximity: an attribute on the line above a statement and one on the same line
attach the same way, and an attribute separated from a statement by a blank
line still attaches to it.

there is no expression attribute. an attribute is rejected (`COV1021`) when
what follows it is not an item or statement: a block's tail expression, an
operand, a match arm, a struct field, an enum variant, a parameter, `else`, a
lone `;`, a closing `}`, a `use` or `module` declaration, or the end of the
file. to exclude part of an expression, use a comment directive (section 6).

several attributes may precede one construct. their order is kept, and a
`coverage` attribute means the same whatever other attributes stand beside it.

## 3. the argument form

```text
#[coverage(<mode>, reason = "<text>")]
```

exactly two arguments, in this order:

1. one bare mode identifier from section 4;
2. `reason = ` followed by one string literal whose value is 1 to 1,024 bytes
   of UTF-8.

every other shape is an error: no argument list, the `= literal` attribute
form, a missing, unknown, or differently cased mode, the reason before the
mode, a duplicate or extra argument, a nested argument list, or a reason that
is not a string literal or is too long (`COV3201`). a missing or empty reason
is `COV3207`.

## 4. modes

there are exactly three modes, with no synonym. there is no `function_off`,
`region_off`, `line_off`, or list of metrics: a line is excluded only because
the regions that make it up are.

<!-- BEGIN GENERATED: coverage modes (scripts/gen_coverage_attribute.py) -->
| Mode | Attaches to | Effect |
|---|---|---|
| `off` | a `fn`, or an `impl` or `trait` with at least one function body, or any statement | excludes the ordinary coverage (function, region, derived line, branch) of the construct and its whole ordinary subtree; contract clauses stay measured |
| `branch_off` | an `if`, `while`, `for`, `loop` or `match` statement | excludes only the outcomes the decision owns directly; its region, line, body and nested decisions stay ordinary |
| `contract_off` | a `fn` that owns at least one contract clause | removes the clauses the function owns directly from contract-coverage denominators; enforcement, proof disposition and ordinary coverage are unchanged |
<!-- END GENERATED: coverage modes -->

details:

- **`off`** on a function excludes its entry and its ordinary body; on an
  `impl` or `trait`, every function body in it; on a statement, that
  statement and every region and decision inside it. `off` on an item with no
  executable code (`struct`, `enum`, type alias, newtype, `const`, `static`, a
  `trait` without function bodies) is `COV1021`.
- **`branch_off`** excludes the outcomes the coverage planner gives the
  decision itself: `true`/`false` of an `if`, `body`/`exit` of a `while`,
  `for`, or `loop`, the arms of a `match`. it does not reach decisions nested
  in a body. on any other construct (functions, declarations, calls,
  assignments, `return`, `break`, `continue`, explicit blocks) it is
  `COV1021`.
- **`contract_off`** does not turn contracts off: runtime-checked clauses still
  run, statically verified clauses keep their proof disposition, and a
  violation behaves as always. the report keeps their evaluation data as
  excluded evidence. the clauses a function owns directly are its `requires`,
  `ensures`, and every `loop_invariant` and `assert` whose nearest enclosing
  function it is. on a statement, or on a function that owns no clause, it is
  `COV1021`.

one construct may carry several `coverage` attributes only when their effects
are disjoint, such as `off` and `contract_off` on a function with contracts.
the same mode twice, `off` with `branch_off`, or an exclusion inside the
subtree of an enclosing `off` that already covers it is `COV3203`. an
exclusion inside an `off` subtree that the `off` does not cover (a
`contract_off` on a nested function with contracts) is allowed.

## 5. validation and effect

a compiler parses, keeps, and validates `coverage` attributes in every build,
with or without coverage. everything in sections 1 to 4 is checked whatever
the coverage mode, so a malformed or misplaced attribute fails the first
ordinary build. only the effect depends on the mode: with `--coverage=off`
nothing is excluded or emitted; with `map` or `instrument` the excluded
constructs stay in the coverage map as exclusion records (sv0cov SPEC 16.3)
and leave only their denominators.

the parser and syntax tree keep every attribute in order with its span, the
span of each argument, and the identity of the construct it attaches to. a
formatter keeps the attachment and writes each attribute on its own line
directly before its construct, at the construct's indentation.

the same source gives the same exclusions for every backend (generated C and
both VM profiles). there is no way to exclude code for one backend only.

a compiler that does not implement these semantics rejects the attribute
instead of ignoring it.

## 6. comment directives

where an attribute cannot go (inside an expression), coverage uses comment
directives, `// sv0cov: ignore-next reason="..."` and an `ignore-start` /
`ignore-end` pair. a comment beginning `// sv0cov:` is reserved for them.
their grammar and scan are sv0cov SPEC 19.3; an attribute and a directive that
give the same construct different policy are `COV3202`.

## 7. diagnostics

the codes are sv0cov's diagnostic registry codes, reported by the compiler
as `error[COVxxxx]` at the attribute's span (the argument's span where one
argument is at fault).

<!-- BEGIN GENERATED: coverage attribute diagnostics (scripts/gen_coverage_attribute.py) -->
| Code | Title | When |
|---|---|---|
| `COV1021` | Unsupported coverage attribute placement | the attribute is not followed by an item or statement (an expression, a match arm, a field, a variant, a parameter, `else`, a lone `;`, a closing `}`, a `use` or `module` declaration, the end of the file), or its mode cannot apply to the construct it attaches to |
| `COV3201` | Invalid coverage exclusion | the content is not exactly `coverage(<mode>, reason = "<text>")`: no argument list, an `= literal` form, an unknown or differently cased mode, the mode not first, a missing mode, a duplicate or extra argument, a nested argument list, a reason that is not a string literal or is longer than 1,024 bytes; or a rejected namespace spelling |
| `COV3202` | Conflicting coverage exclusions | an attribute and a comment directive give the same construct different policy |
| `COV3203` | Redundant coverage exclusion | one construct has the same mode twice, or `off` together with `branch_off`; or an exclusion lies inside the subtree of an enclosing `off` whose effect already includes it |
| `COV3207` | Coverage exclusion has no reason | the `reason` argument is missing, or its string is empty |
<!-- END GENERATED: coverage attribute diagnostics -->

## 8. implementation status

this page is the R0.1 language definition (sv0cov CV-301). sv0c keeps and
validates `coverage` attributes since sv0cov CV-302: a front-end pass
(`sv0c/lib/attributes.sv0`) records every attribute with its span, argument
spans, and the construct it attaches to, checks sections 1 to 3 in every
build with the diagnostics of section 7, and gives the parser the token
stream without the attributes it need not see. the mode-to-construct and
redundancy checks of section 4 and the exclusion effect come with CV-305;
until then a valid `coverage` attribute is refused in a `--coverage=map` or
`instrument` build (`COV1021`) rather than ignored. the workspace formatter
(`scripts/fmt_sv0.py`) lays attributes out as section 5 says since CV-303,
keeping every attachment and argument; where the construct shares a line with
earlier code it reports an error instead of choosing an indentation. comment
directives come with CV-304.
