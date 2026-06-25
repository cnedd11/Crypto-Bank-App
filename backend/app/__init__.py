import logging

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Logging setup:
# Security events (blocked injections, failed logins, forbidden access) are
# logged at WARNING level so they can be monitored and audited.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enforce foreign key constraints in SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_app(test_config=None):
    """Application factory. Pass a dict to override config for testing."""
    app = Flask(__name__, instance_relative_config=True)

    # Load default config from config module.
    from config import Config
    app.config.from_object(Config)

    # Override with any test/custom settings passed in.
    if test_config is not None:
        app.config.update(test_config)

    # OWASP A07: Harden session cookies.
    app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
    app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
    app.config.setdefault('SESSION_COOKIE_SECURE', False)

    CORS(app, supports_credentials=True)
    db.init_app(app)

    with app.app_context():
        # Import models so SQLAlchemy creates the tables.
        from . import models  # noqa: F401
        db.create_all()

        # Register route blueprints.
        from .routes import auth_bp, customers_bp, wallets_bp
        app.register_blueprint(auth_bp)
        app.register_blueprint(customers_bp)
        app.register_blueprint(wallets_bp)

        # Register global error handlers.
        from .errors import register_error_handlers
        register_error_handlers(app)

    return app
