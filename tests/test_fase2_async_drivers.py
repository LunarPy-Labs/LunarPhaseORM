import pytest
import pytest_asyncio
from lunarphase import Model, StringField, IntegerField, PrimaryKeyField, create_engine

class Product(Model):
    __tablename__ = "products"
    id = PrimaryKeyField()
    name = StringField()
    price = IntegerField()
    category = StringField()

@pytest.mark.asyncio
async def test_query_chaining():
    engine = create_engine("sqlite:///:memory:")
    await engine.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            price INTEGER,
            category VARCHAR(255)
        );
    """)

    await Product.create(name="Laptop", price=1000, category="Electronics")
    await Product.create(name="Mouse", price=25, category="Electronics")
    await Product.create(name="Desk", price=300, category="Furniture")
    await Product.create(name="Chair", price=150, category="Furniture")

    # Test where & order_by & limit
    items = await Product.where(Product.price > 100).order_by("price", "desc").limit(2).all()
    assert len(items) == 2
    assert items[0].name == "Laptop"
    assert items[1].name == "Desk"

    # Test count & exists
    c = await Product.where(category="Electronics").count()
    assert c == 2

    exists = await Product.where(name="Laptop").exists()
    assert exists is True

    # Test pagination
    paginated, total, pages = await Product.where(Product.price > 10).paginate(page=1, per_page=2)
    assert len(paginated) == 2
    assert total == 4
    assert pages == 2
