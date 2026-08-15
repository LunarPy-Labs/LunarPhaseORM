import pytest
import pytest_asyncio
import sys
import os
from unittest.mock import patch
from lunarphase.core.state import PyStateTracker, create_state_tracker
import lunarphase.query.builder as qb_module
import lunarphase.migrations.diff as diff_module
import lunarphase.core.model as model_module
import lunarphase.core.state as state_module
from lunarphase import (
    Model,
    PrimaryKeyField,
    StringField,
    IntegerField,
    FloatField,
    BooleanField,
    DateTimeField,
    JSONField,
    HasOne,
    BelongsTo,
    HasMany,
    UnitOfWork,
    IdentityMap,
    create_engine,
    get_engine,
    SQLiteEngine,
)
from lunarphase.cli.main import run_cli

class CategoryCov(Model):
    __tablename__ = "cat_cov_base"
    id = PrimaryKeyField()
    name = StringField()

class ProfileHasOne(Model):
    __tablename__ = "profiles_has_one"
    id = PrimaryKeyField()
    bio = StringField()
    user_id = IntegerField()
    user = BelongsTo(lambda: UserHasOne, foreign_key="user_id")

class UserHasOne(Model):
    __tablename__ = "users_has_one"
    id = PrimaryKeyField()
    name = StringField()
    score = FloatField(default=0.0)
    is_vip = BooleanField(default=False)
    created_at = DateTimeField()
    data = JSONField()
    profile = HasOne(ProfileHasOne, foreign_key="user_id")
    items = HasMany(ProfileHasOne, foreign_key="user_id")

class CategoryBuilder(Model):
    __tablename__ = "cat_builder"
    id = PrimaryKeyField()
    name = StringField()

class CategoryModelTest(Model):
    __tablename__ = "cat_model_test"
    id = PrimaryKeyField()
    name = StringField()

class CategoryDiffTest(Model):
    __tablename__ = "cat_diff_test"
    id = PrimaryKeyField()

@pytest_asyncio.fixture(autouse=True)
async def fresh_engine(tmp_path):
    db_file = str(tmp_path / "test_cov.db")
    engine = create_engine(f"sqlite:///{db_file}")
    yield engine
    await engine.disconnect()

@pytest.mark.asyncio
async def test_pystate_tracker_fallback():
    tracker = PyStateTracker()
    tracker.set_initial_state({"a": 1, "b": "hello"})
    assert not tracker.is_dirty()
    assert tracker.dirty_fields() == []

    tracker.set_field("a", 2)
    assert tracker.is_dirty()
    assert tracker.dirty_fields() == ["a"]
    assert tracker.get_dirty_changes() == {"a": 2}

    assert tracker.get_field("b") == "hello"
    assert tracker.get_current_dict() == {"a": 2, "b": "hello"}

    tracker.hydrate_snapshot()
    assert not tracker.is_dirty()

    with patch.object(state_module, "HAS_RUST_CORE", False):
        py_tr = create_state_tracker()
        assert isinstance(py_tr, PyStateTracker)

@pytest.mark.asyncio
async def test_has_one_relationship(fresh_engine):
    await fresh_engine.execute("""
        CREATE TABLE IF NOT EXISTS users_has_one (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            score REAL,
            is_vip BOOLEAN,
            created_at DATETIME,
            data JSON
        );
    """)
    await fresh_engine.execute("""
        CREATE TABLE IF NOT EXISTS profiles_has_one (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bio VARCHAR(255),
            user_id INTEGER
        );
    """)

    user = await UserHasOne.create(name="Alex", score=9.5, is_vip=True)
    profile = await ProfileHasOne.create(bio="Developer bio", user_id=user.id)

    fetched_profile = await user.profile
    assert fetched_profile is not None
    assert fetched_profile.bio == "Developer bio"

    fetched_user = await profile.user
    assert fetched_user is not None
    assert fetched_user.name == "Alex"

    # Eager loading test
    users = await UserHasOne.where(id=user.id).with_relations("items").all()
    assert len(users) == 1
    assert hasattr(users[0], "_items_cached")

@pytest.mark.asyncio
async def test_relations_empty_cases():
    unsaved_user = UserHasOne(name="Unsaved")
    res_items = await unsaved_user.items
    assert res_items == []

    res_profile = await unsaved_user.profile
    assert res_profile is None

    empty_prof = ProfileHasOne(bio="No user")
    res_parent = await empty_prof.user
    assert res_parent is None

@pytest.mark.asyncio
async def test_query_builder_python_fallback_and_methods(fresh_engine):
    await fresh_engine.execute("""
        CREATE TABLE IF NOT EXISTS cat_builder (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255)
        );
    """)
    await CategoryBuilder.create(name="Tech")
    await CategoryBuilder.create(name="Science")

    with patch.object(qb_module, "HAS_RUST_COMPILER", False):
        builder = CategoryBuilder.where(name="Tech").select("id", "name")
        items = await builder.all()
        assert len(items) == 1
        assert items[0].name == "Tech"

        c = await CategoryBuilder.where(id=1).count()
        assert c == 1

        first_item = await CategoryBuilder.where(id=999).first()
        assert first_item is None

@pytest.mark.asyncio
async def test_model_methods_and_repr(fresh_engine):
    await fresh_engine.execute("""
        CREATE TABLE IF NOT EXISTS cat_model_test (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255)
        );
    """)

    cat = CategoryModelTest(name="Shorts")
    assert repr(cat) == "<CategoryModelTest id=None>"
    assert await cat.delete() is False

    cat_created = await CategoryModelTest.create(name="Shirts")
    assert repr(cat_created) == f"<CategoryModelTest id={cat_created.id}>"

    # Save non-dirty returns False
    assert await cat_created.save() is False

    with patch.object(model_module, "HAS_RUST_COMPILER", False):
        cat_fb = await CategoryModelTest.create(name="Books")
        assert cat_fb.id is not None

        cat_fb.name = "Novels"
        saved = await cat_fb.save()
        assert saved is True

        deleted = await cat_fb.delete()
        assert deleted is True

@pytest.mark.asyncio
async def test_migration_diff_python_fallback(fresh_engine):
    with patch.object(diff_module, "HAS_RUST_DIFF", False):
        up, down = await diff_module.MigrationDiff.generate_diff([CategoryDiffTest])
        assert len(up) > 0

@pytest.mark.asyncio
async def test_engine_disconnect_and_types():
    eng = SQLiteEngine("sqlite:///:memory:")
    await eng.connect()
    assert eng.dialect == "sqlite"
    await eng.disconnect()
    await eng.disconnect()

    eng_pg = create_engine("postgresql://localhost/db")
    assert eng_pg.dialect in ["sqlite", "postgres"]

@pytest.mark.asyncio
async def test_identity_map_and_uow_edge_cases():
    imap = IdentityMap()
    cat = CategoryCov(name="Test")
    imap.register(cat)
    assert imap.get(CategoryCov, 1) is None

    cat.id = 1
    imap.register(cat)
    assert imap.get(CategoryCov, 1) is cat

    imap.remove(cat)
    assert imap.get(CategoryCov, 1) is None

    imap.register(cat)
    imap.clear()
    assert imap.get(CategoryCov, 1) is None

    # UoW register dirty and deleted
    uow = UnitOfWork()
    c2 = CategoryCov(name="Dirty")
    c2.id = 10
    uow.register_dirty(c2)
    assert c2 in uow.dirty_objects

    uow.register_deleted(c2)
    assert c2 in uow.deleted_objects

@pytest.mark.asyncio
async def test_cli_commands(tmp_path, fresh_engine):
    with patch.object(sys, "argv", ["lunarphase", "status"]):
        await run_cli()

    with patch.object(sys, "argv", ["lunarphase", "make:migration", "init"]):
        await run_cli()

    with patch.object(sys, "argv", ["lunarphase", "migrate"]):
        await run_cli()

    with patch.object(sys, "argv", ["lunarphase", "rollback"]):
        await run_cli()

@pytest.mark.asyncio
async def test_field_descriptor_null_ops():
    cat = CategoryCov(name="NullTest")
    assert (CategoryCov.name == None).op == "IS"
    assert (CategoryCov.name != None).op == "IS NOT"
    assert (CategoryCov.name.is_null()).op == "IS"
    assert (CategoryCov.name.is_not_null()).op == "IS NOT"
    assert (CategoryCov.name.like("%test%")).op == "LIKE"
    assert (CategoryCov.name.in_(["a", "b"])).op == "IN"
