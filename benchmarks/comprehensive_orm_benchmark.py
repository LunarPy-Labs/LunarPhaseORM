import asyncio
import time
import tracemalloc
import gc

from lunarphase import (
    Model,
    PrimaryKeyField,
    StringField,
    IntegerField,
    HasMany,
    BelongsTo,
    create_engine,
    UnitOfWork,
)
from lunarphase._lunarphase_rs import SchemaDiffEngine
from lunarphase.query.batcher import DeferredAutoBatcher

# Define Models for Hydration & Relation Benchmarks
class Author(Model):
    __tablename__ = "authors"
    id = PrimaryKeyField()
    name = StringField()
    email = StringField()
    posts = HasMany(lambda: Post, foreign_key="author_id")

class Post(Model):
    __tablename__ = "posts"
    id = PrimaryKeyField()
    title = StringField()
    views = IntegerField()
    author_id = IntegerField()
    author = BelongsTo(Author, foreign_key="author_id")


def format_duration(seconds: float) -> str:
    us = seconds * 1_000_000
    if us < 1000:
        return f"{us:.0f} µs"
    ms = us / 1000
    if ms < 1000:
        return f"{ms:.1f} ms"
    s = ms / 1000
    return f"{s:.2f} s"

def format_bytes(bytes_val: int) -> str:
    if bytes_val < 1024:
        return f"{bytes_val} B"
    kb = bytes_val / 1024
    if kb < 1024:
        return f"{kb:.1f} KB"
    mb = kb / 1024
    return f"{mb:.2f} MB"


# 1. Hydration & Mass Instantiation Benchmark
def run_hydration_benchmark():
    dataset_sizes = [1000, 10000, 100000]
    print("\n" + "=" * 65)
    print(" 🚀 1. HYDRATION BENCHMARK (Model.hydrate Mass Instantiation)")
    print("=" * 65)
    print(f"{'Rows':<12} | {'Time':<12} | {'Ops / Sec':<16} | {'Peak RAM':<12}")
    print("-" * 65)

    for count in dataset_sizes:
        raw_rows = [
            {"id": i, "name": f"Author {i}", "email": f"author{i}@test.com"}
            for i in range(count)
        ]

        gc.collect()
        tracemalloc.start()
        t0 = time.perf_counter()

        models = [Author.hydrate(row) for row in raw_rows]

        duration = time.perf_counter() - t0
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        ops_per_sec = count / duration if duration > 0 else 0
        print(
            f"{count:<12,d} | {format_duration(duration):<12} | "
            f"{ops_per_sec:<16,.0f} | {format_bytes(peak_mem):<12}"
        )
        del models, raw_rows

    print("=" * 65 + "\n")


# 2. Rust Schema Diff Engine Benchmark
def run_schema_diff_benchmark():
    diff_engine = SchemaDiffEngine()
    column_counts = [10, 50, 100, 500]

    print("=" * 65)
    print(" 🚀 2. RUST SCHEMA DIFF ENGINE BENCHMARK (SchemaDiffEngine)")
    print("=" * 65)
    print(f"{'Columns':<12} | {'Diff Time':<14} | {'Generated DDLs':<18}")
    print("-" * 65)

    for cols_cnt in column_counts:
        model_fields = {
            f"col_{i}": {"data_type": "VARCHAR(255)", "nullable": True, "primary_key": False}
            for i in range(cols_cnt)
        }
        # Database DB columns missing last 5 columns
        db_cols = {
            f"col_{i}": "VARCHAR(255)"
            for i in range(cols_cnt - 5)
        }

        t0 = time.perf_counter()
        for _ in range(100):
            upgrade_ddls, _ = diff_engine.diff_table("users", model_fields, db_cols, "sqlite")
        duration = (time.perf_counter() - t0) / 100

        print(
            f"{cols_cnt:<12} | {format_duration(duration):<14} | "
            f"{len(upgrade_ddls)} ALTER Statements"
        )

    print("=" * 65 + "\n")


# 3. Unit of Work & Identity Map Transaction Benchmark
async def run_unit_of_work_benchmark():
    print("=" * 65)
    print(" 🚀 3. UNIT OF WORK & IDENTITY MAP BENCHMARK")
    print("=" * 65)

    engine = create_engine("sqlite:///:memory:")
    await engine.execute("CREATE TABLE authors (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255), email VARCHAR(255));")

    sizes = [100, 1000, 5000]
    print(f"{'Records':<14} | {'Commit Time':<14} | {'Operations':<18}")
    print("-" * 65)

    for count in sizes:
        uow = UnitOfWork(engine)
        
        t0 = time.perf_counter()
        async with uow.begin():
            for i in range(count):
                author = Author(name=f"User {i}", email=f"user{i}@test.com")
                uow.register_new(author)

        duration = time.perf_counter() - t0
        print(f"{count:<14,d} | {format_duration(duration):<14} | Atomic Transaction")

    print("=" * 65 + "\n")


# 4. N+1 Relation Resolution Benchmark
async def run_n1_relation_benchmark():
    print("=" * 65)
    print(" 🚀 4. N+1 QUERY RESOLUTION BENCHMARK (Batcher vs Sequential)")
    print("=" * 65)

    engine = create_engine("sqlite:///:memory:")
    await engine.execute("CREATE TABLE authors (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255), email VARCHAR(255));")
    await engine.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY AUTOINCREMENT, title VARCHAR(255), views INTEGER, author_id INTEGER);")

    # Seed 100 authors and 500 posts
    for a_id in range(1, 101):
        await engine.execute("INSERT INTO authors (id, name, email) VALUES (?, ?, ?)", (a_id, f"Author {a_id}", f"a{a_id}@test.com"))
        for p_i in range(5):
            await engine.execute("INSERT INTO posts (title, views, author_id) VALUES (?, ?, ?)", (f"Post {p_i} by {a_id}", 100 * p_i, a_id))

    # Test Sequential N+1 Access
    t0 = time.perf_counter()
    authors = await Author.all()
    seq_post_count = 0
    for author in authors:
        posts = await Post.where(author_id=author.id).all()
        seq_post_count += len(posts)
    seq_time = time.perf_counter() - t0

    # Test Auto-Batcher / Eager Loading
    t0 = time.perf_counter()
    batch_authors = await Author.all()
    
    async def fetch_posts_batch(author_ids):
        all_posts = await Post.where(author_id__in=author_ids).all()
        grouped = {}
        for p in all_posts:
            grouped.setdefault(p.author_id, []).append(p)
        return grouped

    batcher = DeferredAutoBatcher(fetch_posts_batch)
    batch_tasks = [batcher.load(a.id) for a in batch_authors]
    batch_results = await asyncio.gather(*batch_tasks)
    batch_post_count = sum(len(res) for res in batch_results)
    batch_time = time.perf_counter() - t0

    speedup = seq_time / batch_time if batch_time > 0 else 1.0

    print(f"Sequential N+1 Time (100 Queries) : {format_duration(seq_time)}")
    print(f"Auto-Batcher Time  (1 Batch Query) : {format_duration(batch_time)}")
    print(f"Performance Speedup                : {speedup:.1f}x FASTER!")
    print("=" * 65 + "\n")


def main():
    run_hydration_benchmark()
    run_schema_diff_benchmark()
    asyncio.run(run_unit_of_work_benchmark())
    asyncio.run(run_n1_relation_benchmark())

if __name__ == "__main__":
    main()
