import pytest
import time
from lunarphase._lunarphase_rs import StateTracker, QueryCompiler, BatchAggregator, SchemaDiffEngine

def test_rust_core_module_import():
    tracker = StateTracker()
    assert tracker is not None
    compiler = QueryCompiler()
    assert compiler is not None
    aggregator = BatchAggregator()
    assert aggregator is not None
    diff_engine = SchemaDiffEngine()
    assert diff_engine is not None

def test_rust_state_tracker_dirty_diff():
    tracker = StateTracker()
    # Initial state
    tracker.set_initial_state({"name": "Alice", "score": 100, "active": True})
    assert not tracker.is_dirty()
    assert tracker.dirty_fields() == []

    # Mutate score
    tracker.set_field("score", 150)
    assert tracker.is_dirty()
    assert tracker.dirty_fields() == ["score"]
    assert tracker.get_dirty_changes() == {"score": 150}

    # Hydrate snapshot
    tracker.hydrate_snapshot()
    assert not tracker.is_dirty()

def test_rust_state_tracker_benchmark():
    tracker = StateTracker()
    tracker.set_initial_state({"id": 1, "value": "test", "counter": 0})

    start = time.perf_counter()
    for i in range(10000):
        tracker.set_field("counter", i)
        _ = tracker.is_dirty()
    duration = time.perf_counter() - start

    assert duration < 1.0, f"Rust StateTracker took {duration:.4f} seconds for 10,000 updates"

def test_rust_query_compiler_dialects():
    compiler = QueryCompiler()

    # SQLite
    sql_sqlite, params = compiler.compile_select("users", ["id", "name"], [("age", ">", "18")], [], [], 10, 0, "sqlite")
    assert "SELECT id, name FROM users WHERE age > ?" in sql_sqlite
    assert params == ["18"]

    # Postgres
    sql_pg, _ = compiler.compile_select("users", ["id", "name"], [("age", ">", "18")], [], [], 10, 0, "postgres")
    assert "SELECT id, name FROM users WHERE age > $1" in sql_pg

    # MySQL
    sql_mysql, _ = compiler.compile_select("users", ["id", "name"], [("age", ">", "18")], [], [], 10, 0, "mysql")
    assert "SELECT id, name FROM users WHERE age > %s" in sql_mysql
