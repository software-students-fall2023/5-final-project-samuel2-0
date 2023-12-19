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
    app.app.config["TESTING"] = True
    with app.app.test_client() as client:
        yield client


def test_welcome_route(client):
    """
    testing the landing page
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome" in response.data

