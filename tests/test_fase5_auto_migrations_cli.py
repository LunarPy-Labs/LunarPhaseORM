import os
import shutil
import pytest
from lunarphase import Model, StringField, IntegerField, PrimaryKeyField, create_engine
from lunarphase.migrations.runner import MigrationRunner

class Article(Model):
    __tablename__ = "articles"
    id = PrimaryKeyField()
    title = StringField()
    views = IntegerField(default=0)

@pytest.mark.asyncio
async def test_auto_migration_generation_and_execution(tmp_path):
    mig_dir = str(tmp_path / "test_migrations")
    engine = create_engine("sqlite:///:memory:")
    runner = MigrationRunner(migrations_dir=mig_dir)

    # 1. Generate migration script
    filepath = await runner.make_migration("create_articles_table", [Article])
    assert filepath is not None
    assert os.path.exists(filepath)

    # 2. Run migration upgrade
    await runner.migrate()

    # Verify table exists in DB by inserting article
    art = await Article.create(title="Hello LunarPhaseORM", views=100)
    assert art.id is not None

    # 3. Rollback migration
    await runner.rollback()

    # Verify table dropped after rollback
    with pytest.raises(Exception):
        await Article.all()
