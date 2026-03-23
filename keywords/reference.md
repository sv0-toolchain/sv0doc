# sv0 keyword and operator reference

complete keyword and operator reference tables for the sv0 programming language.
this reference drives the lexer's keyword recognition and the parser's operator
precedence.

extracted from: sv0 compiler vision and design document

---

## 1. reserved keywords

### 1.1 binding keywords

| keyword  | purpose                                          |
|----------|--------------------------------------------------|
| `let`    | variable binding (immutable by default)          |
| `mut`    | mutable binding modifier                         |
| `const`  | compile-time constant declaration                |
| `static` | global lifetime variable (one instance)          |

### 1.2 function keywords

| keyword  | purpose                                          |
|----------|--------------------------------------------------|
| `fn`     | function definition                              |
| `return` | explicit early return from function              |

### 1.3 control flow keywords

| keyword    | purpose                                          |
|------------|--------------------------------------------------|
| `if`       | conditional branching                            |
| `else`     | alternative branch                               |
| `match`    | exhaustive pattern matching expression           |
| `while`    | conditional loop                                 |
| `for`      | iterator-based loop (`for x in expr`)            |
| `in`       | iterator source in `for` loops                   |
| `loop`     | unconditional infinite loop                      |
| `break`    | exit the innermost loop                          |
| `continue` | skip to the next iteration of the innermost loop|

### 1.4 type definition keywords

| keyword   | purpose                                         |
|-----------|-------------------------------------------------|
| `struct`  | product type (named fields)                     |
| `enum`    | sum type (tagged union / algebraic data type)   |
| `trait`   | interface definition (with optional contracts)  |
| `impl`    | trait implementation or inherent methods         |
| `type`    | type alias (transparent) or refined type        |
| `newtype` | distinct wrapper type (not interchangeable)     |
| `where`   | trait bounds on generics; refinement predicates |

### 1.5 visibility keywords

| keyword        | purpose                                              |
|----------------|------------------------------------------------------|
| `pub`          | public visibility (accessible from outside)          |
| `pub(project)` | project-internal visibility (not exposed externally) |
| `project`      | reserved keyword: refers to the current project      |

### 1.6 module keywords

| keyword  | purpose                                          |
|----------|--------------------------------------------------|
| `module` | module path declaration                          |
| `use`    | import items from other modules                  |

### 1.7 safety and ownership keywords

| keyword  | purpose                                          |
|----------|--------------------------------------------------|
| `unsafe` | opt out of borrow checking for unsafe operations |
| `move`   | force closure to capture environment by value    |

### 1.8 casting keyword

| keyword | purpose                                           |
|---------|---------------------------------------------------|
| `as`    | type cast (with implicit contract on narrowing)   |

### 1.9 self keywords

| keyword | purpose                                           |
|---------|---------------------------------------------------|
| `self`  | method receiver (current instance)                |
| `Self`  | the implementing type in trait/impl context       |

### 1.10 contract keywords

| keyword          | purpose                                        |
|------------------|------------------------------------------------|
| `requires`       | precondition (must hold on function entry)     |
| `ensures`        | postcondition (must hold on function exit)     |
| `loop_invariant` | loop invariant (must hold each iteration)      |
| `result`         | return value binding in `ensures` clauses      |
| `old`            | pre-state snapshot in `ensures` clauses        |
| `forall`         | universal quantifier in contract expressions   |
| `exists`         | existential quantifier in contract expressions |
| `borrows`        | borrow-source annotation for references        |
| `no_alias`       | non-aliasing assertion for pointer arguments   |

### 1.11 literal keywords

| keyword | purpose                                           |
|---------|---------------------------------------------------|
| `true`  | boolean literal true                              |
| `false` | boolean literal false                             |
| `Some`  | `Option<T>` constructor (value present)           |
| `None`  | `Option<T>` constructor (value absent)            |
| `Ok`    | `Result<T, E>` constructor (success)              |
| `Err`   | `Result<T, E>` constructor (failure)              |

### 1.12 assertion keyword

| keyword  | purpose                                           |
|----------|---------------------------------------------------|
| `assert` | runtime assertion (panics on failure if false)    |

`assert expr;` is a keyword-level statement, not a macro. it desugars to
`if !(expr) { panic("assertion failed: ...") }`.

### 1.13 reserved for future milestones

| keyword | purpose                        | milestone |
|---------|--------------------------------|-----------|
| `asm!`  | inline assembly macro          | 6         |

### 1.14 complete keyword list (alphabetical)

```
as        assert      borrows     break     const       continue
else      ensures     enum        Err       exists      false
fn        for         forall      if        impl        in
let       loop        loop_invariant        match       module
move      mut         newtype     no_alias  None        Ok
old       project     pub         requires  result      return
self      Self        Some        static    struct      trait
true      type        unsafe      use       where       while
```

total: 47 reserved keywords.

---

## 2. operators

### 2.1 arithmetic operators

| operator | purpose        | arity  | trait              |
|----------|----------------|--------|--------------------|
| `+`      | addition       | binary | `core::ops::Add`   |
| `-`      | subtraction    | binary | `core::ops::Sub`   |
| `*`      | multiplication | binary | `core::ops::Mul`   |
| `/`      | division       | binary | `core::ops::Div`   |
| `%`      | remainder      | binary | `core::ops::Rem`   |
| `-`      | negation       | unary  | `core::ops::Neg`   |

### 2.2 equality and comparison operators

| operator | purpose              | arity  | trait              |
|----------|----------------------|--------|--------------------|
| `==`     | equal                | binary | `core::ops::Eq`    |
| `!=`     | not equal            | binary | `core::ops::Eq`    |
| `<`      | less than            | binary | `core::ops::Ord`   |
| `>`      | greater than         | binary | `core::ops::Ord`   |
| `<=`     | less or equal        | binary | `core::ops::Ord`   |
| `>=`     | greater or equal     | binary | `core::ops::Ord`   |

### 2.3 logical operators

| operator | purpose    | arity  | trait                     |
|----------|------------|--------|---------------------------|
| `&&`     | logical and | binary | built-in for `bool`       |
| `\|\|`  | logical or  | binary | built-in for `bool`       |
| `!`      | logical not | unary  | built-in for `bool`       |

logical `&&` and `||` are short-circuit: the right operand is only evaluated
if the left operand does not determine the result.

### 2.4 bitwise operators

| operator | purpose      | arity  | trait                    |
|----------|--------------|--------|--------------------------|
| `&`      | bitwise and  | binary | `core::ops::BitAnd`     |
| `\|`     | bitwise or   | binary | `core::ops::BitOr`      |
| `^`      | bitwise xor  | binary | `core::ops::BitXor`     |
| `~`      | bitwise not  | unary  | `core::ops::Not`        |
| `<<`     | left shift   | binary | `core::ops::Shl`        |
| `>>`     | right shift  | binary | `core::ops::Shr`        |

### 2.5 reference and dereference operators

| operator | purpose              | arity  | trait                        |
|----------|----------------------|--------|------------------------------|
| `&`      | shared borrow        | unary  | built-in                     |
| `&mut`   | mutable borrow       | unary  | built-in                     |
| `*`      | dereference          | unary  | `core::ops::Deref` / `DerefMut` |

context disambiguates `&` (borrow vs bitwise and) and `*` (dereference vs multiply):

- unary prefix position: `&expr` is borrow, `*expr` is dereference
- binary infix position: `a & b` is bitwise and, `a * b` is multiply

### 2.6 error propagation operator

| operator | purpose             | arity  | trait                        |
|----------|---------------------|--------|------------------------------|
| `?`      | early return on err | postfix| built-in for `Result`/`Option` |

`expr?` on a `Result<T, E>`:

- if `Ok(v)`: unwraps to `v`
- if `Err(e)`: returns `Err(e)` from the enclosing function

`expr?` on an `Option<T>`:

- if `Some(v)`: unwraps to `v`
- if `None`: returns `None` from the enclosing function

can only be used in functions returning `Result` or `Option`.

### 2.7 range operators

| operator | purpose         | arity  | trait      |
|----------|-----------------|--------|------------|
| `..`     | half-open range | binary | built-in   |
| `..=`    | inclusive range  | binary | built-in   |

`0..10` produces `[0, 10)` (0 through 9).
`0..=10` produces `[0, 10]` (0 through 10).

### 2.8 index operator

| operator | purpose    | arity  | trait                           |
|----------|------------|--------|---------------------------------|
| `[]`     | indexing   | postfix| `core::ops::Index` / `IndexMut` |

`a[i]` desugars to `Index::index(&a, i)`.
`a[i] = v` desugars to `*IndexMut::index_mut(&mut a, i) = v`.

### 2.9 cast operator

| operator | purpose     | arity  | trait      |
|----------|-------------|--------|------------|
| `as`     | type cast   | postfix| built-in   |

`expr as Type` performs a type cast. narrowing casts insert implicit contracts.

### 2.10 pattern and structural operators

| operator | purpose                    | context       | trait      |
|----------|----------------------------|---------------|------------|
| `\|`     | or-pattern in match        | patterns      | built-in   |
| `=>`     | closure arrow / match arm  | closures/match| built-in   |
| `::`     | path separator             | paths         | built-in   |
| `.`      | field access / method call | expressions   | built-in   |
| `#[...]` | attribute annotation       | items         | built-in   |

### 2.11 assignment and compound assignment operators

| operator | purpose                | arity  | trait                    |
|----------|------------------------|--------|--------------------------|
| `=`      | assignment             | binary | built-in                 |
| `+=`     | add and assign         | binary | `core::ops::AddAssign`   |
| `-=`     | subtract and assign    | binary | `core::ops::SubAssign`   |
| `*=`     | multiply and assign    | binary | `core::ops::MulAssign`   |
| `/=`     | divide and assign      | binary | `core::ops::DivAssign`   |
| `%=`     | remainder and assign   | binary | `core::ops::RemAssign`   |
| `&=`     | bitwise AND and assign | binary | `core::ops::BitAndAssign`|
| `\|=`    | bitwise OR and assign  | binary | `core::ops::BitOrAssign` |
| `^=`     | bitwise XOR and assign | binary | `core::ops::BitXorAssign`|
| `<<=`    | left shift and assign  | binary | `core::ops::ShlAssign`   |
| `>>=`    | right shift and assign | binary | `core::ops::ShrAssign`   |

`x += y` desugars to `x = x + y` (calls `AddAssign::add_assign` when overloaded).
assignment is a statement, not an expression. it does not return a value.

---

## 3. operator precedence table

precedence levels from highest (tightest binding) to lowest. operators at the
same precedence level are left-associative unless noted.

| level | category       | operators                          | associativity   |
|-------|----------------|------------------------------------|-----------------|
| 1     | postfix        | `.` `()` `[]` `?`                  | left            |
| 2     | unary          | `-` `!` `~` `*` `&` `&mut`        | right (prefix)  |
| 3     | cast           | `as`                               | left            |
| 4     | multiplicative | `*` `/` `%`                        | left            |
| 5     | additive       | `+` `-`                            | left            |
| 6     | shift          | `<<` `>>`                          | left            |
| 7     | bitwise AND    | `&`                                | left            |
| 8     | bitwise XOR    | `^`                                | left            |
| 9     | bitwise OR     | `\|`                               | left            |
| 10    | comparison     | `==` `!=` `<` `>` `<=` `>=`       | non-associative |
| 11    | logical AND    | `&&`                               | left            |
| 12    | logical OR     | `\|\|`                             | left            |
| 13    | range          | `..` `..=`                         | non-associative |
| 14    | assignment     | `=` `+=` `-=` `*=` `/=` `%=` etc. | right           |

notes:

- comparison operators are non-associative: `a < b < c` is a compile error (use `a < b && b < c`)
- range operators are non-associative: `a..b..c` is a compile error
- unary operators bind tighter than binary: `-a + b` is `(-a) + b`
- `as` binds tighter than arithmetic: `x as f64 + 1.0` is `(x as f64) + 1.0`
- closures `(x) => expr` have the lowest precedence among expressions

design decision: this precedence table follows the C/Rust convention as specified
by the design document's stated influences ("C-like surface syntax" with Rust
as a primary inspiration).

---

## 4. delimiter tokens

| token | purpose                                    |
|-------|--------------------------------------------|
| `{`   | block / struct / enum / match body open     |
| `}`   | block / struct / enum / match body close    |
| `(`   | grouping / tuple / function params open     |
| `)`   | grouping / tuple / function params close    |
| `[`   | array / index / attribute open              |
| `]`   | array / index / attribute close             |
| `;`   | statement terminator                        |
| `,`   | separator in lists                          |
| `:`   | type annotation separator                   |
| `->`  | return type separator                       |
| `::`  | path separator                              |
| `=>`  | match arm / closure body separator          |
| `..`  | range / struct rest pattern                 |
| `#`   | attribute prefix (in `#[...]`)             |

---

## 5. type keyword tokens

these identifiers are recognized as type names by the parser:

| token    | type                              |
|----------|-----------------------------------|
| `i8`     | 8-bit signed integer              |
| `i16`    | 16-bit signed integer             |
| `i32`    | 32-bit signed integer             |
| `i64`    | 64-bit signed integer             |
| `i128`   | 128-bit signed integer            |
| `u8`     | 8-bit unsigned integer            |
| `u16`    | 16-bit unsigned integer           |
| `u32`    | 32-bit unsigned integer           |
| `u64`    | 64-bit unsigned integer           |
| `u128`   | 128-bit unsigned integer          |
| `usize`  | pointer-width unsigned integer    |
| `isize`  | pointer-width signed integer      |
| `f32`    | 32-bit IEEE 754 float             |
| `f64`    | 64-bit IEEE 754 float             |
| `bool`   | boolean type                      |
| `char`   | unicode scalar value (UTF-32)     |
| `byte`   | alias for `u8`                    |
| `string` | owned UTF-8 string                |
