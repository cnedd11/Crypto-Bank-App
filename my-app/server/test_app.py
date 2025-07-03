# tests/test_app.py

import pytest
from server.app import app, db, User, Customer, CryptoWallet
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    # configure app for testing
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "test-secret",
    })
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def register(client, email, password, role=None):
    payload = {"email": email, "password": password}
    if role:
        payload["role"] = role
    return client.post("/api/register", json=payload)

def login(client, email, password):
    return client.post("/api/login", json={"email": email, "password": password})

def logout(client):
    return client.post("/api/logout")

def test_register_missing_fields(client):
    rv = client.post("/api/register", json={"email": "a@b.com"})
    assert rv.status_code == 400
    assert b"Email and password required" in rv.data

def test_register_and_duplicate(client):
    rv1 = register(client, "a@b.com", "secret")
    assert rv1.status_code == 201
    rv2 = register(client, "a@b.com", "another")
    assert rv2.status_code == 400
    assert b"Email already registered" in rv2.data

def test_login_logout_and_me(client):
    # no user -> login fails
    rv = login(client, "no@one", "pw")
    assert rv.status_code == 401

    # register & login
    register(client, "u@x.com", "pw123")
    rv = login(client, "u@x.com", "pw123")
    assert rv.status_code == 200

    # me endpoint
    rv = client.get("/api/me")
    assert rv.status_code == 200
    assert b"u@x.com" in rv.data

    # message endpoint (protected)
    rv = client.get("/api/message")
    assert rv.status_code == 200
    assert b"Hello from Flask" in rv.data

    # logout
    rv = logout(client)
    assert rv.status_code == 200

    # me now unauthorized
    assert client.get("/api/me").status_code == 401
    # message unauthorized
    assert client.get("/api/message").status_code == 401

def test_protected_routes_session_persists(client):
    # register and login
    register(client, "aa@bb.com", "pw123")
    login(client, "aa@bb.com", "pw123")
    rv = client.get("/api/message")
    assert rv.status_code == 200

def test_customer_crud_and_delete_permissions(client):
    # list empty
    rv = client.get("/api/customers")
    assert rv.status_code == 200
    assert rv.json == []

    # add customer missing fields
    rv = client.post("/api/customers", json={"name": "X"})
    assert rv.status_code == 400

    # valid add
    rv = client.post("/api/customers", json={
        "name": "Alice", "email": "alice@mail.com", "phone": "123"
    })
    assert rv.status_code == 201
    cust_id = rv.json["id"]

    # list now has one
    rv = client.get("/api/customers")
    assert any(c["id"] == cust_id for c in rv.json)

    # delete without login
    rv = client.delete(f"/api/customers/{cust_id}")
    assert rv.status_code == 401

    # login as regular
    register(client, "u1@mail", "pw123", role="user")
    login(client, "u1@mail", "pw123")
    rv = client.delete(f"/api/customers/{cust_id}")
    assert rv.status_code == 403

    # login as admin
    register(client, "admin@mail", "pw123", role="admin")
    login(client, "admin@mail", "pw123")
    rv = client.delete(f"/api/customers/{cust_id}")
    assert rv.status_code == 200
    assert b"deleted" in rv.data

    # deleting again yields 404
    rv = client.delete(f"/api/customers/{cust_id}")
    assert rv.status_code == 404

def test_wallets_crud(client):
    # prepare customer
    rv = client.post("/api/customers", json={
        "name": "Bob", "email": "bob@mail", "phone": ""
    })
    cust_id = rv.json["id"]

    # list wallets empty
    rv = client.get(f"/api/customers/{cust_id}/wallets")
    assert rv.status_code == 200
    assert rv.json == []

    # add wallet missing fields
    rv = client.post("/api/wallets", json={"customer_id": cust_id})
    assert rv.status_code == 400

    # add for non-existent customer
    rv = client.post("/api/wallets", json={
        "customer_id": 999, "wallet_name": "X"
    })
    assert rv.status_code == 404

    # valid add
    rv = client.post("/api/wallets", json={
        "customer_id": cust_id, "wallet_name": "MyWallet", "balance": 5.5
    })
    assert rv.status_code == 201
    w_id = rv.json["id"]
    assert rv.json["balance"] == 5.5

    # list now includes it
    rv = client.get(f"/api/customers/{cust_id}/wallets")
    assert any(w["id"] == w_id for w in rv.json)

    # update missing wallet
    rv = client.put("/api/wallets/999", json={"wallet_name": "New"})
    assert rv.status_code == 404

    # valid update
    rv = client.put(f"/api/wallets/{w_id}", json={"wallet_name": "Updated", "balance": 2.2})
    assert rv.status_code == 200
    assert rv.json["wallet_name"] == "Updated"
    assert rv.json["balance"] == 2.2

    # delete wallet without auth
    rv = client.delete(f"/api/wallets/{w_id}")
    assert rv.status_code == 401

    # login as non-admin
    register(client, "user2@mail", "pw123", role="user")
    login(client, "user2@mail", "pw123")
    rv = client.delete(f"/api/wallets/{w_id}")
    assert rv.status_code == 403

    # admin deletes
    register(client, "root@mail", "pw123", role="admin")
    login(client, "root@mail", "pw123")
    rv = client.delete(f"/api/wallets/{w_id}")
    assert rv.status_code == 200
    assert b"deleted" in rv.data

    # cascading delete: add wallet, then delete customer
    rv = client.post("/api/wallets", json={
        "customer_id": cust_id, "wallet_name": "Temp", "balance": 1.0
    })
    w2 = rv.json["id"]
    # delete customer -> wallets cascade
    rv = client.delete(f"/api/customers/{cust_id}")
    assert rv.status_code == 200
    # now wallet should be gone
    login(client, "root@mail", "pw123")
    rv = client.get(f"/api/customers/{cust_id}/wallets")
    assert rv.status_code == 200
    assert rv.json == []