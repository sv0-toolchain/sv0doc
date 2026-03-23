# sv0 memory model specification

formal specification of sv0's memory model. the memory model is central to sv0's
safety guarantees and drives the borrow checker implementation in sv0c.

extracted from: sv0 compiler vision and design document

---

## 1. ownership

### 1.1 single owner rule

every value has exactly one owner at any point in time. the owner is the binding
(variable) that holds the value.

### 1.2 move semantics

assignment transfers ownership. the source binding is invalidated after a move.

```
let data = vec![1, 2, 3];
let owned = data;           // data moves to owned
// data is no longer valid here -- compile error to use it
```

after `let owned = data`, the binding `data` is in a *moved-from* state. any
subsequent use of `data` is a compile error. this is enforced by the compiler's
local move/borrow analysis (tier 1).

### 1.3 scope-based deallocation (RAII)

when an owner goes out of scope, the value is dropped (destructors run, memory
is freed). this is Resource Acquisition Is Initialization (RAII).

```
{
    let buffer = Vec::new();
    // ... use buffer ...
}   // buffer is dropped here -- memory freed
```

there is no garbage collector. deallocation is deterministic and predictable.

### 1.4 function arguments

passing a value to a function transfers ownership (moves) unless the value is
`Copy`. the function becomes the new owner.

```
fn consume(v: Vec<i32>) { ... }

let data = vec![1, 2, 3];
consume(data);              // data moves into consume
// data is no longer valid here
```

to avoid transferring ownership, pass a reference (`&data` or `&mut data`).

---

## 2. Copy and Clone

### 2.1 Copy trait

a type is `Copy` if assignment duplicates the value (bitwise copy) instead of
moving it. `Copy` types are cheap to duplicate and do not own heap resources.

**auto-derivation:** the compiler auto-derives `Copy` for any struct or enum
whose fields are all `Copy`. no annotation is required.

```
// automatically Copy -- all fields are f64 (which is Copy)
struct Complex {
    re: f64,
    im: f64,
}

let a = Complex { re: 1.0, im: 2.0 };
let b = a;          // a is copied, both a and b are valid
```

**explicit Copy:** the programmer can write `impl Copy for T {}` to document
intent. this is equivalent to auto-derivation — the compiler still verifies all
fields are `Copy`.

```
impl Copy for Complex {}
impl Clone for Complex {
    fn clone(self: &Self) -> Self { *self }
}
```

### 2.2 types that cannot be Copy

types that own heap resources are NEVER `Copy`:

- `Vec<T>` — owns a heap-allocated buffer
- `Box<T>` — owns a heap-allocated value
- `string` — owns a heap-allocated UTF-8 buffer

assignment of these types always moves. `impl Copy for Vec<T>` is a compile error.

### 2.3 Copy and Drop are mutually exclusive

a type with a `Drop` implementation cannot be `Copy`. this prevents double-free:
if a value were copied and both copies went out of scope, the destructor would
run twice.

### 2.4 Clone trait

`Clone` provides `.clone()` for explicit duplication. every `Copy` type is
automatically `Clone` (`Copy` implies `Clone`).

types that are not `Copy` can implement `Clone` for explicit, potentially
expensive duplication:

```
let v1 = vec![1, 2, 3];
let v2 = v1.clone();       // allocates a new buffer, copies elements
// both v1 and v2 are valid
```

### 2.5 Copy summary

| type category          | Copy? | reason                                    |
|------------------------|-------|-------------------------------------------|
| integer types          | yes   | primitive, fixed-size                     |
| float types            | yes   | primitive, fixed-size                     |
| `bool`, `char`, `byte` | yes   | primitive, fixed-size                     |
| `&T`                   | yes   | pointers are cheap to copy                |
| `&mut T`               | NO    | exclusivity prevents copying              |
| arrays `[T; N]`        | yes*  | when `T` is `Copy`                       |
| tuples                 | yes*  | when all elements are `Copy`              |
| structs                | yes*  | when all fields are `Copy`                |
| enums                  | yes*  | when all variant payloads are `Copy`      |
| `string`, `Vec<T>`     | NO    | own heap resources                        |
| `Box<T>`               | NO    | owns heap resource                        |
| types with `Drop`      | NO    | Copy and Drop are mutually exclusive      |

\* auto-derived

---

## 3. references and the exclusivity rule

### 3.1 shared references: `&T`

`&T` borrows a value for read-only access. multiple shared references to the
same value may coexist.

```
let data = vec![1, 2, 3];
let a = &data;
let b = &data;
println(a);     // ok
println(b);     // ok
```

### 3.2 exclusive references: `&mut T`

`&mut T` borrows a value for read-write access. at most one exclusive reference
may exist at a time, and no shared references may coexist with it.

```
let mut data = vec![1, 2, 3];
let c = &mut data;
c.push(4);      // ok: exclusive access
```

### 3.3 the exclusivity rule

at any point in time, a value may have EITHER:

- **one `&mut T`** (exclusive, mutable access), OR
- **any number of `&T`** (shared, read-only access)

NEVER both simultaneously. this rule prevents data races and iterator
invalidation at compile time.

```
let mut data = vec![1, 2, 3];
let a = &data;          // shared borrow
let c = &mut data;      // COMPILE ERROR: cannot borrow as mutable
                        // while shared borrow exists
```

### 3.4 auto-dereferencing

the compiler auto-dereferences when calling methods. `v.len()` works even though
`len` takes `&self` — the compiler inserts the necessary `&` or `*` operations.

explicit `*` is needed for:

- assigning through a mutable reference: `*m = 20`
- copying a value out of a reference: `let val = *r`

---

## 4. borrow tracking tiers

sv0 uses a three-tier system for tracking borrows. each tier handles increasingly
complex cases with increasing programmer involvement.

### 4.1 tier 1: automatic local borrow tracking

within a function body, the compiler tracks every borrow and move automatically.
no annotations are needed.

**capabilities:**

- tracks when a value is borrowed, moved, or dropped
- detects use-after-move
- detects conflicting borrows (shared + exclusive)
- detects dangling references (reference outlives referent)

```
fn process() {
    let data = vec![1, 2, 3];
    let r = &data;          // r borrows data
    println(r);             // ok: data is still alive
    let owned = data;       // data moves to owned; r is now invalid
    // println(r);          // COMPILE ERROR: r borrows invalidated data
}
```

**implementation:** flow-sensitive liveness analysis within function bodies.
each borrow is tracked from creation to last use. the compiler detects conflicts
between overlapping borrow regions.

### 4.2 tier 2: elision rules at function boundaries

for function signatures that return references, simple rules automatically
determine which input the output borrows from:

**rule 1:** if there is exactly one input reference, the output reference borrows
from it.

```
fn first_word(s: &string) -> &string {
    // compiler knows result borrows from s
    ...
}
```

**rule 2:** if one of the inputs is `&self` or `&mut self`, the output borrows
from `self`.

```
fn name(self: &User) -> &string {
    &self.name
}
```

**rule 3:** otherwise, the programmer must annotate with a `borrows` contract
(tier 3).

**special case:** if the function returns an owned value (not a reference), no
borrow relationship exists — no annotation is needed regardless of inputs.

```
fn to_uppercase(s: &string) -> string {
    // returns owned string, no borrow relationship
    ...
}
```

### 4.3 tier 3: explicit borrows contracts

when the elision rules don't apply (multiple input references, ambiguous borrow
source), the programmer writes a `borrows` clause.

`borrows(x, y)` means: the returned reference must not outlive `x` or `y`. the
caller must keep both alive as long as the result is used.

```
fn longest(x: &string, y: &string) -> &string
    borrows(x, y)
{
    if x.len() > y.len() { x } else { y }
}
```

this is semantically equivalent to Rust's lifetime parameters:

- sv0: `fn longest(x: &string, y: &string) -> &string borrows(x, y)`
- Rust: `fn longest<'a>(x: &'a str, y: &'a str) -> &'a str`

**single-source borrow:**

```
fn select(cond: bool, a: &[u8], b: &[u8]) -> &[u8]
    borrows(a)
{
    if cond { a } else { panic("condition was false") }
}
```

`borrows(a)` means the result borrows only from `a` — the caller only needs to
keep `a` alive.

---

## 5. structs holding references

structs that hold references use `borrows` on the struct declaration to indicate
which fields contain borrowed data:

```
struct Parser borrows(input) {
    input: &string,
    position: usize,
}
```

`borrows(input)` means the `Parser` struct cannot outlive the data that `input`
references.

constructing a struct with references creates a borrow relationship:

```
fn make_parser(source: &string) -> Parser
    borrows(source)
{
    Parser { input: source, position: 0 }
}
// Parser cannot outlive the string it borrows from
```

this replaces Rust's lifetime parameters on structs:

- sv0: `struct Parser borrows(input) { input: &string, ... }`
- Rust: `struct Parser<'a> { input: &'a str, ... }`

---

## 6. memory contracts

the contract system can express memory properties beyond what the type system
captures:

### 6.1 no_alias(a, b)

asserts that two references do not alias (point to disjoint memory):

```
fn swap(a: &mut u8, b: &mut u8) -> ()
    requires(no_alias(a, b))
    ensures(*a == old(*b) && *b == old(*a))
{ ... }
```

### 6.2 old(expr) for pre-state comparison

captures the pre-mutation state of expressions for postcondition comparison:

```
fn fill_random(buf: &mut [u8]) -> ()
    ensures(buf.len() == old(buf.len()))
{ ... }
```

### 6.3 borrows for borrow-source declaration

declares which inputs the output is tied to, replacing lifetime parameters:

```
fn longest(x: &string, y: &string) -> &string
    borrows(x, y)
{ ... }
```

### 6.4 verification phases

memory contracts follow the same phased verification as all other contracts:

| phase   | behavior                                               |
|---------|--------------------------------------------------------|
| phase 1 | `no_alias` checked at runtime via pointer comparison   |
| phase 1 | `old()` values captured in temporaries at function entry|
| phase 2 | SMT solver reasons about aliasing statically           |
| phase 3 | cross-function borrow analysis, modular proofs         |

---

## 7. allocation

### 7.1 stack allocation

fixed-size types are stack-allocated by default:

```
let key: [u8; 32] = generate_key();   // 32 bytes on the stack
let x: i32 = 42;                       // 4 bytes on the stack
```

### 7.2 heap allocation: Box\<T\>

`Box<T>` allocates a value on the heap. the box owns the allocation and frees
it when dropped (RAII).

```
let buffer: Box<[u8]> = Box::new([0u8; 4096]);
// buffer freed when it goes out of scope
```

### 7.3 heap-backed collections

`Vec<T>` and `string` manage heap-allocated buffers that grow dynamically.
they own their buffers and free them on drop.

```
let mut v: Vec<i32> = Vec::new();
v.push(1);
v.push(2);
// v freed when it goes out of scope -- buffer deallocated
```

### 7.4 RAII (Resource Acquisition Is Initialization)

destructors run when the owner goes out of scope. this applies to:

- `Box<T>` — frees the heap allocation
- `Vec<T>` — frees the buffer
- `string` — frees the UTF-8 buffer
- `Mutex` guards — releases the lock
- file handles — closes the file

the `Drop` trait customizes destruction behavior:

```
trait Drop {
    fn drop(self: &mut Self);
}
```

`drop` receives `&mut Self` — it cleans up resources but does not deallocate
the value itself (deallocation happens automatically after `drop` returns).

`drop` is called automatically by the compiler. the programmer never calls
`drop()` directly on a value — this prevents double-drop bugs. to drop early,
use `std::mem::drop(value)` which takes ownership and lets the value go out of
scope.

**destruction order:**

- struct fields are dropped in reverse declaration order (last declared, first dropped)
- local variables are dropped in reverse declaration order within their scope
- for enums, only the active variant's payload is dropped
- a type with `Drop` cannot be `Copy` (prevents double-drop)

**partial moves:**

if a field is moved out of a struct, the remaining fields are dropped individually
at end of scope. the moved field is not dropped (the new owner is responsible).
the struct as a whole cannot be used after a partial move.

---

## 8. unsafe

### 8.1 purpose

`unsafe` blocks opt out of borrow checking for operations the compiler cannot
verify as safe. contracts are still enforced inside `unsafe` blocks — they
serve as the safety net when the compiler's static analysis can't help.

### 8.2 operations requiring unsafe

| operation                          | example                                |
|------------------------------------|----------------------------------------|
| raw pointer dereference            | `unsafe { *ptr }`                      |
| FFI (foreign function interface)   | `unsafe { c_function() }`             |
| mutable static variable access     | `unsafe { GLOBAL_COUNT += 1 }`        |
| integer-to-pointer cast            | `unsafe { 0xB800 as *mut u32 }`       |
| function pointer to integer cast   | `unsafe { func as u64 }`              |

### 8.3 contracts inside unsafe

contracts are NOT relaxed inside unsafe blocks. the programmer writes contracts
to document and verify the invariants that the compiler can't check:

```
unsafe fn write_mmio(addr: usize, value: u32) -> ()
    requires(addr != 0)
{
    let ptr = addr as *mut u32;
    *ptr = value;
}
```

### 8.4 raw pointers

`*const T` (immutable) and `*mut T` (mutable) are raw pointers.

| operation                    | safe? |
|------------------------------|-------|
| creating a raw pointer       | yes   |
| dereferencing a raw pointer  | NO — requires `unsafe` |
| pointer arithmetic           | NO — requires `unsafe` |
| casting reference to raw ptr | yes   |
| casting integer to pointer   | NO — requires `unsafe` |

raw pointers do not participate in the borrow checker. they exist for three
use cases:

1. kernel/hardware access (MMIO registers)
2. FFI with C libraries
3. data structures the borrow checker cannot express (e.g., doubly-linked lists)

all other code should use references (`&T`, `&mut T`).

### 8.5 raw pointer examples

```
let x: i32 = 42;
let p: *const i32 = &x as *const i32;  // safe: creating raw pointer
let q: *mut i32 = &mut x as *mut i32;  // safe: creating raw pointer

unsafe {
    let val = *p;       // unsafe: dereference
    *q = 100;           // unsafe: write through raw pointer
}

// integer to pointer (for MMIO)
let mmio: *mut u32 = unsafe { 0xB800_0000 as *mut u32 };
```

---

## 9. Send and Sync marker traits

### 9.1 Send

a type is `Send` if ownership can be transferred to another thread. the compiler
infers `Send` automatically: if all fields of a type are `Send`, the composite
type is `Send`.

- most types are `Send`
- raw pointers are NOT `Send`
- negative impl: `impl !Send for GpuBuffer {}`

### 9.2 Sync

a type is `Sync` if `&T` can be shared across threads (concurrent reads are safe).
a type is `Sync` if and only if `&T` is `Send`.

- most immutable types are `Sync`
- types with `&mut T` fields are NOT `Sync`
- negative impl: `impl !Sync for UnsafeCell<T> {}`

### 9.3 thread safety enforcement

`thread::spawn` requires the closure to be `Send + FnOnce`. this ensures:

- all captured values can be transferred to the new thread
- no references to the spawning scope cross thread boundaries (closures must use `move`)

---

## appendix: memory model summary

| aspect                           | mechanism              | annotation needed? |
|----------------------------------|------------------------|--------------------|
| ownership + move                 | automatic              | never              |
| `&T`/`&mut T` exclusivity       | automatic              | never              |
| local borrow tracking            | automatic (tier 1)     | never              |
| single-input function boundaries | elision rules (tier 2) | never              |
| `&self` methods                  | elision rules (tier 2) | never              |
| multiple-input reference returns | `borrows()` contract   | yes (tier 3)       |
| structs holding references       | `borrows()` on struct  | yes (tier 3)       |
| aliasing guarantees              | `no_alias()` contract  | yes                |
| memory postconditions            | `ensures()` with `old()` | yes              |
| raw pointer access               | `unsafe` block         | yes                |
