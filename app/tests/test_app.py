import sys
from unittest.mock import Mock
import pytest
import mongomock
import pymongo
from bson import ObjectId
import json

sys.path.append("..")

from app import app, connection_db, get_all_users
from mongomock import MongoClient


@pytest.fixture
def client():
    app.config["TESTING"] = True
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
    mocked_mongo_client = mongomock.MongoClient("localhost", 27017)
    monkeypatch.setattr("app.connection_db", lambda: mocked_mongo_client)
    assert isinstance(mocked_mongo_client, mongomock.MongoClient)


def test_welcome_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome" in response.data


def test_login_route(client, monkeypatch):
    user_id = str(ObjectId())
    monkeypatch.setattr(
        "app.db.users.find_one",
        lambda query: {
            "_id": ObjectId(user_id),
            "email": "test@example.com",
            "password": "password",
        },
    )
    response = client.post(
        "/login", data={"email": "test@example.com", "password": "wrong_password"}
    )
    assert response.status_code == 401

    response = client.post(
        "/login", data={"email": "nonexistent@example.com", "password": "password"}
    )
    assert response.status_code == 401


def test_signup_route(client):
    response = client.get("/signup")
    assert response.status_code == 200
    assert b"Sign Up" in response.data


def test_logout_route(client):
    response = client.get("/logout")
    assert response.status_code == 302


def test_inbox_route_fail(client):
    response = client.get("/inbox")
    assert response.status_code == 302


def test_send_letter_route(client):
    response = client.get("/send_letter")
    assert response.status_code == 401


def test_personal_info_route(client):
    response = client.get("/personal_info")
    assert response.status_code == 302


def test_my_friends_route(client):
    response = client.get("/my_friends")
    assert response.status_code == 404


def test_find_friends_route(client):
    response = client.get("/find_friends")
    assert response.status_code == 404


def test_add_friend_route(client):
    response = client.get("/add_friend")
    assert response.status_code == 404


def test_send_letter_fail(client, mocked_mongo_client):
    sender_id = str(ObjectId())
    receiver_id = str(ObjectId())
    letter_text = "Hello, this is a test letter!"
    with app.test_client() as client:
        with client.session_transaction() as session:
            session["userid"] = sender_id
    response = client.post(
        "/send_letter", data={"receiver_id": receiver_id, "letter_text": letter_text}
    )
    assert (
        response.status_code == 500
    ), f"Expected status code 500, but got {response.status_code}"


def test_add_to_friends_fail(client, mocked_mongo_client):
    friend_id = str(ObjectId())
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["userid"] = "some_user_id"
    response = client.post("/add_to_friends", data={"friendId": friend_id})
    assert (
        response.status_code == 500
    ), f"Expected status code 500, but got {response.status_code}"


def test_logout(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = "some_user_id"
        session["email"] = "user@example.com"
        session["username"] = "testuser"

    response = client.get("/logout")
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
    response = client.get("/inbox")
    assert response.status_code == 200


def test_personal_info(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())

    def mock_find_one(self, query):
        if "userid" in session:
            return {"_id": ObjectId(session["userid"]), "username": "testuser"}
        return None

    monkeypatch.setattr("pymongo.collection.Collection.find_one", mock_find_one)
    response = client.get("/personal_info")
    assert response.status_code == 200


def test_signup(client, monkeypatch):
    signup_data = {
        "_id": str(ObjectId()),
        "email": "testtest@gmail.com",
        "username": "test",
        "password": "12345",
        "first_name": "test",
        "last_name": "tring",
        "name": "tring test",
        "languages": ["English"],
        "interests": ["Coding"],
        "about_me": "Lindo",
        "age": "18",
        "country": "Afghanistan",
    }

    def mock_insert_one(self, document):
        return Mock(inserted_id=signup_data["_id"])

    monkeypatch.setattr("pymongo.collection.Collection.insert_one", mock_insert_one)
    response = client.post("/signup", data=signup_data)
    assert response.status_code == 302


def test_mock_login(client, monkeypatch):
    login_data = {
        "email": "tring@gmail.com",
        "password": "12345",
    }

    def mock_find_one(self, query):
        return {
            "_id": ObjectId("6581038e3fe4cc32f9584bb7"),
            "email": "tring@gmail.com",
            "username": "tring",
            "password": "hashed_password",
        }

    monkeypatch.setattr("pymongo.collection.Collection.find_one", mock_find_one)
    response = client.post("/login", data=login_data)
    assert response.status_code == 401


def test_login_user_not_found(client, monkeypatch):
    login_data = {
        "email": "nonexistent@gmail.com",
        "password": "password",
    }

    def mock_find_one(self, query):
        return None

    monkeypatch.setattr("pymongo.collection.Collection.find_one", mock_find_one)
    response = client.post("/login", data=login_data)
    assert response.status_code == 401
    response_data = json.loads(response.data)
    assert response_data["error"] == "User not found"


def test_remove_letter(client, monkeypatch):
    letter_id = str(ObjectId())
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    mock_delete_one = Mock()
    monkeypatch.setattr("pymongo.collection.Collection.delete_one", mock_delete_one)
    mock_delete_one.return_value.deleted_count = 1
    response = client.post(f"/inbox/{letter_id}")
    assert response.status_code == 302


def test_read_letter(client, monkeypatch):
    letter_id = str(ObjectId())
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    mock_find_one = Mock()
    monkeypatch.setattr("pymongo.collection.Collection.find_one", mock_find_one)
    mock_find_one.return_value = {"_id": ObjectId(letter_id), "text": "Test letter"}
    response = client.get(f"/read_letter/{letter_id}")
    assert response.status_code == 200


def test_personal_info(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())

    # Mock the user data in the database
    mock_find_one = Mock()
    monkeypatch.setattr("pymongo.collection.Collection.find_one", mock_find_one)
    mock_find_one.return_value = {"_id": ObjectId(), "username": "testuser"}

    # Mock the update_one operation to simulate successful update
    mock_update_one = Mock()
    monkeypatch.setattr("pymongo.collection.Collection.update_one", mock_update_one)

    response = client.post(
        "/personal_info",
        data={
            "country": "Country",
            "about_me": "About me",
            "age": "25",
            "languages": ["English", "Spanish"],
            "interests": ["Reading", "Traveling"],
        },
    )

    assert response.status_code == 302


def test_myprofile(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    mock_get_user = Mock()
    monkeypatch.setattr("app.get_user", mock_get_user)
    mock_get_user.return_value = {"_id": ObjectId(), "username": "testuser"}
    response = client.get("/profile")
    assert response.status_code == 200


def test_edit_profile(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    mock_get_user = Mock()
    monkeypatch.setattr("app.get_user", mock_get_user)
    mock_get_user.return_value = {"_id": ObjectId(), "username": "testuser"}
    response = client.get("/profile/edit_profile")
    assert response.status_code == 200


def test_update_profile(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    mock_get_user = Mock()
    monkeypatch.setattr("app.get_user", mock_get_user)
    mock_get_user.return_value = {
        "_id": ObjectId(),
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "age": "25",
        "country": "Testland",
    }

    mock_update_one = Mock()
    monkeypatch.setattr("pymongo.collection.Collection.update_one", mock_update_one)
    mock_update_one.return_value.modified_count = 1
    response = client.post(
        "/profile/edit_profile",
        data={
            "username": "newusername",
            "first_name": "New",
            "last_name": "Name",
            "age": "30",
            "country": "Newland",
        },
    )

    assert response.status_code == 200


def test_edit_interests(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())

    mock_get_user = Mock()
    monkeypatch.setattr("app.get_user", mock_get_user)
    mock_get_user.return_value = {
        "_id": ObjectId(),
        "username": "testuser",
        "interests": ["Reading", "Traveling"],
    }

    response = client.get("/profile/edit_interests")
    assert response.status_code == 200
    assert b"Edit Interests" in response.data


def test_update_interests(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())

    # Mock the get_user function to simulate successful user retrieval
    mock_get_user = Mock()
    monkeypatch.setattr("app.get_user", mock_get_user)
    user_id = ObjectId()
    mock_get_user.return_value = {
        "_id": user_id,
        "username": "testuser",
        "interests": ["Reading", "Traveling"],
    }

    new_interests = ["Hiking", "Cooking"]
    response = client.post(
        "/profile/edit_interests", data={"interests[]": new_interests}
    )

    assert response.status_code == 200
    assert b"Profile" in response.data


def test_edit_languages(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    mock_get_user = Mock()
    monkeypatch.setattr("app.get_user", mock_get_user)
    user_id = ObjectId()
    mock_get_user.return_value = {
        "_id": user_id,
        "username": "testuser",
        "languages": ["English", "French"],
    }
    response = client.get("/profile/edit_languages")
    assert response.status_code == 200
    assert b"Languages" in response.data
    assert b"English" in response.data
    assert b"French" in response.data


def test_update_languages(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())

    mock_get_user = Mock()
    monkeypatch.setattr("app.get_user", mock_get_user)
    user_id = ObjectId()
    mock_get_user.return_value = {
        "_id": user_id,
        "username": "testuser",
        "languages": ["English", "French"],
    }

    mock_update_one = Mock()
    monkeypatch.setattr("pymongo.collection.Collection.update_one", mock_update_one)

    response = client.post(
        "/profile/edit_languages", data={"languages[]": ["Spanish", "German"]}
    )

    assert response.status_code == 200
    assert b"Languages" in response.data
    assert b"Spanish" in response.data
    assert b"German" in response.data


def test_my_friends(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    mock_get_user = Mock()
    monkeypatch.setattr("app.get_user", mock_get_user)
    user_id = ObjectId()
    mock_get_user.return_value = {
        "_id": user_id,
        "username": "testuser",
        "friends": ["friend1", "friend2"],
    }

    mock_find_one = Mock()
    monkeypatch.setattr("pymongo.collection.Collection.find_one", mock_find_one)
    friend1 = {"_id": ObjectId(), "username": "friend1"}
    friend2 = {"_id": ObjectId(), "username": "friend2"}
    mock_find_one.side_effect = [friend1, friend2]

    response = client.get("/my_friends")
    assert response.status_code == 200


def test_send_letter(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    mock_get_user = Mock()
    monkeypatch.setattr("app.get_user", mock_get_user)
    sender_id = ObjectId()
    receiver_id = ObjectId()
    mock_get_user.side_effect = [
        {"_id": sender_id, "username": "sender"},
        {"_id": receiver_id, "username": "receiver"},
    ]
    mock_insert_one = Mock()
    monkeypatch.setattr("pymongo.collection.Collection.insert_one", mock_insert_one)

    response_get = client.get("/send_letter")
    assert response_get.status_code == 200


def test_add_to_friends(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    mock_object_id = Mock()
    monkeypatch.setattr("bson.ObjectId", mock_object_id)
    user_id = ObjectId()
    friend_id = ObjectId()
    mock_object_id.side_effect = [user_id, friend_id]
    mock_find_one = Mock()
    monkeypatch.setattr("pymongo.collection.Collection.find_one", mock_find_one)
    user = {"_id": user_id, "username": "testuser", "friends": []}
    friend = {"_id": friend_id, "username": "friend"}
    mock_find_one.side_effect = [user, friend]
    mock_update_one = Mock()
    monkeypatch.setattr("pymongo.collection.Collection.update_one", mock_update_one)
    response = client.post("/add_to_friends", data={"friendId": str(friend_id)})
    assert response.status_code == 200


def test_find_user(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    mock_object_id = Mock()
    monkeypatch.setattr("bson.ObjectId", mock_object_id)
    user_id = ObjectId()
    mock_object_id.return_value = user_id

    mock_find_one = Mock()
    monkeypatch.setattr("pymongo.collection.Collection.find_one", mock_find_one)
    user = {"_id": user_id, "username": "testuser"}
    mock_find_one.return_value = user
    response = client.post("/findUser", data={"userId": str(user_id)})
    assert response.status_code == 200


def test_get_all_users_json(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    mock_object_id = Mock()
    monkeypatch.setattr("bson.ObjectId", mock_object_id)
    user_id = ObjectId()
    mock_object_id.return_value = user_id

    mock_get_user = Mock()
    mock_get_all_users = Mock()
    monkeypatch.setattr("app.get_user", mock_get_user)
    monkeypatch.setattr("app.get_all_users", mock_get_all_users)

    current_user = {"_id": user_id, "username": "testuser"}
    all_users = [
        {"_id": ObjectId(), "username": "user1"},
        {"_id": ObjectId(), "username": "user2"},
        {"_id": ObjectId(), "username": "user3"},
    ]

    mock_get_user.return_value = current_user
    mock_get_all_users.return_value = all_users

    response = client.get("/getUsersJson")
    assert response.status_code == 200
    assert response.is_json

    users_list = response.json
    assert isinstance(users_list, list)
    assert all(isinstance(user, dict) and "_id" in user for user in users_list)
    assert len(users_list) == len(all_users)


def test_pal_profile(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    monkeypatch.setattr("bson.ObjectId", Mock(return_value=ObjectId()))
    mock_get_user = Mock()
    monkeypatch.setattr("app.get_user", mock_get_user)
    current_user = {"_id": ObjectId(), "username": "testuser"}
    friend_user = {"_id": ObjectId(), "username": "frienduser"}
    mock_get_user.side_effect = (
        lambda user_id: current_user
        if str(user_id) == str(current_user["_id"])
        else friend_user
    )
    monkeypatch.setattr("app.render_template", Mock(return_value="rendered_template"))
    response = client.get(
        "/pal_profile", query_string={"user_id": str(friend_user["_id"])}
    )
    assert response.status_code == 404


"""
def test_see_friend(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    response = client.post("/pal_profile", data={"friend_id": str(ObjectId())})
    assert response.status_code == 404
    assert b"User not found. Log in first." in response.data
"""

"""
def test_see_friend_missing_friend_id(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    monkeypatch.setattr(
        "app.get_user",
        lambda user_id: {"_id": ObjectId(user_id), "username": "testuser"},
    )
    response = client.post("/pal_profile", data={})
    assert response.status_code == 404
    assert b"Friend ID not provided in the form data" in response.data



def test_see_friend_user_not_found(client, monkeypatch):
    with client.session_transaction() as session:
        session["userid"] = str(ObjectId())
    monkeypatch.setattr("app.get_user", lambda user_id: None)
    friend_id = str(ObjectId())
    response = client.post("/pal_profile", data={"friend_id": friend_id})
    assert response.status_code == 404
    assert b"User not found. Log in first." in response.data



def test_my_friends_route_no_user(client, monkeypatch):
    with client.session_transaction() as session:
        session.pop("userid", None)
    response = client.get("/my_friends")
    assert response.status_code == 404
    response_data = json.loads(response.data)
    assert "error" in response_data
    assert response_data["error"] == "User not found. Log in first."
"""


def mock_get_user(user_id):
    return {"_id": ObjectId(user_id), "username": "testuser"}


