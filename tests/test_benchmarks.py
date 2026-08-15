import pytest
from lunarphase._lunarphase_rs import StateTracker as RustStateTracker, QueryCompiler as RustQueryCompiler, BatchAggregator as RustBatchAggregator
from lunarphase.core.state import PyStateTracker
from lunarphase import Model, PrimaryKeyField, StringField, IntegerField

class BenchUser(Model):
    __tablename__ = "bench_users"
    id = PrimaryKeyField()
    name = StringField()
    age = IntegerField()
    email = StringField()

def test_bench_rust_state_tracker(benchmark):
    def run_rust_tracker():
        tracker = RustStateTracker()
        tracker.set_initial_state({"id": 1, "name": "Alice", "age": 25, "email": "alice@example.com"})
        for i in range(500):
            tracker.set_field("age", 25 + (i % 10))
            _ = tracker.is_dirty()
            _ = tracker.get_dirty_changes()
        return tracker

    benchmark(run_rust_tracker)

def test_bench_python_state_tracker(benchmark):
    def run_py_tracker():
        tracker = PyStateTracker()
        tracker.set_initial_state({"id": 1, "name": "Alice", "age": 25, "email": "alice@example.com"})
        for i in range(500):
            tracker.set_field("age", 25 + (i % 10))
            _ = tracker.is_dirty()
            _ = tracker.get_dirty_changes()
        return tracker

    benchmark(run_py_tracker)

def test_bench_rust_query_compiler(benchmark):
    compiler = RustQueryCompiler()
    wheres = [("age", ">", "18"), ("status", "=", "'active'")]
    joins = [("inner", "roles", "users.role_id = roles.id")]
    order_by = [("created_at", "desc")]

    def run_rust_compiler():
        for _ in range(500):
            _ = compiler.compile_select("users", ["id", "name", "email"], wheres, joins, order_by, 10, 0, "sqlite")

    benchmark(run_rust_compiler)

def test_bench_python_query_compiler(benchmark):
    columns = ["id", "name", "email"]
    wheres = [("age", ">", "18"), ("status", "=", "'active'")]
    joins = [("inner", "roles", "users.role_id = roles.id")]
    order_by = [("created_at", "desc")]
    limit = 10
    offset = 0

    def run_py_compiler():
        for _ in range(500):
            cols_str = ", ".join(columns)
            sql = f"SELECT {cols_str} FROM users"
            params = []
            for jtype, jtable, jcond in joins:
                sql += f" {jtype.upper()} JOIN {jtable} ON {jcond}"
            if wheres:
                where_clauses = []
                for col, op, val in wheres:
                    where_clauses.append(f"{col} {op} ?")
                    params.append(val)
                sql += " WHERE " + " AND ".join(where_clauses)
            if order_by:
                order_clauses = [f"{col} {dir.upper()}" for col, dir in order_by]
                sql += " ORDER BY " + ", ".join(order_clauses)
            if limit is not None:
                sql += f" LIMIT {limit}"
            if offset is not None:
                sql += f" OFFSET {offset}"

    benchmark(run_py_compiler)

def test_bench_rust_batch_aggregator(benchmark):
    def run_rust_aggregator():
        agg = RustBatchAggregator()
        for i in range(1000):
            agg.add_key(str(i % 100))
        return agg.get_keys()

    benchmark(run_rust_aggregator)

def test_bench_model_hydration_and_dirty_diff(benchmark):
    raw_rows = [{"id": i, "name": f"User-{i}", "age": 20 + i, "email": f"user{i}@test.com"} for i in range(200)]

    def run_model_operations():
        models = [BenchUser.hydrate(row) for row in raw_rows]
        for m in models:
            m.age += 1
            _ = m.is_dirty
            _ = m.get_dirty_changes()
        return models

    benchmark(run_model_operations)
