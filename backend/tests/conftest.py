import pytest
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import User
from app.routes.auth import _failed_logins


@pytest.fixture
def client():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret',
    })
    with app.app_context():
        db.create_all()
        _failed_logins.clear()
        yield app.test_client()
        db.drop_all()


def create_admin(email, pw):
    """Insert an admin user directly into the DB, bypassing the register endpoint.

    The public /api/register endpoint always assigns the 'user' role, so admin
    accounts must be seeded directly (or via a protected admin management route).
    """
    hashed = generate_password_hash(pw)
    user = User(email=email, role='admin')
    user.password = hashed
    db.session.add(user)
    db.session.commit()
