import pytest
import pytest_asyncio
from lunarphase import Model, StringField, IntegerField, PrimaryKeyField, create_engine
from lunarphase.core.ast import BinaryOp, ColumnRef, Literal

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    create_engine("sqlite:///:memory:")

class User(Model):
    __tablename__ = "users"
    id = PrimaryKeyField()
    name = StringField()
    age = IntegerField()

@pytest.mark.asyncio
async def test_field_descriptor_operator_overloading():
    op = User.age > 18
    assert isinstance(op, BinaryOp)
    assert op.op == ">"
    assert isinstance(op.left, ColumnRef)
    assert op.left.column_name == "age"
    assert isinstance(op.right, Literal)
    assert op.right.value == 18

@pytest.mark.asyncio
async def test_model_crud():
    engine = create_engine("sqlite:///:memory:")
    await engine.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            age INTEGER
        );
    """)

    # Create
    user = await User.create(name="Alice", age=25)
    assert user.id is not None
    assert user.name == "Alice"
    assert user.age == 25
    assert not user.is_dirty

    # Read
    fetched = await User.where(id=user.id).first()
    assert fetched is not None
    assert fetched.name == "Alice"

    # Update
    fetched.age = 26
    assert fetched.is_dirty
    saved = await fetched.save()
    assert saved is True
    assert not fetched.is_dirty

    # Delete
    deleted = await fetched.delete()
    assert deleted is True
    assert await User.where(id=user.id).first() is None
