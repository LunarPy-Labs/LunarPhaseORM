# Relations & Auto-Batching Tutorial

This document covers relationship descriptors (`HasMany`, `BelongsTo`, `HasOne`), eager loading, and the `DeferredAutoBatcher` micro-task scheduling engine.

---

## 1. Declaring Relationships

Declare model relationships using relationship descriptors:

```python
from lunarphase import Model, PrimaryKeyField, StringField, IntegerField, HasMany, BelongsTo, HasOne

class Author(Model):
    __tablename__ = "authors"

    id = PrimaryKeyField()
    name = StringField()

    # One-to-Many: Author has many Posts
    posts = HasMany(lambda: Post, foreign_key="author_id")

    # One-to-One: Author has one Profile
    profile = HasOne(lambda: Profile, foreign_key="author_id")

class Post(Model):
    __tablename__ = "posts"

    id = PrimaryKeyField()
    author_id = IntegerField()
    title = StringField()

    # Many-to-One: Post belongs to Author
    author = BelongsTo(Author, foreign_key="author_id")

class Profile(Model):
    __tablename__ = "profiles"

    id = PrimaryKeyField()
    author_id = IntegerField()
    bio = StringField()
```

---

## 2. Relationship Access Syntax

### 2.1 Lazy Relationship Loading

Accessing a relationship attribute asynchronously loads the related model(s):

```python
# Accessing HasMany
author = await Author.where(id=1).first()
posts = await author.posts  # Returns List[Post]

# Accessing BelongsTo
post = await Post.where(id=10).first()
author = await post.author  # Returns Optional[Author]

# Accessing HasOne
author = await Author.where(id=1).first()
profile = await author.profile  # Returns Optional[Profile]
```

---

## 3. The N+1 Problem & Auto-Batching Engine

In traditional ORMs, accessing relationships inside a loop causes $N+1$ queries:

```python
# Traditional ORM: Executes 1 SELECT for authors, then N SELECT queries inside loop!
authors = await Author.all()
for author in authors:
    posts = await author.posts  # N+1 bottleneck!
```

### How `DeferredAutoBatcher` Resolves N+1 Queries

LunarPhaseORM uses **Event Loop Micro-Task Deferred Batching**. When accessing `await author.posts` inside a loop, tasks are registered into a micro-task queue via `asyncio.get_running_loop().call_soon()`.

```python
async def auto_batching_tutorial():
    authors = await Author.all()

    # Accessing author.posts across loop iterations registers keys into DeferredAutoBatcher.
    # The event loop micro-task flushes them into a SINGLE query:
    # SELECT * FROM posts WHERE author_id IN (1, 2, 3, 4, 5...);
    for author in authors:
        posts = await author.posts
        print(f"Author {author.name} has {len(posts)} posts.")
```

---

## 4. Eager Loading Syntax (`with_relations`)

If you prefer to pre-fetch relationships upfront, use `.with_relations()`:

```python
async def eager_loading_tutorial():
    # Eagerly loads all related posts in 1 query before entering the loop
    authors = await Author.with_relations("posts").all()

    for author in authors:
        # Accessing author.posts now reads directly from memory!
        for post in author.posts:
            print(f"- {author.name}: {post.title}")
```
