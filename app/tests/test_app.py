import sys
from unittest.mock import Mock
import tempfile
import os
import pytest
import mongomock
import pymongo
from bson import ObjectId
import json 

sys.path.append("..")

from app import app, connection_db
from mongomock import MongoClient

@pytest.fixture
def client():

    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            connection_db()
        yield client

@pytest.fixture
def mocked_mongo_client(monkeypatch):
    mock_client = MongoClient()
    monkeypatch.setattr("app.connection_db", lambda: mock_client)
    return mock_client

def test_connection_db(monkeypatch):
    mocked_mongo_client = mongomock.MongoClient('localhost', 27017)
    monkeypatch.setattr('app.connection_db', lambda: mocked_mongo_client)  
    assert isinstance(mocked_mongo_client, mongomock.MongoClient)

def test_welcome_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome' in response.data   

def test_login_route(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_signup_route(client):
    response = client.get('/signup')
    assert response.status_code == 200
    assert b'Sign Up' in response.data

def test_logout_route(client):
    response = client.get('/logout')
    assert response.status_code == 302 

def test_inbox_route_fail(client):
    response = client.get('/inbox')
    assert response.status_code == 302 

def test_send_letter_route(client):
    response = client.get('/send_letter')
    assert response.status_code == 401 

def test_personal_info_route(client):
    response = client.get('/personal_info')
    assert response.status_code == 302 

def test_my_friends_route(client):
    response = client.get('/my_friends')
    assert response.status_code == 404 

def test_find_friends_route(client):
    response = client.get('/find_friends')
    assert response.status_code == 404 

def test_add_friend_route(client):
    response = client.get('/add_friend')
    assert response.status_code == 404

def test_send_letter_fail(client, mocked_mongo_client):
    sender_id = str(ObjectId())
    receiver_id = str(ObjectId())
    letter_text = "Hello, this is a test letter!"

    with app.test_client() as client:
        with client.session_transaction() as session:
            session["userid"] = sender_id
    response = client.post(
        '/send_letter',
        data={'receiver_id': receiver_id, 'letter_text': letter_text}
    )
    assert response.status_code == 400, f"Expected status code 400, but got {response.status_code}"

def test_add_to_friends_fail(client, mocked_mongo_client):
    friend_id = str(ObjectId())
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["userid"] = "some_user_id"
    response = client.post('/add_to_friends', data={'friendId': friend_id})
    assert response.status_code == 500, f"Expected status code 500, but got {response.status_code}"

def test_logout(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = "some_user_id"
        session["email"] = "user@example.com"
        session["username"] = "testuser"

    response = client.get('/logout')
    assert response.status_code == 302

    with client.session_transaction() as session:
        assert "userid" not in session
        assert "email" not in session
        assert "username" not in session

def test_inbox(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    def mock_find_one(self, query):
        if "userid" in session:
            return {"_id": ObjectId(session["userid"]), "username": "testuser"}
        return None
    monkeypatch.setattr("pymongo.collection.Collection.find_one", mock_find_one)
    response = client.get('/inbox')
    assert response.status_code == 200

def test_personal_info(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    def mock_find_one(self, query):
        if "userid" in session:
            return {"_id": ObjectId(session["userid"]), "username": "testuser"}
        return None
    monkeypatch.setattr("pymongo.collection.Collection.find_one", mock_find_one)
    response = client.get('/personal_info')
    assert response.status_code == 200

 
def test_signup(client, monkeypatch):
    signup_data = {
        '_id': str(ObjectId()),
        'email': 'testtest@gmail.com',
        'username': 'test',
        'password': '12345',
        'first_name': 'test',
        'last_name': 'tring',
        'name': 'tring test',
        'languages': ['English'],  
        'interests': ['Coding'],   
        'about_me': 'Lindo',
        'age': '18',
        'country': 'Afghanistan'
    }
    def mock_insert_one(self, document):
        return Mock(inserted_id=signup_data['_id'])
    monkeypatch.setattr("pymongo.collection.Collection.insert_one", mock_insert_one)
    response = client.post('/signup', data=signup_data)
    assert response.status_code == 302

def test_mock_login(client, monkeypatch):
    login_data = {
        'email': 'tring@gmail.com',
        'password': '12345',
    }
    def mock_find_one(self, query):
        return {
            '_id': ObjectId('6581038e3fe4cc32f9584bb7'),
            'email': 'tring@gmail.com',
            'username': 'tring',
            'password': 'hashed_password', 
            
        }
    monkeypatch.setattr("pymongo.collection.Collection.find_one", mock_find_one)
    response = client.post('/login', data=login_data)
    assert response.status_code == 401 


def test_login_user_not_found(client, monkeypatch):
    login_data = {
        'email': 'nonexistent@gmail.com',
        'password': 'password',
    }

    def mock_find_one(self, query):
        return None
    monkeypatch.setattr("pymongo.collection.Collection.find_one", mock_find_one)
    response = client.post('/login', data=login_data)
    assert response.status_code == 401  
    response_data = json.loads(response.data)
    assert response_data['error'] == 'User not found'


   

