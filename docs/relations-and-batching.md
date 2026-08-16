# Relations & Auto-Batching Engine

This document describes relationship descriptors (`HasMany`, `BelongsTo`, `HasOne`), eager loading, and the `DeferredAutoBatcher` micro-task scheduling algorithm.

---

## Defining Relationships

Relationships are declared on models using relationship descriptors:

```python
from lunarphase import Model, PrimaryKeyField, StringField, IntegerField, HasMany, BelongsTo

class Author(Model):
    __tablename__ = "authors"
    id = PrimaryKeyField()
    name = StringField()
    posts = HasMany(lambda: Post, foreign_key="author_id")

class Post(Model):
    __tablename__ = "posts"
    id = PrimaryKeyField()
    title = StringField()
    author_id = IntegerField()
    author = BelongsTo(Author, foreign_key="author_id")
```

---

## The N+1 Problem & Solution Algorithm

When accessing relationship attributes inside an async iteration loop, naive ORM implementations issue a separate SQL `SELECT` for each parent model ($N+1$ queries):

```python
# Naive execution issuing N+1 queries:
authors = await Author.all()
for author in authors:
    posts = await author.posts # Issues SELECT * FROM posts WHERE author_id = ? for EVERY loop!
```

### `DeferredAutoBatcher` Execution Cycle

LunarPhaseORM resolves $N+1$ queries by scheduling relationship loading tasks into the `asyncio` event loop micro-task queue via `loop.call_soon()`:

```
Step 1: Loop Execution
  for author in authors:
      posts = await author.posts ──► Registers key into DeferredAutoBatcher queue

Step 2: Micro-Task Scheduler (loop.call_soon)
  Event loop yields control to micro-task ──► Triggers _flush_batch()

Step 3: Single Batch Query Execution
  Executes ONE SQL query: SELECT * FROM posts WHERE author_id IN (1, 2, 3, ... N);

Step 4: Rust Key Deduplication & Result Distribution
  BatchAggregator deduplicates keys via FxHashSet<i64> ──► Resolves Future for each author
```

---

## Eager Loading (`with_relations`)

Relationships can also be eagerly fetched in advance using `with_relations()`:

```python
# Fetches authors and eagerly loads all related posts in a single batch query
authors = await Author.with_relations("posts").all()

for author in authors:
    for post in author.posts:
        print(post.title)
```
