# sv0 contract system semantics

formal specification of the sv0 contract system. contracts are the defining
feature of sv0 — this document is precise enough to implement the contract
analyzer in sv0c.

extracted from: sv0 compiler vision and design document

---

## 1. contract syntax

### 1.1 contract clauses

contracts are clauses that appear between a function's signature and its body.
they assert properties that must hold at function entry (preconditions) or
function exit (postconditions).

```
fn name(params) -> ReturnType
    requires(precondition_expr)
    ensures(postcondition_expr)
{
    // body
}
```

### 1.2 requires (precondition)

`requires(expr)` — must be true when the function is called.

- `expr` must evaluate to `bool`
- `expr` may reference function parameters
- the compiler checks all call sites against the precondition
- multiple `requires` clauses are conjunctive (all must hold)

```
fn gcd(a: u32, b: u32) -> u32
    requires(a > 0)
    requires(b > 0)
{ ... }
```

### 1.3 ensures (postcondition)

`ensures(expr)` — must be true when the function returns.

- `expr` must evaluate to `bool`
- `expr` may reference function parameters, `result`, and `old(expr)`
- multiple `ensures` clauses are conjunctive (all must hold)

```
fn gcd(a: u32, b: u32) -> u32
    ensures(result > 0)
    ensures(a % result == 0 && b % result == 0)
{ ... }
```

### 1.4 loop_invariant

`loop_invariant(expr)` — must be true at the start of every loop iteration.

- appears between the `while` condition and the loop body
- `expr` must evaluate to `bool`
- `expr` may reference variables in scope
- multiple `loop_invariant` clauses are conjunctive

```
while y != 0
    loop_invariant(x > 0 && y > 0)
{
    let temp = y;
    y = x % y;
    x = temp;
}
```

### 1.5 placement rules

| clause             | placement                                      |
|--------------------|------------------------------------------------|
| `requires(expr)`   | between function signature and body            |
| `ensures(expr)`    | between function signature and body            |
| `borrows(x, y)`    | between function signature and body            |
| `loop_invariant`   | between `while` condition and loop body        |

### 1.6 multiple clauses

multiple contract clauses of the same kind form a conjunction — all must hold
simultaneously. the order of clauses does not matter.

```
fn f(x: i32) -> i32
    requires(x > 0)
    requires(x < 100)
    ensures(result > x)
    ensures(result < x * x)
{ ... }
```

is equivalent to:

```
requires(x > 0 && x < 100)
ensures(result > x && result < x * x)
```

---

## 2. contract builtins

### 2.1 result

`result` binds to the function's return value inside `ensures` clauses.

**scope:** only valid inside `ensures`.

**type:** same as the function's return type.

**usage patterns:**

for simple return types, `result` binds directly:

```
fn abs(x: i32) -> i32
    ensures(result >= 0)
{ ... }
```

for tuple return types, use `.0`, `.1`, etc.:

```
fn encrypt(key: &Key, plaintext: &[u8]) -> (Vec<u8>, Tag)
    ensures(result.0.len() == plaintext.len())
{ ... }
```

for `Result<T, E>` or `Option<T>` return types, use `match`:

```
fn parse_port(input: &string) -> Result<u16, ParseError>
    ensures(match result {
        Ok(port) => port > 0,
        Err(_)   => true,
    })
{ ... }
```

**compilation:**

the compiler binds `result` to the function's return value before evaluating the
postcondition. for runtime checks, this means saving the return value in a
temporary and evaluating the ensures expression before returning.

### 2.2 old(expr)

`old(expr)` captures the value of `expr` at function entry for comparison in
postconditions.

**scope:** only valid inside `ensures`.

**semantics:**

- the compiler evaluates `expr` at function entry (before any mutations)
- the captured value is stored in a compiler-generated temporary
- inside the ensures clause, `old(expr)` refers to this captured value

**examples:**

```
fn fill_random(buf: &mut [u8]) -> ()
    ensures(buf.len() == old(buf.len()))
{ ... }

fn push(vec: &mut Vec<u8>, value: u8) -> ()
    ensures(vec.len() == old(vec.len()) + 1)
{ ... }

fn swap(a: &mut u8, b: &mut u8) -> ()
    requires(no_alias(a, b))
    ensures(*a == old(*b) && *b == old(*a))
{ ... }
```

**runtime implementation:**

for runtime-checked contracts, the compiler generates code to snapshot the
`old(expr)` values at function entry:

```
// compiler-generated pseudocode for swap:
fn swap(a: &mut u8, b: &mut u8) {
    let __old_b = *b;   // snapshot old(*b)
    let __old_a = *a;   // snapshot old(*a)
    // ... function body ...
    assert(*a == __old_b && *b == __old_a);  // ensures check
}
```

### 2.3 forall (universal quantifier)

`forall(var in range, predicate)` — true if `predicate` holds for every value
of `var` in `range`.

**scope:** valid inside `requires`, `ensures`, and `loop_invariant`.

**semantics:**

- `var` is a fresh binding scoped to `predicate`
- `range` is any expression implementing `IntoIterator` (typically a range like `0..n`)
- `predicate` is a boolean expression that may reference `var`

**runtime behavior (phase 1):**

iterated over the entire range. equivalent to:

```
let mut __result = true;
for var in range {
    if !predicate {
        __result = false;
        break;
    }
}
__result
```

**static behavior (phase 2+):**

the SMT solver attempts to prove the universally quantified property without iteration.

**examples:**

```
fn sort(data: &mut [i32]) -> ()
    ensures(forall(i in 0..data.len() - 1, data[i] <= data[i + 1]))
{ ... }

fn fill(buf: &mut [u8], value: u8) -> ()
    ensures(forall(i in 0..buf.len(), buf[i] == value))
{ ... }
```

### 2.4 exists (existential quantifier)

`exists(var in range, predicate)` — true if `predicate` holds for at least one
value of `var` in `range`.

**scope:** valid inside `requires`, `ensures`, and `loop_invariant`.

**runtime behavior (phase 1):**

iterated over the entire range. equivalent to:

```
let mut __result = false;
for var in range {
    if predicate {
        __result = true;
        break;
    }
}
__result
```

**examples:**

```
fn contains(haystack: &[i32], needle: i32) -> bool
    ensures(result == exists(i in 0..haystack.len(), haystack[i] == needle))
{ ... }
```

### 2.5 no_alias(a, b)

`no_alias(a, b)` — asserts that two references do not alias (do not point to
overlapping memory).

**scope:** valid inside `requires`.

**semantics:**

- `a` and `b` must be reference or pointer expressions
- the assertion guarantees the compiler and verifier that `a` and `b` refer to
  disjoint memory regions

**example:**

```
fn swap(a: &mut u8, b: &mut u8) -> ()
    requires(no_alias(a, b))
    ensures(*a == old(*b) && *b == old(*a))
{ ... }
```

**verification:**

- phase 1: runtime check compares pointer addresses
- phase 2+: SMT solver reasons about aliasing statically

### 2.6 borrows(x, y)

`borrows(x, y)` — declares which input references the output is tied to.

**scope:** function signatures and struct declarations. NOT inside requires/ensures.

**semantics:**

`borrows(x, y)` replaces Rust-style lifetime parameters. it means: the returned
reference must not outlive `x` or `y`. the caller must keep the named inputs
alive as long as the result is used.

**on function signatures:**

```
fn longest(x: &string, y: &string) -> &string
    borrows(x, y)
{ ... }
```

equivalent to Rust's `fn longest<'a>(x: &'a str, y: &'a str) -> &'a str`.

**on struct declarations:**

```
struct Parser borrows(input) {
    input: &string,
    position: usize,
}
```

means `Parser` cannot outlive the `input` reference it holds.

### 2.7 builtins summary

| builtin                        | valid in                             | purpose                                    |
|--------------------------------|--------------------------------------|--------------------------------------------|
| `result`                       | `ensures`                            | the function's return value                |
| `old(expr)`                    | `ensures`                            | snapshot of `expr` at function entry       |
| `forall(var in range, pred)`   | `requires`, `ensures`, `loop_invariant` | universal quantifier                    |
| `exists(var in range, pred)`   | `requires`, `ensures`, `loop_invariant` | existential quantifier                  |
| `no_alias(a, b)`               | `requires`                           | asserts non-aliasing of references         |
| `borrows(x, y)`                | function/struct declaration          | declares borrow sources for output         |

---

## 3. contract verification phases

### 3.1 phase 1: runtime contracts

all `requires`, `ensures`, and `loop_invariant` are compiled to runtime checks.

**on failure:**

a failed contract check:

1. prints the source location (file, line, column)
2. prints the contract expression as source text
3. prints the values of all referenced variables
4. aborts the program

**code generation:**

```
// source:
fn gcd(a: u32, b: u32) -> u32
    requires(a > 0)
    ensures(result > 0)
{ ... }

// compiled (pseudocode):
fn gcd(a: u32, b: u32) -> u32 {
    if !(a > 0) {
        contract_fail("requires(a > 0)", file, line, [("a", a)]);
    }
    let __result = { ... };  // original body
    if !(__result > 0) {
        contract_fail("ensures(result > 0)", file, line, [("result", __result)]);
    }
    __result
}
```

**availability:** phase 1 (initial compiler).

### 3.2 phase 2: local static verification

the compiler uses an embedded SMT solver (Z3 or lightweight alternative) to
prove contracts locally within a function.

**behavior:**

- contracts that are proven produce NO runtime code
- contracts that cannot be proven REMAIN as runtime checks
- `sv0 verify` reports verification status for every contract

**reporting:**

```
$ sv0 verify
src/gcd.sv0:3  requires(a > 0)          [runtime]  -- cannot prove (input)
src/gcd.sv0:4  ensures(result > 0)      [verified] -- proven via loop invariant
src/gcd.sv0:9  loop_invariant(x > 0)    [verified] -- proven
```

**availability:** phase 2+ (requires SMT solver integration).

### 3.3 phase 3: modular static verification

cross-function verification:

- the caller's arguments are proven against the callee's `requires`
- refinement types are checked at every assignment
- the compiler can prove that a function's preconditions are satisfied by every caller

**examples:**

```
type PositiveInt = i32 where self > 0;

fn double(x: PositiveInt) -> PositiveInt
    ensures(result == x * 2)
{ x * 2 }

let y: PositiveInt = 5;     // compiler proves 5 > 0
let z = double(y);           // compiler proves y > 0 satisfies requires
```

**availability:** phase 3+ (requires stable type system and SMT solver).

---

## 4. contract-mode settings

the `contract-mode` setting controls how contracts are compiled. it can be set in
`sv0.toml` or via the `--contract-mode` flag.

| mode       | behavior                                                          | available from |
|------------|-------------------------------------------------------------------|----------------|
| `runtime`  | all contracts compiled to runtime checks (default)                | phase 1        |
| `verified` | proven contracts stripped; unproven remain as runtime checks      | phase 2+       |
| `disabled` | all contract checks stripped — no runtime cost, no safety net     | phase 1        |

**recommended usage:**

- `runtime` — development and testing. catches bugs early.
- `verified` — production with SMT solver. best of both worlds.
- `disabled` — release builds where performance is critical and contracts have been verified separately via `sv0 verify`.

**configuration:**

```toml
# sv0.toml
[build]
contract-mode = "runtime"
```

```bash
# command line override
sv0 build --contract-mode=verified
```

---

## 5. trait contracts

### 5.1 contracts on trait methods

trait definitions can include contracts on their methods. these contracts define
the behavioral specification that all implementations must satisfy.

```
trait Serialize {
    fn serialize(self: &Self) -> Vec<u8>
        ensures(result.len() > 0);

    fn deserialize(data: &[u8]) -> Result<Self, Error>
        requires(data.len() > 0);
}
```

### 5.2 impl must satisfy trait contracts

an `impl` block MUST satisfy the contracts declared on the trait. the compiler
verifies this at the impl site.

### 5.3 impl can strengthen contracts

implementations may add ADDITIONAL contracts beyond what the trait requires.
these additional contracts apply only when the concrete type is known.

```
impl Serialize for KeyPair {
    fn serialize(self: &Self) -> Vec<u8>
        ensures(result.len() == 96)    // stronger than trait's > 0
    { ... }
}
```

### 5.4 contravariance rules

contract strengthening follows the Liskov Substitution Principle:

| contract   | impl may be...  | reasoning                                  |
|------------|-----------------|---------------------------------------------|
| `requires` | WEAKER          | impl accepts more inputs than trait demands |
| `ensures`  | STRONGER        | impl guarantees more than trait promises    |

- weakening `requires`: `impl requires(x > 0)` is valid when trait has `requires(x > 5)` because the impl accepts a superset of inputs
- strengthening `ensures`: `impl ensures(result.len() == 96)` is valid when trait has `ensures(result.len() > 0)` because the impl guarantees a subset of outputs

---

## 6. narrowing cast contracts

### 6.1 implicit contract insertion

narrowing casts (`larger_type as smaller_type`) implicitly insert a `requires`
contract that the value fits in the target type:

```
let x: u32 = 42;
let z: u8 = x as u8;
// implicitly: requires(x <= 255)
```

### 6.2 verification behavior

- if the compiler can prove the value fits (e.g., via bitmask), no runtime check
  is emitted:

  ```
  let low: u16 = (addr & 0xFFFF) as u16;  // provably safe
  ```

- if the compiler cannot prove it, a runtime check is inserted:

  ```
  let z: u8 = x as u8;  // runtime panic if x > 255
  ```

### 6.3 alternatives

| method         | behavior                              | contract? |
|----------------|---------------------------------------|-----------|
| `x as u8`      | narrowing cast with implicit contract | yes       |
| `x.truncate()` | intentional wrapping (x % 256)        | no        |
| `x.try_into()` | checked conversion, returns `Result`  | no        |

---

## appendix: contract expression well-formedness rules

1. contract expressions must evaluate to `bool`
2. contract expressions must be pure (no side effects, no mutation)
3. `result` is only valid inside `ensures`
4. `old(expr)` is only valid inside `ensures`
5. `forall` and `exists` are only valid inside contract clauses
6. `no_alias` is only valid inside `requires`
7. `borrows` is NOT a contract expression — it is a declaration annotation
8. contract expressions may call functions, but those functions must be pure
9. contract expressions may use pattern matching (for `Result`/`Option` destructuring)
10. contract expressions may use short-circuit logical operators (`&&`, `||`)
