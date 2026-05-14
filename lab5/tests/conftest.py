import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import app
from models.book import books_db


@pytest.fixture(scope="session")
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clean_db():
    books_db.clear()
    yield
    books_db.clear()
