import pytest
import pytest_asyncio
import re
from lunarphase import (
    Model,
    PrimaryKeyField,
    StringField,
    IntegerField,
    BooleanField,
    create_engine,
    get_engine,
    SQLiteEngine,
    MySQLEngine,
    PostgresEngine,
)
from lunarphase.migrations.runner import MigrationRunner
from lunarphase.migrations.schema import SchemaExtractor
from lunarphase.migrations.diff import MigrationDiff


class User(Model):
    __tablename__ = "users"
    id = PrimaryKeyField()
    name = StringField(nullable=False)
    age = IntegerField(default=18)
    is_active = BooleanField(default=True)


class Post(Model):
    __tablename__ = "posts"
    id = PrimaryKeyField()
    user_id = IntegerField()
    title = StringField()


# ===================================================================
# 1. ENGINE INSTANTIATION & DIALECT RESOLUTION TESTS
# ===================================================================

def test_engine_factory_dialect_resolution():
    """Verify that create_engine returns correct engine subclass and dialect string."""
    sqlite_eng = create_engine("sqlite:///:memory:")
    assert isinstance(sqlite_eng, SQLiteEngine)
    assert sqlite_eng.dialect == "sqlite"

    mysql_eng = create_engine("mysql://root:secret@localhost:3306/my_database")
    assert isinstance(mysql_eng, MySQLEngine)
    assert mysql_eng.dialect == "mysql"
    assert mysql_eng.host == "localhost"
    assert mysql_eng.port == 3306
    assert mysql_eng.user == "root"
    assert mysql_eng.password == "secret"
    assert mysql_eng.db == "my_database"

    pg_eng = create_engine("postgres://postgres:secret@localhost:5432/my_database")
    assert isinstance(pg_eng, PostgresEngine)
    assert pg_eng.dialect == "postgres"

    pgsql_eng = create_engine("postgresql://postgres:secret@localhost:5432/my_database")
    assert isinstance(pgsql_eng, PostgresEngine)
    assert pgsql_eng.dialect == "postgres"


# ===================================================================
# 2. PLACEHOLDER & SQL CONVERSION TESTS
# ===================================================================

def test_postgres_placeholder_conversion():
    """Verify PostgresEngine converts ? placeholders into $1, $2, $3..."""
    pg_eng = PostgresEngine("postgres://user:pass@localhost/db")
    
    sql_input = "SELECT * FROM users WHERE age >= ? AND is_active = ? AND name = ?;"
    converted = pg_eng._convert_placeholders(sql_input)
    assert converted == "SELECT * FROM users WHERE age >= $1 AND is_active = $2 AND name = $3;"


# ===================================================================
# 3. SCHEMA EXTRACTION & MIGRATION DIFF TESTS
# ===================================================================

@pytest.mark.asyncio
async def test_schema_extractor_model_and_diff():
    """Verify SchemaExtractor extracts field metadata and generates DDL for models."""
    model_schema = SchemaExtractor.extract_from_model(User)
    assert model_schema["table_name"] == "users"
    assert "name" in model_schema["fields"]
    assert model_schema["fields"]["name"]["nullable"] is False

    create_up, create_down = await MigrationDiff.generate_diff([User, Post])
    assert len(create_up) == 2
    assert len(create_down) == 2
    assert "CREATE TABLE" in create_up[0]
    assert "DROP TABLE" in create_down[0]


# ===================================================================
# 4. END-TO-END MIGRATION & CRUD TEST (SQLITE ENGINE)
# ===================================================================

@pytest.mark.asyncio
async def test_sqlite_e2e_migration_and_crud(tmp_path):
    mig_dir = str(tmp_path / "sqlite_migrations")
    engine = create_engine("sqlite:///:memory:")
    runner = MigrationRunner(migrations_dir=mig_dir)

    # 1. Make Migration
    mig_file = await runner.make_migration("init_sqlite_schema", [User])
    assert mig_file is not None

    # 2. Apply Migration
    await runner.migrate()

    # 3. CRUD Operations
    u1 = await User.create(name="Alice", age=25)
    assert u1.id is not None

    u2 = await User.create(name="Bob", age=30)
    assert u2.id is not None

    # Filter & Count
    adults = await User.where(User.age >= 21).all()
    assert len(adults) == 2

    cnt = await User.where(User.age >= 21).count()
    assert cnt == 2

    # Update (Dirty tracking)
    u1.age = 26
    await u1.save()

    updated_u1 = await User.where(name="Alice").first()
    assert updated_u1.age == 26

    # Delete
    await u2.delete()
    cnt_after = await User.where().count()
    assert cnt_after == 1

    # 4. Rollback Migration
    await runner.rollback()

    await engine.disconnect()
