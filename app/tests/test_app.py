import sys
from unittest.mock import Mock
import pytest
import pymongo


sys.path.append("..")

from app import app

@pytest.fixture
def client():
    """
    Creates a flask testing client to simmulate calls to the web-app.
    """
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

