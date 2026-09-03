# sv0 type system rules

formal specification of the sv0 type system. this document drives
the implementation of sv0c's type checker.

extracted from: sv0 compiler vision and design document

---

## 1. primitive types

### 1.1 integer types

| type   | width  | signed | range                                      |
|--------|--------|--------|--------------------------------------------|
| `i8`   | 8-bit  | yes    | -128 to 127                                |
| `i16`  | 16-bit | yes    | -32768 to 32767                            |
| `i32`  | 32-bit | yes    | -2^31 to 2^31 - 1                          |
| `i64`  | 64-bit | yes    | -2^63 to 2^63 - 1                          |
| `i128` | 128-bit| yes    | -2^127 to 2^127 - 1                        |
| `u8`   | 8-bit  | no     | 0 to 255                                   |
| `u16`  | 16-bit | no     | 0 to 65535                                 |
| `u32`  | 32-bit | no     | 0 to 2^32 - 1                              |
| `u64`  | 64-bit | no     | 0 to 2^64 - 1                              |
| `u128` | 128-bit| no     | 0 to 2^128 - 1                             |
| `usize`| ptr    | no     | platform pointer width                     |
| `isize`| ptr    | yes    | platform pointer width                     |

all integer types are `Copy`.

### 1.2 floating-point types

| type  | width  | precision          |
|-------|--------|--------------------|
| `f32` | 32-bit | IEEE 754 single    |
| `f64` | 64-bit | IEEE 754 double    |

floating-point types are `Copy`.

### 1.3 other primitive types

| type     | description                                |
|----------|--------------------------------------------|
| `bool`   | boolean: `true` or `false`. 1 byte.        |
| `char`   | unicode scalar value (UTF-32). 4 bytes.    |
| `byte`   | alias for `u8`. single byte.               |
| `string` | owned UTF-8 string. heap-allocated.        |

`bool`, `char`, and `byte` are `Copy`. `string` is NOT `Copy` (owns heap data).

#### 1.3.1 owned `string` runtime representation and backend ABI (normative)

This subsection is the accepted resolution of **sv0-strings SPEC OQ-001** and the
enablement gates **UP-001 / UP-002 / UP-003**. It is
*resolved-pending-implementation*: the representation below is normative now;
landing it is tracked as `sv0-toolchain` slices **SS-U02b** (C runtime),
**SS-U02c** (VM alignment), and **SS-U02d** (allocation failure + `Drop`).

**Layout.** An owned `string` value SHALL be a three-field record, in this field
order:

| field  | type            | meaning                                                |
|--------|-----------------|-------------------------------------------------------|
| `data` | non-null `*u8`  | address of content byte 0                              |
| `len`  | `usize`         | count of content bytes (**not** a NUL-terminated len) |
| `cap`  | `usize`         | allocated capacity in bytes; `cap >= len`             |

- `string` is not `Copy`; it owns `[data, data + cap)` and frees it on drop
  (RAII, `memory-model/ownership.md` §7.4).
- The content is exactly `len` bytes of well-formed UTF-8. **An embedded `\0`
  byte is content**, never a terminator; there is no implicit trailing `\0`.
- `data` is never null, even for the empty string — `len == 0` (with
  `cap == 0` permitted, no allocation required) uses a valid non-null base.
- C-style terminated interop goes through `CStr` / `CString`
  (`strings_cstr`), which validate and own their own terminator; a bare
  `string` never carries one.
- Both backends SHALL use this identical field set and order, so a `string`
  produced by any lowering path is ABI-compatible with every consumer.

**Length and comparison (UP-002).** `len_bytes`, complete equality, ordering,
concatenation, byte access, and substring SHALL be defined purely from `len` and
the byte range — never a `strlen` / `strcmp`-style scan that stops at `\0`. Two
`string`s are equal iff their `len` is equal and all `len` bytes are equal (so
`"a\0b"` differs from `"a"` and from `"a\0c"`).

**Access (UP-003).** Byte access and substring SHALL bounds-check
(`i < len`; `0 <= a <= b <= len`) **before** any memory access and produce the
*same* typed failure or contract violation on both backends. Substring yields an
owned copy (or a borrowed byte view where the API states so); it never fabricates
a misaligned or over-long `string`.

**Allocation failure and destruction.** Construction or growth that would exceed
an allocation limit, or that the allocator rejects, SHALL surface a typed failure
*before* the value is observable — there is no partially-initialised `string`. A
`len + other.len` overflow in concatenation is checked before allocation, leaving
the inputs unchanged. Drop releases `[data, data + cap)` exactly once on both
backends.

*OQ-003 disposition (SS-U02d).* In the current bootstrap runtime the "typed
failure" is realised as a **fail-closed abort** (`sv0_panic` on the C backend, a
raised runtime fault on the VM): the string value is never observable in a
partial state, but the failure is not yet a recoverable `Result`-returning
value — a recoverable allocator-failure API is deferred to a non-bootstrap
backend. Likewise, this runtime allocates `string` / `Vec<T>` / `Box<T>` buffers
arena-style and releases them at process exit; per-value `Drop`/RAII for `string`
is deferred with them (it is an unimplemented language feature, not a
string-specific gap). A deterministic **allocation-accounting + fault-injection**
hook (`SV0_STR_FAIL_AT` on the C backend) makes the fail-closed path testable
without exhausting memory. See `UP-007 / UP-013` and sv0-strings SPEC OQ-003.

**VM.** `sv0vm` string-table representation and string builtins SHALL align to
these length semantics; an out-of-range access is fail-closed with the C
backend's fault class, never a truncated or wrapped result.

### 1.4 widening and narrowing casts

**widening casts** (smaller to larger type of same signedness) are always safe
and insert no runtime checks:

```
let x: u32 = 42;
let y: u64 = x as u64;    // always safe
```

**narrowing casts** (larger to smaller type) implicitly insert a contract:

```
let x: u32 = 42;
let z: u8 = x as u8;      // implicit requires(x <= 255)
```

the compiler proves the cast is safe or inserts a runtime check:

- if the compiler can prove the value fits (e.g., via bitmask), no check is emitted
- otherwise, a runtime check panics if the value overflows

**alternatives to narrowing casts:**

- `.truncate()` — intentional wrapping, no contract, no check. `x.truncate()` yields `x % 256` for u8.
- `.try_into()` — checked conversion returning `Result`. returns `Err` if the value doesn't fit.

**signedness casts** follow the same rules: `i32 as u32` requires the value is non-negative.

---

## 2. composite types

### 2.1 arrays

`[T; N]` — fixed-size, stack-allocated array of `N` elements of type `T`.

- `N` must be a compile-time constant expression
- `T` must be `Copy` for array repeat initialization `[val; N]`
- arrays are `Copy` when `T` is `Copy`
- index access `arr[i]` desugars to the `Index` trait and is bounds-checked

### 2.2 slices

`&[T]` — borrowed view into contiguous memory (array, Vec, or another slice).

- slices are always references; there is no owned slice type
- `&[T]` is a fat pointer: (data pointer, length)
- `&mut [T]` allows mutation of elements

#### 2.2.1 runtime representation and backend ABI (normative)

This subsection is the accepted resolution of **sv0-strings SPEC OQ-002** and
the enablement gates **UP-004 / UP-005**. It is *resolved-pending-implementation*:
the representation below is normative now; landing it on both backends is tracked
as `sv0-toolchain` slices **SS-U03b** (C), **SS-U03c** (VM `IndexAccess`), and
**SS-U03d** (borrow compile-fail suite).

**Layout.** A slice value of type `&[T]` or `&mut [T]` SHALL be a two-field
record, in this field order:

| field  | type          | meaning                                        |
|--------|---------------|-----------------------------------------------|
| `data` | non-null `*T` | address of element 0 of the viewed range      |
| `len`  | `usize`       | element count of the view (not a byte count)  |

- The record is passed and returned **by value** (two machine words). As `&[T]`
  it is `Copy`; as `&mut [T]` it follows the move / exclusivity rules.
- `data` SHALL address valid, contiguously allocated storage for `len` values of
  `T` for the whole lifetime of the view, and is never null — even when
  `len == 0`, `data` is a valid non-null base (the backing container's base or a
  well-known non-null sentinel).
- `T` has the same layout it has inside an array / `Vec<T>`; slicing performs no
  copy and no reallocation.
- Both backends SHALL use this identical layout and field order, so a slice
  produced by any lowering path is ABI-compatible with every consumer
  (`T-SLICE-ABI-001`).

**Construction.** `&arr[..]`, `&v[a..b]`, `&s[a..b]` (and the `mut` forms)
compute `data = base + a`, `len = b - a`. A range with `a > b`, or `b` past the
source length, SHALL be a checked failure at the slicing site (contract
violation / typed error), never an out-of-range `data` / `len` pair.

**Access.** `sl[i]` (read or write) SHALL bounds-check `i < len` **before** any
memory access and produce the *same* typed failure or contract violation on both
backends (`UP-003` parity). `sl.len()` returns the `len` field. Unchecked
indexing exists only under `unsafe` on a raw pointer (`memory-model` §8.4).

**Borrow rules through lowering.** The exclusivity rule
(`memory-model/ownership.md` §3.3) is enforced on the *source* before lowering;
the lowered `{data,len}` record carries no runtime borrow state, so lowering and
code generation SHALL NOT create a view that outlives the borrow it came from:

- returning a `&[T]` / `&mut [T]` backed by a function local is rejected at
  compile time (dangling view) on both project backends;
- a `&mut [T]` view SHALL NOT coexist with any other live view of the same
  region; violations are a stable diagnostic class (`SS-U03d`).

**Interval overlap.** Whether two slice views overlap is a question about the
`[data, data + len)` ranges, not pointer identity; a contract that needs
non-overlap uses the interval predicate (`memory-model/ownership.md` §6.1,
enablement `UP-006`), not `data_a != data_b`.

**VM.** `sv0vm` SHALL accept `IndexAccess` on a slice operand of this layout
(currently rejected), with the same bounds-check-before-access semantics; see
`bytecode/instructions.md`.

**String / byte-slice bridges (`SS-U16`).** Two compiler-only builtins bridge
an owned `string` (a length-bearing `sv0_str` handle, §1.3.1) and a `&[byte]`
view, for the `sv0-strings` `strings_text::from_utf8` / `as_bytes` surface:

| Name | Type (surface) | Semantics |
|------|----------------|-----------|
| `string_from_bytes` | `(v: &[byte]) -> string` | New owned `string` **copied** from `v`'s bytes (each element narrowed to its low 8 bits). Exactly one owned-string allocation, fault-injectable via `SV0_STR_FAIL_AT` (`SS-U02d`); on failure it fails closed with `sv0_panic` and `v` is untouched. Embedded `0x00` is preserved. |
| `string_byte_view` | `(s: string) -> &[byte]` | A read-only `&[byte]` view of the complete storage of `s`, embedded `0x00` included. Because `string` values are immutable and the view's backing store is arena-lived, the view can neither dangle nor observe a later change; a backend MAY materialise it. |

Both lower to IR builtin ids `35` / `36` (`sv0_str_from_byte_slice` /
`sv0_str_byte_view` in the C runtime; `CALL_BUILTIN 35` / `36` in `sv0vm`).

### 2.3 tuples

`(T1, T2, ..., Tn)` — heterogeneous, fixed-size, ordered collection.

- `()` is the unit type (zero elements)
- access via `.0`, `.1`, etc.
- tuples are `Copy` when all element types are `Copy`
- tuples can be destructured in `let` bindings and `match` patterns

### 2.4 structs (product types)

named, heterogeneous product types with named fields.

```
struct Complex {
    re: f64,
    im: f64,
}
```

- fields are private by default; `pub` makes them accessible outside the module
- structs are `Copy` when all fields are `Copy` (auto-derived)
- structs can have `borrows(field)` annotations for reference-holding structs

### 2.5 enums (sum types / tagged unions)

```
enum CryptoError {
    InvalidKeyLength { expected: u32, got: u32 },
    InvalidNonce,
    AuthenticationFailed,
    BufferTooSmall { needed: usize },
}
```

- variants may be unit, tuple, or struct variants
- enums are `Copy` when all variant payloads are `Copy`
- pattern matching on enums must be exhaustive

### 2.6 Option\<T\> and Result\<T, E\>

`Option<T>` represents an optional value:

| variant   | meaning          |
|-----------|------------------|
| `Some(T)` | value is present |
| `None`    | value is absent  |

`Result<T, E>` represents a failable computation:

| variant  | meaning          |
|----------|------------------|
| `Ok(T)`  | success          |
| `Err(E)` | failure          |

both are enums defined in `core::option` and `core::result`. the `?` operator
works with both types for early error propagation.

### 2.7 type aliases

```
type AesKey = [u8; 32];
```

type aliases are transparent — fully interchangeable with the underlying type.
no new type is created; `AesKey` and `[u8; 32]` are the same type.

### 2.8 refined types

```
type PositiveInt = i32 where self > 0;
type BoundedBuffer<N: usize> = Vec<u8> where self.len() <= N;
```

refined types are type aliases with compile-time-checked constraints. the
compiler verifies the refinement predicate at every assignment. refinement
predicates must be expressible as contract expressions. the predicate refers to
the refined value as `self`.

availability: refinement types require phase 2+ verification (SMT solver).

status (M4): the `where <predicate>` syntax **parses** (the predicate is stored on
the type-alias item as a contract expression; M4-S-030) and `sv0 verify`
**checks** it at each `let p: T = e` binding (M4-S-031): the obligation
`predicate[self := e]` is discharged by the same z3 machinery as `ensures`,
proven from the enclosing function's `requires`.

### 2.9 newtypes

```
newtype Key([u8; 32]);
newtype Nonce12([u8; 12]);
```

newtypes create a DISTINCT type that wraps the underlying type. unlike type aliases,
newtypes are NOT interchangeable — `Key` and `[u8; 32]` are different types.
this prevents accidental misuse (e.g., passing a key where a nonce is expected).

newtypes have no runtime overhead — the wrapper is erased at compile time.

---

## 3. reference types

### 3.1 shared references: `&T`

- read-only access to the referent
- multiple `&T` to the same value may coexist
- the referent must outlive all shared references

### 3.2 exclusive references: `&mut T`

- read-write access to the referent
- at most one `&mut T` may exist at a time
- no `&T` may coexist with an `&mut T` to the same value
- the referent must outlive the exclusive reference

### 3.3 raw pointers

| type         | description             |
|--------------|-------------------------|
| `*const T`   | immutable raw pointer   |
| `*mut T`     | mutable raw pointer     |

- creating raw pointers is safe; dereferencing requires `unsafe`
- raw pointers do not participate in borrow checking
- exist for: kernel/hardware access, FFI, data structures the borrow checker can't express

### 3.4 function pointers

`fn(A, B) -> C` — pointer to a function with the given signature.

- function pointers are `Copy`, `Send`, and `Sync`
- closures that capture no environment are coercible to function pointers
- casting a function pointer to an integer requires `unsafe`

---

## 4. type inference

### 4.1 local variable inference

local bindings infer their type from the initializer expression:

```
let x = 42;           // inferred as i32 (default integer type)
let y = 3.14;         // inferred as f64 (default float type)
let z = x * 2;        // inferred as i32
let s = "hello";      // inferred as &string (string literal)
```

the type annotation is optional on `let` bindings when the initializer provides
enough information. the annotation is required when the type cannot be inferred
(e.g., `let v: Vec<i32> = Vec::new()`).

### 4.2 closure parameter inference

closure parameter types are inferred when the closure is passed to a function
with a known signature:

```
let doubled = numbers.map((x) => x * 2);
// x is inferred as the element type of numbers
```

when used standalone (not in a context that constrains the type), closure parameter
types must be annotated:

```
let add = (x: i32, y: i32) => x + y;
```

### 4.3 function boundary rule

types are EXPLICIT at function boundaries — function parameters and return types
must be annotated. there is no inference across function signatures. this ensures
that each function's type is readable without analyzing its body.

```
fn add(a: i32, b: i32) -> i32 { a + b }   // explicit types required
```

### 4.4 integer and float literal defaults

- unsuffixed integer literals default to `i32`
- unsuffixed float literals default to `f64`
- a suffix overrides the default: `42u64`, `3.14f32`

---

## 5. generics

### 5.1 type parameters

generic functions and types accept type parameters with optional trait bounds:

```
fn find<T: Eq>(haystack: &[T], needle: &T) -> Option<usize>
```

`T: Eq` constrains `T` to types that implement the `Eq` trait. multiple bounds
use `+` syntax: `T: Eq + Clone`.

### 5.2 where clauses

for complex bounds, `where` clauses provide an alternative syntax:

```
fn complex_fn<T, U>(a: T, b: U) -> T
    where T: Add<U, Output = T> + Clone,
          U: Into<T>
```

`where` clauses are preferred when bounds are long or involve associated types.

### 5.3 associated types

traits can declare associated types:

```
trait Iterator {
    type Item;
    fn next(self: &mut Self) -> Option<Self::Item>;
}

trait Add<Rhs> {
    type Output;
    fn add(self: Self, rhs: Rhs) -> Self::Output;
}
```

implementors define the associated type:

```
impl Add for Complex {
    type Output = Complex;
    fn add(self: Self, rhs: Complex) -> Complex { ... }
}
```

### 5.4 generic associated types (GATs)

associated types can themselves have type parameters:

```
trait Container {
    type Item<T>;
    fn wrap<T>(value: T) -> Self::Item<T>;
    fn unwrap<T>(item: Self::Item<T>) -> T;
}
```

implementors define the generic associated type with concrete type constructors:

```
impl Container for BoxContainer {
    type Item<T> = Box<T>;
    fn wrap<T>(value: T) -> Box<T> { Box::new(value) }
    fn unwrap<T>(item: Box<T>) -> T { *item }
}
```

GATs enable higher-kinded patterns — traits that abstract over type constructors
rather than concrete types. they are available from milestone 1 for type-level
expressiveness but are an advanced feature.

### 5.5 const generics

generic parameters whose bound is a concrete primitive type (not a trait) are
const generic parameters — they accept compile-time values instead of types.

```
struct FixedBuffer<T, N: usize> {
    data: [T; N],
    len: usize,
}

fn zeroed_array<N: usize>() -> [u8; N] {
    [0; N]
}
```

the parser treats type params and const params uniformly (`identifier : bound`).
the type checker distinguishes them: if the bound names a trait, it's a type
param; if it names a concrete primitive type, it's a const param.

**allowed const param types:** `usize`, `isize`, `u8`–`u128`, `i8`–`i128`, `bool`.

**const arguments at instantiation:**

| form                          | example                          |
|-------------------------------|----------------------------------|
| integer literal               | `FixedBuffer<u8, 32>`            |
| const identifier              | `FixedBuffer<u8, MAX_SIZE>`      |
| const expression block        | `FixedBuffer<u8, {N + 1}>`       |

const expression blocks use `{ expr }` for compound expressions. the expression
must be evaluable at compile time.

**const params in type positions:**

const params can be used wherever a compile-time value is needed:

- array sizes: `[T; N]`
- repeat initialization: `[0; N]`
- contract expressions: `requires(N > 0)`
- other const params: `FixedBuffer<T, {N * 2}>`

**interaction with refined types:**

```
type BoundedBuffer<N: usize> = Vec<u8> where self.len() <= N;
```

the const param `N` is available in the refinement predicate.

### 5.6 monomorphization

generics are implemented via monomorphization — the compiler generates a
specialized copy of each generic function or type for each concrete type
argument used. this produces efficient code (no runtime dispatch) at the cost
of binary size.

**bootstrap milestone note:** for milestone 3 self-host work, the **full**
lowering-side duplication story (**T0-2d** / **M3-S-054**) is **explicitly
deferred** until a future slice — checker instantiation (**§5** surfaces +
unification) is required for accepted programs; see
[`compiler/bootstrap-generics-policy.md`](../compiler/bootstrap-generics-policy.md).

---

## 6. trait system

### 6.1 trait definition

traits define an interface — a set of methods that implementing types must provide.
trait methods can carry contracts:

```
trait Serialize {
    fn serialize(self: &Self) -> Vec<u8>
        ensures(result.len() > 0);

    fn deserialize(data: &[u8]) -> Result<Self, Error>
        requires(data.len() > 0);
}
```

### 6.2 trait implementation

`impl Trait for Type` implements a trait for a type. the implementation must
provide all required methods with compatible signatures.

**contract interaction with traits:**

- impl must satisfy all trait contracts
- impl can strengthen contracts (add more guarantees)
- contravariance: impl `requires` can be WEAKER (accept more inputs), impl `ensures` can be STRONGER (guarantee more)
- this follows the Liskov Substitution Principle

```
impl Serialize for KeyPair {
    fn serialize(self: &Self) -> Vec<u8>
        ensures(result.len() == 96)    // stronger than trait's > 0
    { ... }
}
```

### 6.3 inherent impl blocks

`impl Type` (without a trait) attaches methods directly to a type. a type can
have multiple inherent impl blocks.

methods use `self` to determine the receiver:

| self parameter   | meaning                  | ownership after call              |
|------------------|--------------------------|-----------------------------------|
| `self: &Self`    | shared borrow            | caller retains ownership          |
| `self: &mut Self`| exclusive borrow         | caller retains ownership          |
| `self: Self`     | by value                 | caller's value is moved/consumed  |

functions without `self` are associated functions (called via `Type::name()`).

### 6.4 trait resolution

when a method is called on a value, the compiler resolves which trait
implementation to use:

1. check inherent impl blocks for the concrete type
2. check trait implementations in scope
3. if multiple traits provide a method with the same name, the call is ambiguous — use qualified syntax: `Trait::method(value)`

### 6.5 impl coherence (orphan rules)

to prevent conflicting implementations:

- a trait can only be implemented for a type if either the trait or the type
  is defined in the current project
- at most one implementation of a trait exists for any given type
- the compiler rejects duplicate or conflicting implementations

### 6.6 operator trait desugaring

operators desugar to trait method calls:

| expression | desugars to           | trait         |
|------------|-----------------------|---------------|
| `a + b`    | `Add::add(a, b)`     | `core::ops::Add`   |
| `a - b`    | `Sub::sub(a, b)`     | `core::ops::Sub`   |
| `a * b`    | `Mul::mul(a, b)`     | `core::ops::Mul`   |
| `a / b`    | `Div::div(a, b)`     | `core::ops::Div`   |
| `a % b`    | `Rem::rem(a, b)`     | `core::ops::Rem`   |
| `-a`       | `Neg::neg(a)`        | `core::ops::Neg`   |
| `a == b`   | `Eq::eq(&a, &b)`     | `core::ops::Eq`    |
| `a < b`    | `Ord::lt(&a, &b)`    | `core::ops::Ord`   |
| `a[i]`     | `Index::index(&a, i)`| `core::ops::Index`  |
| `a[i] = v` | `IndexMut::index_mut(&mut a, i)` | `core::ops::IndexMut` |
| `*a`       | `Deref::deref(&a)`   | `core::ops::Deref` |

### 6.7 formatting traits

`Display` and `Debug` control string formatting in `println`, `print`, and `format!`.
they are defined in `core::fmt`.

**milestone 1 definitions (string-returning form):**

```
trait Display {
    fn to_display(self: &Self) -> string;
}

trait Debug {
    fn to_debug(self: &Self) -> string;
}
```

- `Display` controls `{}` placeholders — user-facing, readable output
- `Debug` controls `{:?}` placeholders — developer-facing, structural output
- `println("value: {}", x)` calls `Display::to_display(&x)` for each `{}`
- `println("debug: {:?}", x)` calls `Debug::to_debug(&x)` for each `{:?}`
- the compiler type-checks format placeholders against arguments at compile time

**planned migration (post-bootstrap):**

when the standard library matures, these traits will migrate to a Formatter-based
approach that writes into a buffer instead of allocating intermediate strings:

```
trait Display {
    fn fmt(self: &Self, f: &mut Formatter) -> Result<(), FmtError>;
}
```

the trait names and format string syntax remain the same; only the method
signatures change.

**standard implementations:**

all primitive types implement both `Display` and `Debug`:

| type     | `Display` output            | `Debug` output                 |
|----------|-----------------------------|--------------------------------|
| integers | decimal: `42`               | decimal: `42`                  |
| floats   | decimal: `3.14`             | full precision: `3.14000000`   |
| `bool`   | `true` / `false`            | `true` / `false`               |
| `char`   | the character: `a`          | quoted: `'a'`                  |
| `string` | the content: `hello`        | quoted: `"hello"`              |
| arrays   | not implemented             | `[1, 2, 3]`                   |
| tuples   | not implemented             | `(1, true)`                    |

- enums and structs do NOT auto-implement `Display` (the programmer defines user-facing formatting)
- `Debug` can be auto-derived via `#[derive(Debug)]` (milestone 4+ when the derive macro system is available)
- until `#[derive(Debug)]` is available, programmers implement `Debug` manually

---

## 7. function overloading

sv0 supports function overloading — multiple functions with the same name but
different parameter types.

### 7.1 resolution rules

1. the compiler examines the types of all arguments at the call site
2. it selects the overload whose parameter types exactly match
3. if no exact match exists, implicit widening conversions are NOT applied — the call is rejected
4. if multiple overloads match, the compiler reports an ambiguity error

### 7.2 interaction with generics

- generic functions participate in overload resolution
- a concrete overload is preferred over a generic one when both match
- overload resolution happens BEFORE generic instantiation

### 7.3 interaction with contracts

- overload resolution is independent of contracts
- contracts are checked AFTER the overload is resolved
- each overload may have different contracts

---

## 8. auto-derivation rules

### 8.1 Copy

a type is automatically `Copy` when ALL of its fields are `Copy`:

| type category           | Copy?                                    |
|------------------------|------------------------------------------|
| integer types          | yes (always)                             |
| float types            | yes (always)                             |
| `bool`, `char`, `byte` | yes (always)                             |
| `string`               | NO (owns heap data)                      |
| arrays `[T; N]`        | yes, when `T` is `Copy`                 |
| tuples `(T1, T2, ...)` | yes, when all `Ti` are `Copy`           |
| structs                | yes, when all fields are `Copy`          |
| enums                  | yes, when all variant payloads are `Copy`|
| `Vec<T>`, `Box<T>`     | NO (own heap data)                       |
| references `&T`        | yes (always)                             |
| `&mut T`               | NO (exclusivity prevents copying)        |

the programmer may also write `impl Copy for T {}` to make intent explicit.
the compiler still verifies all fields are `Copy`.

a type with a `Drop` implementation CANNOT be `Copy`.

### 8.2 Clone

`Copy` implies `Clone` — every `Copy` type is automatically `Clone`.
`Clone` provides `.clone()` for explicit duplication.

types that are NOT `Copy` can still implement `Clone` for explicit, potentially
expensive duplication (e.g., `Vec<T>` clones by allocating a new buffer and
copying all elements).

### 8.3 Send

a type is automatically `Send` when ALL of its fields are `Send`.

- most types are `Send`
- raw pointers (`*const T`, `*mut T`) are NOT `Send`
- types with thread-affine invariants use negative impls: `impl !Send for GpuBuffer {}`

### 8.4 Sync

a type is automatically `Sync` when ALL of its fields are `Sync`.

a type is `Sync` if and only if `&T` is `Send` (concurrent reads are safe).

- most immutable types are `Sync`
- `&mut T` is NOT `Sync`
- types with interior mutability may not be `Sync`
- negative impls: `impl !Sync for UnsafeCell<T> {}`

---

## 9. Drop trait and destructor semantics

### 9.1 the Drop trait

`Drop` customizes what happens when a value goes out of scope. it is defined
in `core::ops`:

```
trait Drop {
    fn drop(self: &mut Self);
}
```

`drop` receives `&mut Self` — it can clean up resources but does not deallocate
the value itself. deallocation happens automatically after `drop` returns.

### 9.2 implicit drop

the compiler inserts drop calls automatically when an owner goes out of scope.
the programmer never calls `drop()` directly on a value — this prevents
double-drop bugs.

to drop a value early (before end of scope), use `std::mem::drop(value)`:

```
let file = fs::open("data.txt");
// ... use file ...
std::mem::drop(file);       // file is dropped here (moved into drop, then goes out of scope)
// file is no longer valid
```

`std::mem::drop` is a regular function that takes ownership of its argument
and does nothing — the value is dropped when the function returns.

### 9.3 field destruction order

when a struct or enum is dropped, fields are destroyed in **reverse declaration
order** — the last field declared is dropped first.

```
struct Connection {
    logger: Logger,         // dropped third (last)
    buffer: Vec<u8>,        // dropped second
    socket: TcpStream,      // dropped first
}
```

this mirrors stack unwinding semantics: resources acquired later are released
first. it matters when one field's destructor depends on another field still
being valid (e.g., flushing a buffer before closing a socket).

for enums, only the active variant's payload is dropped.

### 9.4 drop order for local variables

local variables in a scope are dropped in **reverse declaration order**:

```
{
    let a = resource_a();   // dropped third (last)
    let b = resource_b();   // dropped second
    let c = resource_c();   // dropped first
}
```

### 9.5 Drop and Copy are mutually exclusive

a type that implements `Drop` cannot be `Copy`. this prevents double-drop:
if a value were bitwise-copied and both copies went out of scope, the
destructor would run twice.

the compiler rejects `impl Copy for T` when `T` implements `Drop`.

### 9.6 partial moves

if a field is moved out of a struct, the struct is in a partially-moved state:

- the moved field is NOT dropped (the new owner is responsible)
- the remaining fields are dropped individually when the struct goes out of scope
- the struct as a whole cannot be used after a partial move

```
struct Pair {
    left: Vec<i32>,
    right: Vec<i32>,
}

let p = Pair { left: vec![1], right: vec![2] };
let taken = p.left;        // left is moved out
// p.right is still valid and will be dropped at end of scope
// p.left is owned by taken
// p as a whole cannot be used
```

the compiler tracks partial moves at the field level within function bodies
(tier 1 borrow tracking).

---

## 10. block statements: implicit separator and `if` without `else`

this section aligns the formal spec with **sv0c** (bootstrap compiler) behavior
for control flow written as **statements** inside `{ ... }`.

### 10.1 implicit statement boundary after braced control flow

inside a **block expression** `block_expr`, a **statement** may be either:

- a traditional **expression statement** `expr_stmt` — `expr` followed by **`;`**, or
- a **braced control-flow expression** (`if` / `while` / `for` / `loop` / `match`,
  or a nested **`{ ... }` block expression**) **without** a trailing **`;`**
  when immediately followed by another **statement** or by the **closing `}`**
  of the enclosing block (tail expression position).

other expression forms (calls, arithmetic, paths, etc.) still require an explicit
**`;`** before the next statement. see **`grammar/sv0.ebnf`** (`braced_ctrl_stmt`).

### 10.2 typing: `if` without `else`

for **`if cond then_block`** with **no** `else` branch:

- **`cond`** must have type **`bool`**.
- the whole **`if`** expression has type **`unit`**.
- **`then_block`** is normally checked as **`unit`**. if **`then_block`** is a
  block whose **last statement** is **`return ...`**, the block is treated as
  **diverging** (early exit from the enclosing function): the **`return`**
  value is checked against the **enclosing function’s return type**, and the
  **`if`** is still **`unit`** in the surrounding block.

if **`then_block`** ends with a **non-`unit` tail expression** (e.g. `{ 1 }` with
no `else`), that is a **type error** in this slice — the **`unit`** expectation
is not satisfied.

---

## appendix: type checking algorithm summary

the sv0c type checker operates in a single pass over the resolved AST:

1. **collect** — gather all type, trait, and impl definitions into a type environment
2. **check items** — for each function, struct, enum, trait, and impl:
   a. synthesize types for expressions bottom-up (type synthesis)
   b. check expressions against expected types top-down (type checking)
   c. resolve method calls and operator desugaring
   d. verify trait bound satisfaction
   e. check generic constraints
   f. validate contract expressions (must be boolean-typed)
3. **verify coherence** — check for duplicate or conflicting trait implementations
4. **verify exhaustiveness** — check all match expressions cover all possible values

errors are reported with source locations and suggestions. the type checker
continues after errors to report multiple issues in a single run.
