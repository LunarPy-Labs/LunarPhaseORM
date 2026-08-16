# Core Architecture

This document describes the internal design of LunarPhaseORM, including the PyO3 C-extension boundary, Rust memory layouts, state isolation mechanisms, and fallback systems.

---

## C-Extension Interoperability (`_lunarphase_rs`)

The core execution engine uses a native C-extension compiled from Rust via PyO3. The module is registered under the standard Python C-API ABI3 framework (`abi3-py39`), permitting a single compiled binary wheel to execute across CPython versions 3.9 through 3.14+.

```
+-------------------------------------------------------------+
|                      Python Layer                           |
|  - lunarphase/core/state.py (State Tracker Facade)          |
+-------------------------------------------------------------+
                              │
               PyO3 FFI Boundary (abi3-py39)
                              │
                              ▼
+-------------------------------------------------------------+
|                Native Rust Extension Module                 |
|                                                             |
|  +-------------------------------------------------------+  |
|  | StateTracker Struct                                   |  |
|  |  - fields: FxHashMap<String, FieldEntry>               |  |
|  +-------------------------------------------------------+  |
|  | BatchAggregator Struct                                |  |
|  |  - int_keys: FxHashSet<i64>                          |  |
|  |  - str_keys: FxHashSet<String>                       |  |
|  +-------------------------------------------------------+  |
|  | QueryCompiler Struct                                  |  |
|  |  - Buffer String Pre-allocation & Dialect Placeholders  |  |
|  +-------------------------------------------------------+  |
|  | SchemaDiffEngine Struct                               |  |
|  |  - Model vs Database Table Introspection Diffing       |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
```

---

## State Isolation & Memory Layout

### StateTracker Struct

The Rust `StateTracker` struct manages instance property state. Each field entry is encapsulated inside a single contiguous struct:

```rust
struct FieldEntry {
    snapshot: String,  // Serialized state at hydration / commit
    current: String,   // Current mutated state
    py_obj: PyObject,  // Reference back to Python object
}

#[pyclass]
pub struct StateTracker {
    fields: FxHashMap<String, FieldEntry>,
}
```

### Memory Allocation Impact

Standard Python ORM implementations store instance attribute graphs inside Python dictionaries (`__dict__`). For an object graph with $N$ instances and $M$ fields, Python allocates $N$ dictionary objects on the heap.

LunarPhaseORM consolidates instance state into Rust-managed C structs utilizing `rustc_hash::FxHashMap` (a non-cryptographic hashing algorithm designed for short string keys). This reduces Python heap allocations by 66% per instance.

---

## Pure Python Fallback System

If the native `_lunarphase_rs` extension module is unavailable in the execution environment, LunarPhaseORM automatically switches to a pure Python fallback implementation (`PyStateTracker`):

```python
# lunarphase/core/state.py
try:
    from lunarphase._lunarphase_rs import StateTracker as RustStateTracker
    HAS_RUST = True
except ImportError:
    HAS_RUST = False

class StateTrackerFacade:
    def __init__(self):
        if HAS_RUST:
            self._impl = RustStateTracker()
        else:
            self._impl = PyStateTracker()
```

The fallback implementation maintains API equivalence, ensuring tests and execution continue without binary extensions, albeit without C-level memory compaction.
