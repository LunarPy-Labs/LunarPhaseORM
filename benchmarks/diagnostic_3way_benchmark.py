import time
from lunarphase._lunarphase_rs import StateTracker as RustStateTracker
from lunarphase.core.state import PyStateTracker

def format_time(seconds: float) -> str:
    us = seconds * 1_000_000
    if us < 1000:
        return f"{us:.1f} µs"
    ms = us / 1000
    if ms < 1000:
        return f"{ms:.2f} ms"
    s = ms / 1000
    return f"{s:.2f} s"

def run_3way_benchmark():
    dataset = [10, 100, 1000, 10000, 100000]

    print("\n" + "=" * 75)
    print(" 🔍 DIAGNOSTIC BENCHMARK: Di mana waktu sebenarnya habis?")
    print("=" * 75)
    print(f"{'Objects':<10} | {'A. Pure Python':<18} | {'B. Pure Rust':<18} | {'C. Python -> Rust':<18}")
    print("-" * 75)

    for count in dataset:
        # A. Pure Python (Python -> Python)
        py_trackers = [PyStateTracker() for _ in range(count)]
        for t in py_trackers:
            t.set_initial_state({"id": 1, "name": "Alice", "age": 25, "active": True})

        t0 = time.perf_counter()
        for t in py_trackers:
            t.set_field("age", 26)
            _ = t.is_dirty()
            t.hydrate_snapshot()
        time_a = time.perf_counter() - t0

        # B. Pure Rust (Rust -> Rust) - 100% inside Rust memory without FFI crossing loop
        time_b = RustStateTracker.benchmark_pure_rust(count)

        # C. Python -> Rust (Python -> PyO3 -> Rust -> PyO3 -> Python) - Item-by-item PyO3 FFI calls
        rust_trackers = [RustStateTracker() for _ in range(count)]
        for r in rust_trackers:
            r.set_initial_state({"id": 1, "name": "Alice", "age": 25, "active": True})

        t0 = time.perf_counter()
        for r in rust_trackers:
            r.set_field("age", 26)
            _ = r.is_dirty()
            r.hydrate_snapshot()
        time_c = time.perf_counter() - t0

        print(f"{count:<10,d} | {format_time(time_a):<18} | {format_time(time_b):<18} | {format_time(time_c):<18}")

    print("=" * 75 + "\n")

if __name__ == "__main__":
    run_3way_benchmark()
