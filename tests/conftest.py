import pytest

from app import create_app
from app.database.db import Database


@pytest.fixture
def db():
    database = Database(":memory:")
    database.init_schema()
    return database


@pytest.fixture
def client():
    app = create_app({"TESTING": True, "DATABASE": ":memory:", "SECRET_KEY": "test"})
    with app.test_client() as test_client:
        with test_client.session_transaction() as sess:
            sess["csrf_token"] = "tok"
        yield test_client
