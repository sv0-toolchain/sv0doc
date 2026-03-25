# milestone 0 review: spec completeness assessment

completed: 2026-03-23

this document records the findings from the milestone 0 completeness and
consistency review. all five spec deliverables are present and substantial.
grammar bugs have been fixed inline. the items below are open design
questions that should be resolved during milestone 1 implementation.

---

## grammar fixes applied

the following bugs were fixed directly in `grammar/sv0.ebnf`:

| fix | description |
|-----|-------------|
| type_path `::` before `<` | made optional -- `Vec<i32>` now valid (D18) |
| associated type bindings | added `identifier "=" type_expr` to type args -- `Output = T` |
| tuple field access | added `.0`, `.1` to postfix_op |
| mutable slice type | `&mut [T]` now parseable via `slice_type` |
| attributes reachable | `source_file` now accepts `{ attribute }` before items |
| negative impls reachable | `impl_neg` added to `impl_def` alternatives |
| where clauses | added `where_clause` production; attached to fn, struct, trait, impl |
| Self::Item access | added `self_type_path` production to `type_expr` |
| supertrait syntax | `trait Eq: PartialEq` now parseable via trait_def |
| unit expression | `()` added to `primary_expr` |
| break with value | `break expr;` now valid for loop expressions |
| if-let else chaining | `if let` now supports `else if` and `else if let` |
| expr overlap | removed redundant `or_expr` alternative from `expr` |
| precedence comment | removed incorrect `as` from postfix level |
| refinement predicate | relaxed to arbitrary `expr` (was `self <op> expr` only) |
| Some/None/Ok/Err | moved from keywords to identifiers (D19) |
| closure disambiguation | documented as D21 (check for `=>` after `)`) |
| struct literal restriction | documented as D22 (no struct exprs in conditions) |
| return type omission | documented as D23 (`-> ()` is optional) |

keyword count updated from 47 to 43 in `keywords/reference.md`.

---

## design question resolutions

resolved: 2026-03-23 (milestone 1 planning)

### Q1. string literal type and ownership model -- RESOLVED

`"hello"` has type `&string` with static (program) lifetime. it points to
read-only data embedded in the binary. assigning to a `string` binding
(`let s: string = "hello"`) copies from static data to a heap allocation.
no separate `str` type -- `&string` serves both roles.

### Q2. integer overflow behavior -- RESOLVED

panic in `runtime` contract mode (the default), wrap in `disabled` contract
mode. this aligns with the contract system's philosophy: safety by default,
opt-out for performance. matches the Rust debug/release model.

### Q3. closure capture rules -- DEFERRED

closures are excluded from the milestone 1 bootstrap subset. the
Fn/FnMut/FnOnce trait hierarchy and capture rules will be specified when
closures are added (milestone 2+). programs use named functions and
`for..in` loops instead of iterator adapters with closures.

### Q4. for-loop desugaring -- RESOLVED

milestone 1 supports **range-based for-loops only**. `for x in 0..n { body }`
desugars to:

```
{
    let mut __i = 0;
    while __i < n {
        let x = __i;
        body;
        __i += 1;
    }
}
```

full iterator-protocol desugaring (IntoIterator + Iterator::next) deferred
to when closures and the iterator trait hierarchy are implemented.

### Q5. `?` operator desugaring -- RESOLVED

hardcoded for Result and Option. no `Try` trait.

- on `Result<T, E>`: `match expr { Ok(v) => v, Err(e) => return Err(e) }`
- on `Option<T>`: `match expr { Some(v) => v, None => return None }`

### Q6. Vec, Box, and standard library types -- RESOLVED

compiler builtins for milestone 1 with known method sets:

- `Vec<T>`: `.new()`, `.push()`, `.len()`, `.get()`, index access
- `Box<T>`: `.new()`
- `string`: `.len()`

represented as C structs in codegen. methods registered as inherent impls
that the type checker knows about internally. full library implementation
deferred.

### Q7. println / print / format! semantics -- RESOLVED

`println` and `print` are compiler intrinsics. the parser sees them as
normal function calls; the type checker recognizes them and validates:

- format string must be a string literal (no dynamic format strings)
- `{}` count must match argument count
- each `{}` argument must implement `Display`
- `{:?}` arguments must implement `Debug`

codegen emits `printf`-based C code. `format!` macro deferred to macro system.

### Q8. reborrowing and auto-ref rules -- RESOLVED

`&mut T` can be reborrowed as `&T` for the duration of a call. method
receiver resolution tries `T`, `&T`, `&mut T` in order (following Rust).
auto-ref: if `v` is `Vec<i32>` and `.len()` takes `&Self`, compiler
inserts `&v`.

### Q9. borrow scope model -- RESOLVED

**lexical scopes only** for milestone 1. borrows live until end of the
enclosing block. full NLL (non-lexical lifetimes with control-flow-sensitive
analysis) deferred to milestone 2.

### Q10. module system -- RESOLVED

one file = one module. `module a::b;` declares the module path. `use`
imports resolve by searching `<project>/a/b.sv0` then `<project>/a/b/mod.sv0`.
`core::option`, `core::result`, and `core::ops` are implicitly available.
for milestone 1, single-file compilation with builtins is the minimum;
multi-file is a stretch goal.

---

## items confirmed as correct and consistent

- Copy/Clone auto-derivation rules match across type-system and memory-model
- Drop semantics (reverse declaration order, partial moves) are consistent
- Send/Sync marker trait inference rules are consistent
- borrows() contract semantics match across memory-model and contracts
- three-tier borrow tracking (local, elision, explicit) is well-defined
- contract verification phases (runtime, local static, modular) are clear
- narrowing cast contract insertion is specified with pseudocode
- operator-to-trait desugaring table is complete for arithmetic
- all 43 keywords have grammar productions
- all operators have grammar productions with correct precedence

---

## milestone 1 bootstrap subset

the following features are IN SCOPE for milestone 1:

- all primitive types, arrays, tuples, unit
- let/mut bindings with/without type annotations
- functions with params, return types, early return
- if/else, while, for..in (range only), loop, break (with value), continue, match
- structs (fields, methods via impl), enums (all variant forms)
- basic generics (type params with single trait bounds, monomorphization)
- basic trait def/impl, inherent impls, operator desugaring to traits
- contracts: requires, ensures, loop_invariant -- runtime checks only
- contract builtins: result, old(), forall(), exists(), no_alias()
- Option/Result/Vec/Box/string as compiler builtins
- println/print as compiler intrinsics
- all operators (arithmetic, comparison, logical, bitwise, assignment)
- patterns (wildcard, binding, literal, tuple, struct, enum, or, guards)
- modules (module declaration, use imports, pub/pub(project))
- ? operator for Result/Option
- as casts with narrowing contract insertion

## items explicitly deferred (not needed for milestone 1)

| item | deferred to | notes |
|------|-------------|-------|
| closures | milestone 2+ | complex capture rules; use named fns + for-loops |
| GATs (generic associated types) | milestone 2+ | significant type checker complexity |
| refined types (`where self > 0`) | phase 2+ | parser accepts; type checker rejects |
| `#[derive(Debug)]` | milestone 4+ | manual Debug impls until macro system |
| const expression evaluation (`{N+1}`) | milestone 2+ | literal const args only |
| trait objects (`dyn Trait`) | milestone 2+ | static dispatch sufficient |
| `impl Trait` return types | milestone 2+ | not needed for bootstrap |
| function overloading | milestone 2+ | use distinct names |
| negative impls (`impl !Send`) | milestone 2+ | parse but reject |
| unsafe blocks / raw pointers | milestone 2+ | not needed for bootstrap |
| Send/Sync inference | milestone 2+ | no concurrency in bootstrap |
| SMT solver integration | phase 2+ | runtime contracts only |
| purity checking for contracts | phase 2+ | trust programmer |
| non-lexical lifetimes (NLL) | milestone 2 | lexical scopes in milestone 1 |

## task Rmd corrections

the following corrections apply to the milestone 1 task `.Rmd` files:

- **`sv0c-lexer.Rmd`**: lists `SOME | NONE | OK | ERR` as keyword tokens.
  remove these -- grammar D19 makes them identifiers (`IDENT "Some"`, etc.)
- **`sv0c-parser.Rmd`**: operator precedence order differs from grammar.
  use the grammar's 14-level order as the source of truth.
- **`sv0c-project-setup.Rmd`**: proposes per-module `sources.cm` files.
  use a single flat `sources.cm` instead to avoid CM sub-group complexity.

---

## conclusion

the sv0doc specification is comprehensive and implementable for milestone 1.
the grammar fixes above resolve all mechanical issues. all 10 open design
questions (Q1-Q10) have been resolved with concrete decisions. the milestone 1
bootstrap subset is scoped to produce a working compiler for practical sv0
programs with contracts, deferring advanced features to later milestones.

**milestone 0 status: complete.**
**milestone 1 status: planning complete, implementation starting.**
