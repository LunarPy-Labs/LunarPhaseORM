import pytest
from lunarphase import Model, StringField, IntegerField, PrimaryKeyField, UnitOfWork, IdentityMap, create_engine

class Account(Model):
    __tablename__ = "accounts"
    id = PrimaryKeyField()
    holder = StringField()
    balance = IntegerField()

@pytest.mark.asyncio
async def test_dirty_tracking_snapshot_diff():
    engine = create_engine("sqlite:///:memory:")
    await engine.execute("""
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            holder VARCHAR(255),
            balance INTEGER
        );
    """)

    acc = await Account.create(holder="Alice", balance=1000)
    assert not acc.is_dirty

    # Mutate field
    acc.balance = 1200
    assert acc.is_dirty
    assert acc.get_dirty_changes() == {"balance": 1200} # Only balance is dirty

    # Save updates dirty fields only
    saved = await acc.save()
    assert saved is True
    assert not acc.is_dirty

    # Save when not dirty skips SQL execution
    saved_again = await acc.save()
    assert saved_again is False

@pytest.mark.asyncio
async def test_unit_of_work_and_identity_map():
    engine = create_engine("sqlite:///:memory:")
    await engine.execute("""
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            holder VARCHAR(255),
            balance INTEGER
        );
    """)

    uow = UnitOfWork()
    async with uow.begin():
        acc1 = Account(holder="Bob", balance=500)
        acc2 = Account(holder="Charlie", balance=800)
        uow.register_new(acc1)
        uow.register_new(acc2)

    assert acc1.id is not None
    assert acc2.id is not None
    assert await Account.where(holder="Bob").first() is not None

    # Rollback behavior check
    try:
        async with uow.begin():
            acc3 = Account(holder="Dave", balance=100)
            uow.register_new(acc3)
            raise ValueError("Simulated transaction crash")
    except ValueError:
        pass

    assert await Account.where(holder="Dave").first() is None
