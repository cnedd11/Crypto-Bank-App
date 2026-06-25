# tests/test_app.py

import pytest
from werkzeug.security import generate_password_hash

from server.app import app, db, User, Customer, CryptoWallet, _failed_logins

# Strong password that satisfies the server-side complexity rule:
# min 8 chars, uppercase, lowercase, digit, special character.
STRONG_PW = "Test@1234"


@pytest.fixture
def client():
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "test-secret",
    })
    with app.app_context():
        db.create_all()
        # Reset brute-force tracker between tests so lockouts don't bleed over.
        _failed_logins.clear()
        yield app.test_client()
        db.drop_all()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def register(client, email, pw=STRONG_PW):
    return client.post("/api/register", json={"email": email, "password": pw})


def login(client, email, pw=STRONG_PW):
    return client.post("/api/login", json={"email": email, "password": pw})


def logout(client):
    return client.post("/api/logout")


def create_admin(email, pw=STRONG_PW):
    """Insert an admin user directly into the DB, bypassing the register endpoint.

    The public /api/register endpoint always assigns the 'user' role, so admin
    accounts must be seeded directly (or via a protected admin management route).
    """
    hashed = generate_password_hash(pw)
    user = User(email=email, role='admin')
    user.password = hashed
    db.session.add(user)
    db.session.commit()


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------
def test_register_missing_fields(client):
    rv = client.post("/api/register", json={"email": "a@b.com"})
    assert rv.status_code == 400
    assert b"Email and password required" in rv.data


def test_register_and_duplicate(client):
    rv1 = register(client, "a@b.com")
    assert rv1.status_code == 201
    rv2 = register(client, "a@b.com")
    assert rv2.status_code == 400
    assert b"Email already registered" in rv2.data


def test_login_logout_and_me(client):
    # No user → login fails
    rv = login(client, "no@one.com")
    assert rv.status_code == 401

    # Register & login
    register(client, "u@x.com")
    rv = login(client, "u@x.com")
    assert rv.status_code == 200

    # /api/me returns user info
    rv = client.get("/api/me")
    assert rv.status_code == 200
    assert b"u@x.com" in rv.data

    # Protected message endpoint
    rv = client.get("/api/message")
    assert rv.status_code == 200
    assert b"Hello from Flask" in rv.data

    # Logout
    rv = logout(client)
    assert rv.status_code == 200

    # After logout, both endpoints return 401
    assert client.get("/api/me").status_code == 401
    assert client.get("/api/message").status_code == 401


def test_protected_routes_session_persists(client):
    register(client, "aa@bb.com")
    login(client, "aa@bb.com")
    rv = client.get("/api/message")
    assert rv.status_code == 200


# ---------------------------------------------------------------------------
# OWASP A07 — Authentication Failures: password strength & brute-force tests
# ---------------------------------------------------------------------------
def test_weak_password_rejected(client):
    """Server must reject passwords that do not meet complexity rules."""
    for weak_pw in ("password", "short", "alllower1!", "ALLUPPER1!"):
        rv = client.post("/api/register", json={"email": "x@x.com", "password": weak_pw})
        assert rv.status_code == 400, f"Expected 400 for weak pw: {weak_pw}"
        assert b"Password must be at least 8 characters" in rv.data


def test_brute_force_lockout(client):
    """Account must be locked after MAX_LOGIN_ATTEMPTS consecutive failures.

    The MAX_LOGIN_ATTEMPTS-th bad attempt is itself the trigger that returns 429
    and locks the account; all earlier attempts return 401.
    """
    from server.app import MAX_LOGIN_ATTEMPTS
    register(client, "victim@mail.com")

    # First (MAX_LOGIN_ATTEMPTS - 1) attempts return 401
    for _ in range(MAX_LOGIN_ATTEMPTS - 1):
        rv = login(client, "victim@mail.com", "WrongPass!9")
        assert rv.status_code == 401

    # The MAX_LOGIN_ATTEMPTS-th bad attempt triggers the lockout and returns 429
    rv = login(client, "victim@mail.com", "WrongPass!9")
    assert rv.status_code == 429
    assert b"locked" in rv.data

    # Even the correct credential is now blocked
    rv = login(client, "victim@mail.com")
    assert rv.status_code == 429
    assert b"locked" in rv.data


def test_self_registration_cannot_assign_admin_role(client):
    """OWASP A01: Passing role='admin' in the request body must be ignored."""
    rv = client.post("/api/register", json={
        "email": "hacker@mail.com",
        "password": STRONG_PW,
        "role": "admin",   # attempted privilege escalation
    })
    assert rv.status_code == 201

    # Log in and try an admin action — must be rejected
    login(client, "hacker@mail.com")
    rv2 = client.post("/api/customers", json={"name": "T", "email": "t@t.com"})
    cust_id = rv2.json["id"]
    rv3 = client.delete(f"/api/customers/{cust_id}")
    assert rv3.status_code == 403  # still a plain user, not admin


# ---------------------------------------------------------------------------
# OWASP A03 — SQL Injection: injection patterns must be rejected
# ---------------------------------------------------------------------------
def test_sql_injection_blocked_in_register_email(client):
    """SQL injection keywords in email field must return 400.

    Note: single quotes alone are not blocked (O'Brien is a valid name);
    the check targets SQL operators and keywords such as OR 1=1 and --.
    """
    rv = client.post("/api/register", json={
        "email": "a OR 1=1 --",
        "password": STRONG_PW,
    })
    assert rv.status_code == 400
    assert b"Invalid input" in rv.data


def test_sql_injection_blocked_in_customer_name(client):
    """SQL injection pattern in customer name field must return 400."""
    register(client, "user@mail.com")
    login(client, "user@mail.com")
    rv = client.post("/api/customers", json={
        "name": "'; DROP TABLE customer; --",
        "email": "evil@example.com",
    })
    assert rv.status_code == 400
    assert b"Invalid input" in rv.data


def test_sql_injection_blocked_in_wallet_name(client):
    """SQL injection pattern in wallet name field must return 400."""
    register(client, "user2@mail.com")
    login(client, "user2@mail.com")
    cust = client.post("/api/customers", json={"name": "Bob", "email": "bob@mail.com"})
    cust_id = cust.json["id"]
    rv = client.post("/api/wallets", json={
        "customer_id": cust_id,
        "wallet_name": "' UNION SELECT * FROM user --",
    })
    assert rv.status_code == 400
    assert b"Invalid input" in rv.data


# ---------------------------------------------------------------------------
# OWASP A01 — Broken Access Control: unauthenticated / non-admin access tests
# ---------------------------------------------------------------------------
def test_customer_crud_and_delete_permissions(client):
    # Need to be logged in to list or add customers
    register(client, "setup@mail.com")
    login(client, "setup@mail.com")

    # List empty
    rv = client.get("/api/customers")
    assert rv.status_code == 200
    assert rv.json == []

    # Add customer — missing fields
    rv = client.post("/api/customers", json={"name": "X"})
    assert rv.status_code == 400

    # Valid add
    rv = client.post("/api/customers", json={
        "name": "Alice", "email": "alice@mail.com", "phone": "123"
    })
    assert rv.status_code == 201
    cust_id = rv.json["id"]

    # List now has one entry
    rv = client.get("/api/customers")
    assert any(c["id"] == cust_id for c in rv.json)

    # Delete without any session → 401
    logout(client)
    rv = client.delete(f"/api/customers/{cust_id}")
    assert rv.status_code == 401

    # Delete as regular user → 403
    register(client, "u1@mail.com")
    login(client, "u1@mail.com")
    rv = client.delete(f"/api/customers/{cust_id}")
    assert rv.status_code == 403

    # Delete as admin → 200
    create_admin("admin@mail.com")
    login(client, "admin@mail.com")
    rv = client.delete(f"/api/customers/{cust_id}")
    assert rv.status_code == 200
    assert b"deleted" in rv.data

    # Deleting the same record again → 404
    rv = client.delete(f"/api/customers/{cust_id}")
    assert rv.status_code == 404


def test_wallets_crud(client):
    # Login before any customer/wallet operations (all routes are now auth-guarded)
    register(client, "walletuser@mail.com")
    login(client, "walletuser@mail.com")

    # Prepare customer
    rv = client.post("/api/customers", json={
        "name": "Bob", "email": "bob@mail.com", "phone": ""
    })
    cust_id = rv.json["id"]

    # List wallets — initially empty
    rv = client.get(f"/api/customers/{cust_id}/wallets")
    assert rv.status_code == 200
    assert rv.json == []

    # Add wallet — missing fields
    rv = client.post("/api/wallets", json={"customer_id": cust_id})
    assert rv.status_code == 400

    # Add wallet — non-existent customer
    rv = client.post("/api/wallets", json={"customer_id": 999, "wallet_name": "X"})
    assert rv.status_code == 404

    # Valid add
    rv = client.post("/api/wallets", json={
        "customer_id": cust_id, "wallet_name": "MyWallet", "balance": 5.5
    })
    assert rv.status_code == 201
    w_id = rv.json["id"]
    assert rv.json["balance"] == 5.5

    # List now includes the wallet
    rv = client.get(f"/api/customers/{cust_id}/wallets")
    assert any(w["id"] == w_id for w in rv.json)

    # Update — non-existent wallet
    rv = client.put("/api/wallets/999", json={"wallet_name": "New"})
    assert rv.status_code == 404

    # Valid update
    rv = client.put(f"/api/wallets/{w_id}", json={"wallet_name": "Updated", "balance": 2.2})
    assert rv.status_code == 200
    assert rv.json["wallet_name"] == "Updated"
    assert rv.json["balance"] == 2.2

    # Delete wallet without session → 401
    logout(client)
    rv = client.delete(f"/api/wallets/{w_id}")
    assert rv.status_code == 401

    # Delete as non-admin → 403
    register(client, "user2@mail.com")
    login(client, "user2@mail.com")
    rv = client.delete(f"/api/wallets/{w_id}")
    assert rv.status_code == 403

    # Delete as admin → 200
    create_admin("root@mail.com")
    login(client, "root@mail.com")
    rv = client.delete(f"/api/wallets/{w_id}")
    assert rv.status_code == 200
    assert b"deleted" in rv.data

    # Cascading delete: add another wallet then delete the customer
    rv = client.post("/api/wallets", json={
        "customer_id": cust_id, "wallet_name": "Temp", "balance": 1.0
    })
    # Delete customer → wallets cascade
    rv = client.delete(f"/api/customers/{cust_id}")
    assert rv.status_code == 200
    # Wallet list for the deleted customer must now be empty
    rv = client.get(f"/api/customers/{cust_id}/wallets")
    assert rv.status_code == 200
    assert rv.json == []


# ---------------------------------------------------------------------------
# Email format validation
# ---------------------------------------------------------------------------
def test_register_invalid_email_format(client):
    """Server must reject emails that do not match the expected format (returns 422)."""
    for bad_email in ("notanemail", "missing@", "@nodomain.com", "spaces in@email.com"):
        rv = client.post("/api/register", json={"email": bad_email, "password": STRONG_PW})
        assert rv.status_code == 422, f"Expected 422 for invalid email: {bad_email}"
        assert b"Invalid email format" in rv.data


def test_register_field_length_limits(client):
    """Email or password exceeding maximum length must be rejected with 422."""
    long_email = "a" * 115 + "@b.com"  # 121 characters total, exceeds 120-char limit
    rv = client.post("/api/register", json={"email": long_email, "password": STRONG_PW})
    assert rv.status_code == 422
    assert b"at most 120 characters" in rv.data

    long_pw = "Test@1234" + "x" * 200  # > 128 characters
    rv = client.post("/api/register", json={"email": "new@b.com", "password": long_pw})
    assert rv.status_code == 422
    assert b"at most 128 characters" in rv.data


def test_customer_invalid_email_format(client):
    """Customer email must pass format validation; invalid formats return 422."""
    register(client, "u@u.com")
    login(client, "u@u.com")
    rv = client.post("/api/customers", json={"name": "Test", "email": "bademail"})
    assert rv.status_code == 422
    assert b"Invalid email format" in rv.data


def test_customer_invalid_phone_format(client):
    """Customer phone with disallowed characters must be rejected with 422."""
    register(client, "ph@test.com")
    login(client, "ph@test.com")
    rv = client.post("/api/customers", json={
        "name": "Test", "email": "test@test.com", "phone": "abc!!!###"
    })
    assert rv.status_code == 422
    assert b"Invalid phone format" in rv.data


def test_global_404_handler(client):
    """Requests to unknown API routes must return a JSON 404 error response."""
    rv = client.get("/api/nonexistent-endpoint-xyz")
    assert rv.status_code == 404
    data = rv.get_json()
    assert data is not None, "Response must be valid JSON"
    assert "error" in data
