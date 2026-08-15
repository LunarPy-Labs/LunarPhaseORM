import pytest
import asyncio
from lunarphase import Model, StringField, IntegerField, PrimaryKeyField, HasMany, BelongsTo, create_engine
from lunarphase.query.batcher import DeferredAutoBatcher

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

@pytest.mark.asyncio
async def test_deferred_auto_batcher():
    fetch_count = 0

    async def mock_batch_fetch(keys):
        nonlocal fetch_count
        fetch_count += 1
        return {k: [f"Item-{k}"] for k in keys}

    batcher = DeferredAutoBatcher(mock_batch_fetch)

    # Concurrently request multiple keys
    r1, r2, r3 = await asyncio.gather(
        batcher.load(1),
        batcher.load(2),
        batcher.load(3)
    )

    assert r1 == ["Item-1"]
    assert r2 == ["Item-2"]
    assert r3 == ["Item-3"]
    assert fetch_count == 1 # Only 1 single batch query executed for 3 items!

@pytest.mark.asyncio
async def test_has_many_belongs_to_relations():
    engine = create_engine("sqlite:///:memory:")
    await engine.execute("""
        CREATE TABLE authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255)
        );
    """)
    await engine.execute("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(255),
            author_id INTEGER
        );
    """)

    author = await Author.create(name="Jane Doe")
    p1 = await Post.create(title="Post 1", author_id=author.id)
    p2 = await Post.create(title="Post 2", author_id=author.id)

    author_posts = await author.posts
    assert len(author_posts) == 2
    assert {p.title for p in author_posts} == {"Post 1", "Post 2"}

    post_author = await p1.author
    assert post_author is not None
    assert post_author.name == "Jane Doe"
