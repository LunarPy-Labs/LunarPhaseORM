# 📊 LunarPhaseORM Performance & Memory Benchmarks

This document presents empirical benchmark results and technical performance metrics for **LunarPhaseORM (`v0.1.0`)**. Benchmarks measure execution speed, throughput, latency, and peak tracked memory across the Python ORM layer and native Rust extension (`_lunarphase_rs`).

> **Benchmark note:** Memory figures reported in this document represent **peak memory tracked by `tracemalloc`**, not total process RSS. They should therefore be interpreted as Python-tracked allocation footprints rather than absolute system RAM usage.

---

## 🖥 Environment & Test Specifications

- **OS**: macOS (Apple Silicon arm64)
- **Python**: CPython 3.14 (`abi3-py39` wheel compatibility)
- **Rust Engine**: Rust 1.80+ compiled with `--release` profile (`maturin develop --release`, LTO enabled)
- **Benchmark Tooling**: `pytest-benchmark 5.2.3`, `tracemalloc`, Python `time.perf_counter`

> For exact reproducibility, benchmark results should be interpreted together with the CPU model, macOS version, and available system memory of the test machine.

---

## 1. ⚡ StateTracker Performance & Peak Tracked Memory

Measures snapshot state initialization, property modification, dirty-diff calculation (`is_dirty`), and snapshot hydration across dataset scales from 10 to 100,000 model objects.

### ⏱ Execution Time Benchmark

| Object Count | Pure Python Time | Rust Core Time | Speedup vs Python |
|---:|---:|---:|---:|
| **10** | 83 µs | **55 µs** | 🚀 **1.5× Faster** |
| **100** | 569 µs | **253 µs** | 🚀 **2.2× Faster** |
| **1,000** | 5.6 ms | **2.5 ms** | 🚀 **2.3× Faster** |
| **10,000** | 57.7 ms | **25.1 ms** | 🚀 **2.3× Faster** |
| **100,000** | 1.01 s | **311.0 ms** | 🚀 **3.2× Faster** |

### 🧠 Peak Tracked Memory Benchmark

| Object Count | Python Tracked Memory | Rust Tracked Memory | Reduction |
|---:|---:|---:|---:|
| **10** | 3.2 KB | **1.2 KB** | 🧠 **63.4% Lower** |
| **100** | 46.3 KB | **6.8 KB** | 🧠 **85.3% Lower** |
| **1,000** | 454.9 KB | **63.8 KB** | 🧠 **86.0% Lower** |
| **10,000** | 4.43 MB | **630.6 KB** | 🧠 **86.1% Lower** |
| **100,000** | **44.25 MB** | **6.10 MB** | 🧠 **86.2% Lower** |

> **Technical Insight:** The Rust `StateTracker` stores state using a native `rustc_hash::FxHashMap<String, FieldEntry>` representation. In this benchmark, the Rust implementation reduced peak tracked memory by **86.2% at 100,000 objects**, corresponding to approximately **38.15 MB less tracked memory** than the Python implementation.

---

## 2. ⚡ BatchAggregator — Native Integer Foreign-Key Aggregation

Measures relation foreign-key collection and deduplication using single-pass batch ingestion and native numeric key storage (`FxHashSet<i64>`).

### ⏱ Execution Time & Memory Benchmark

| Key Objects | Python Set Time | Rust Aggregator Time | Speedup vs Python | Tracked Memory Reduction |
|---:|---:|---:|---:|---:|
| **10** | 46 µs | **41 µs** | 🚀 **1.1× Faster** | 🧠 **70.4% Lower** |
| **100** | 47 µs | **42 µs** | 🚀 **1.1× Faster** | 🧠 **90.6% Lower** |
| **1,000** | 1.1 ms | **1.0 ms** | 🚀 **1.1× Faster** | 🧠 **55.7% Lower** |
| **10,000** | 10.2 ms | **1.2 ms** | 🚀 **8.6× Faster** | 🧠 **91.0% Lower** |
| **100,000** | **102.6 ms** | **2.6 ms** | 🚀 **38.8× Faster** | 🧠 **99.0% Lower** |

> **Technical Insight:** The optimized Rust implementation stores numeric foreign keys directly as `i64` values inside an `FxHashSet`, avoiding intermediate string representation. At 100,000 keys, the measured execution time decreased from **102.6 ms to 2.6 ms**, resulting in a **38.8× speedup** in this specific numeric-key aggregation workload.

---

## 3. 🚀 Model Hydration & Mass Instantiation

Measures the throughput of instantiating active ORM `Model` instances from raw database query rows (`dict`).

| Dataset Size | Duration | Throughput | Peak Tracked Memory |
|---:|---:|---:|---:|
| **1,000 Rows** | 6.1 ms | **163,393 ops/sec** | 145.3 KB |
| **10,000 Rows** | 60.5 ms | **165,168 ops/sec** | 1.38 MB |
| **100,000 Rows** | 704.5 ms | **141,937 ops/sec** | 13.73 MB |

> **Technical Insight:** LunarPhaseORM processed approximately **141,000 model hydration operations per second** at the 100,000-row scale, with **13.73 MB of peak tracked memory** recorded by the benchmark.

---

## 4. 🛠 Rust Schema Diff Engine

Measures the duration required by the native Rust `SchemaDiffEngine` to compare database schema introspection data against ORM model metadata and generate migration DDL statements.

| Table Column Count | Schema Diff Duration | Generated DDL |
|---:|---:|---:|
| **10 Columns** | **13 µs** | 5 `ALTER TABLE` Statements |
| **50 Columns** | **57 µs** | 5 `ALTER TABLE` Statements |
| **100 Columns** | **106 µs** | 5 `ALTER TABLE` Statements |
| **500 Columns** | **502 µs** | 5 `ALTER TABLE` Statements |

> **Technical Insight:** The Rust schema comparison and DDL-generation stage completed in **502 µs for a 500-column schema** in this benchmark. The measurement covers schema comparison and DDL generation; it does **not** include database connection, lock acquisition, disk I/O, or execution of the generated SQL statements.

---

## 5. 🔄 Unit of Work & Identity Map Transactions

Measures atomic transaction session handling (`async with uow.begin()`) together with identity-map registration across different record counts.

| Records in Session | Transaction Session Duration | Transaction Model |
|---:|---:|---|
| **100 Records** | 13.2 ms | Atomic Batch Transaction |
| **1,000 Records** | 131.9 ms | Atomic Batch Transaction |
| **5,000 Records** | 649.2 ms | Atomic Batch Transaction |

> **Technical Insight:** The measured transaction workload demonstrates approximately linear scaling across the tested record counts while maintaining atomic transaction semantics and identity-map registration.

---

## 6. 🎯 N+1 Query Resolution

Compares sequential relation access against automatic micro-task batching through `DeferredAutoBatcher`.

| Query Approach | SQL Queries | Execution Time | Result |
|---|---:|---:|---:|
| **Sequential N+1 Access** | 100 | 16.7 ms | Baseline |
| **Deferred Auto-Batcher** | **1** | **3.3 ms** | 🚀 **5.1× Faster** |

### Observed Results

- **5.1× faster** execution in the benchmark.
- Approximately **80.2% lower measured latency**.
- SQL round trips reduced from **100 → 1**, representing **99% fewer query round trips** in this workload.

> **Technical Insight:** `DeferredAutoBatcher` consolidates deferred relation accesses into a single batch query, substantially reducing the number of database round trips. The benchmark measures query execution latency; actual network-byte reduction depends on query payload and database response sizes.

---

# 📈 Summary of Key Results

| Component | Key Result |
|---|---|
| **StateTracker** | **3.2× faster** at 100K objects |
| **StateTracker Memory** | **86.2% lower tracked memory** at 100K |
| **BatchAggregator** | **38.8× faster** at 100K numeric keys |
| **BatchAggregator Memory** | **99.0% lower tracked memory** at 100K |
| **Model Hydration** | **141,937 ops/sec** at 100K rows |
| **SchemaDiffEngine** | **502 µs** for 500-column schema diff |
| **UnitOfWork** | Approximately linear scaling through 5K records |
| **N+1 Auto-Batching** | **5.1× faster**, 100 → 1 SQL round trip |

---

# 💻 How to Reproduce Benchmarks

Run the benchmark scripts locally inside the project virtual environment:

```bash
# 1. Compile Rust Core with Release Optimizations
maturin develop --release

# 2. Run pytest-benchmark Suite
pytest tests/test_benchmarks.py \
  --benchmark-only \
  --benchmark-sort=mean

# 3. Run Advanced Multi-Scale Benchmark
python benchmarks/advanced_scale_benchmark.py

# 4. Run 3-Way Diagnostic Benchmark
python benchmarks/diagnostic_3way_benchmark.py

# 5. Run Comprehensive ORM Benchmark Suite
python benchmarks/comprehensive_orm_benchmark.py
```

> **Methodology:** Results are empirical measurements from the specified test environment. Benchmark results may vary depending on CPU architecture, operating-system scheduling, Python build, compiler configuration, database environment, and system workload. Comparative claims should therefore be reproduced under identical conditions before being generalized to other environments.
