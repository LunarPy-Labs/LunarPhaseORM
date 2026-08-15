import time
import tracemalloc
import gc
from lunarphase._lunarphase_rs import StateTracker as RustStateTracker, BatchAggregator as RustBatchAggregator
from lunarphase.core.state import PyStateTracker

def format_duration(seconds: float) -> str:
    """Formats execution time into µs, ms, or s cleanly."""
    us = seconds * 1_000_000
    if us < 1000:
        return f"{us:.0f} µs"
    ms = us / 1000
    if ms < 1000:
        return f"{ms:.1f} ms"
    s = ms / 1000
    return f"{s:.2f} s"

def format_bytes(bytes_val: int) -> str:
    """Formats byte counts into B, KB, or MB cleanly."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    kb = bytes_val / 1024
    if kb < 1024:
        return f"{kb:.1f} KB"
    mb = kb / 1024
    return f"{mb:.2f} MB"

def run_state_tracker_benchmark():
    object_counts = [10, 100, 1000, 10000, 100000]

    print("\n" + "=" * 65)
    print(" 🚀 ADVANCED BENCHMARK: StateTracker Time & Memory (Python vs Rust)")
    print("=" * 65)

    print("\n### ⏱ Execution Time Benchmark\n")
    print(f"| {'Objects':<10} | {'Python Time':<14} | {'Rust Time':<14} | {'Speedup':<10} |")
    print(f"|{'-'*12}|{'-'*16}|{'-'*16}|{'-'*12}|")

    for count in object_counts:
        # Python StateTracker Time
        t0 = time.perf_counter()
        py_trackers = [PyStateTracker() for _ in range(count)]
        for t in py_trackers:
            t.set_initial_state({"id": 1, "name": "Alice", "age": 25, "active": True})
            t.set_field("age", 26)
            _ = t.is_dirty()
            t.hydrate_snapshot()
        py_time = time.perf_counter() - t0

        # Rust StateTracker Time
        t0 = time.perf_counter()
        rust_trackers = [RustStateTracker() for _ in range(count)]
        for r in rust_trackers:
            r.set_initial_state({"id": 1, "name": "Alice", "age": 25, "active": True})
            r.set_field("age", 26)
            _ = r.is_dirty()
            r.hydrate_snapshot()
        rust_time = time.perf_counter() - t0

        speedup = f"{py_time / rust_time:.1f}x Faster" if rust_time > 0 and py_time >= rust_time else f"{rust_time / py_time:.1f}x Slower"
        print(f"| {count:<10,d} | {format_duration(py_time):<14} | {format_duration(rust_time):<14} | {speedup:<10} |")

    print("\n### 🧠 Peak Memory Footprint (RAM) Benchmark\n")
    print(f"| {'Objects':<10} | {'Python RAM':<14} | {'Rust RAM':<14} | {'RAM Savings':<12} |")
    print(f"|{'-'*12}|{'-'*16}|{'-'*16}|{'-'*14}|")

    for count in object_counts:
        # Python Memory
        gc.collect()
        tracemalloc.start()
        py_trackers = [PyStateTracker() for _ in range(count)]
        for t in py_trackers:
            t.set_initial_state({"id": 1, "name": "Alice", "age": 25, "active": True})
        _, py_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        del py_trackers

        # Rust Memory
        gc.collect()
        tracemalloc.start()
        rust_trackers = [RustStateTracker() for _ in range(count)]
        for r in rust_trackers:
            r.set_initial_state({"id": 1, "name": "Alice", "age": 25, "active": True})
        _, rust_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        del rust_trackers

        savings = f"{(1 - (rust_peak / py_peak)) * 100:.1f}% Saved" if py_peak > 0 else "0%"
        print(f"| {count:<10,d} | {format_bytes(py_peak):<14} | {format_bytes(rust_peak):<14} | {savings:<12} |")

    print("\n" + "=" * 65 + "\n")


def run_batch_aggregator_benchmark():
    object_counts = [10, 100, 1000, 10000, 100000]
    print("=" * 65)
    print(" 🚀 ADVANCED BENCHMARK: BatchAggregator (Native Integer Keys & Batch Ingestion)")
    print("=" * 65)

    print("\n### ⏱ Execution Time & Memory Benchmark (Numeric Foreign Keys)\n")
    print(f"| {'Objects':<10} | {'Python Set':<12} | {'Rust Aggregator':<16} | {'Speedup':<10} | {'RAM Savings':<12} |")
    print(f"|{'-'*12}|{'-'*14}|{'-'*18}|{'-'*12}|{'-'*14}|")

    for count in object_counts:
        # Python Set Time & Memory
        gc.collect()
        tracemalloc.start()
        t0 = time.perf_counter()
        py_set = set()
        raw_keys = [i % 1000 for i in range(count)]
        for k in raw_keys:
            py_set.add(k)
        _ = list(py_set)
        py_time = time.perf_counter() - t0
        _, py_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Rust BatchAggregator Time & Memory (Single Batch FFI Ingestion + i64 Native HashSet)
        gc.collect()
        tracemalloc.start()
        t0 = time.perf_counter()
        rust_agg = RustBatchAggregator()
        rust_agg.add_keys_batch(raw_keys)
        _ = rust_agg.get_keys()
        rust_time = time.perf_counter() - t0
        _, rust_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        speedup = f"{py_time / rust_time:.1f}x Faster" if rust_time > 0 and py_time >= rust_time else f"{rust_time / py_time:.1f}x Slower"
        savings = f"{(1 - (rust_peak / py_peak)) * 100:.1f}% Saved" if py_peak > 0 else "0%"
        print(f"| {count:<10,d} | {format_duration(py_time):<12} | {format_duration(rust_time):<16} | {speedup:<10} | {savings:<12} |")

    print("\n" + "=" * 65 + "\n")

if __name__ == "__main__":
    run_state_tracker_benchmark()
    run_batch_aggregator_benchmark()
