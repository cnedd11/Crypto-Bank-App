# server/app.py

import re
import os
import time
import threading
import logging
from collections import defaultdict
from functools import wraps

from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy.engine import Engine

# --- Logging setup ---
# Security events (blocked injections, failed logins, forbidden access) are
# logged at WARNING level so they can be monitored and audited.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# OWASP A07: Use an environment-driven secret key; the fallback is dev-only.
# In production, set the SECRET_KEY environment variable to a long random string.
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'dev-only-replace-with-strong-env-var-in-production'
)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crypto_bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# OWASP A07: Harden session cookies to reduce session-hijacking risk.
app.config['SESSION_COOKIE_HTTPONLY'] = True   # JS cannot read the cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Mitigates CSRF
app.config['SESSION_COOKIE_SECURE'] = False     # Set True when served over HTTPS
CORS(app, supports_credentials=True)

# Enforce foreign key constraints in SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role     = db.Column(db.String(20), nullable=False, default='user')

class Customer(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=True)

class CryptoWallet(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    wallet_name = db.Column(db.String(100), nullable=False)
    balance     = db.Column(db.Float, nullable=False, default=0.0)
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customer.id', ondelete='CASCADE'),
        nullable=False
    )

# Create tables (run once)
with app.app_context():
    db.create_all()

# ---------------------------------------------------------------------------
# OWASP A07 — Authentication Failures: brute-force login protection
# ---------------------------------------------------------------------------
# In-memory store: {email: {'count': int, 'locked_until': float}}
# Protected by a lock to avoid race conditions under concurrent requests.
# For production, replace with Redis or a persistent store.
_failed_logins = defaultdict(lambda: {'count': 0, 'locked_until': 0.0})
_failed_logins_lock = threading.Lock()
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes

# ---------------------------------------------------------------------------
# OWASP A03 — SQL Injection: detect common injection patterns in user input.
# All DB access already uses SQLAlchemy ORM (parameterised), so this layer
# provides defence-in-depth by rejecting obviously malicious payloads early.
# ---------------------------------------------------------------------------
# Single/double quotes are intentionally excluded from this pattern because
# they appear legitimately in names (e.g. O'Neill) and SQLAlchemy ORM's parameterised
# queries already prevent injection.  The pattern targets SQL operators and keywords.
_SQL_INJECTION_RE = re.compile(
    r"(--|;|/\*|\*/|xp_|union\s+select|select\s+\S+\s+from|"
    r"insert\s+into|drop\s+table|or\s+1\s*=\s*1|and\s+1\s*=\s*1)",
    re.IGNORECASE
)

# OWASP A07: Password complexity rule enforced server-side.
# Min 8 chars, at least one uppercase, one lowercase, one digit, one special char.
_PASSWORD_RE = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$'
)

# Email format: standard printable characters before @, domain label(s), and
# a TLD of at least 2 letters.  Single quotes and other special chars that
# appear legitimately in names are handled by the ORM's parameterised queries.
_EMAIL_RE = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
)

# Phone: optional field; allows digits, spaces, +, -, (, ) up to 30 chars.
_PHONE_RE = re.compile(r'^[\d\s+\-(). ]{1,30}$')


def _contains_sql_injection(value: str) -> bool:
    """Return True if value matches known SQL injection patterns."""
    return bool(_SQL_INJECTION_RE.search(value))


def _is_strong_password(password: str) -> bool:
    """Return True if password satisfies complexity requirements."""
    return bool(_PASSWORD_RE.match(password))

def _validate_balance(value, fallback=0.0):
    """Parse and validate a wallet balance.

    Returns (float, None) on success or (None, error_message) on failure.
    """
    try:
        balance = float(value if value is not None else fallback)
    except (TypeError, ValueError):
        return None, 'Invalid balance value'
    if balance < 0:
        return None, 'Balance cannot be negative'
    return balance, None

# ---------------------------------------------------------------------------
# OWASP A01 — Broken Access Control: reusable access-control decorators.
# ---------------------------------------------------------------------------
def login_required(f):
    """Require a valid session. Returns 401 if the user is not logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning("Unauthenticated access attempt to %s", request.path)
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Require admin role. Returns 401 if not logged in, 403 if not admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            logger.warning(
                "Unauthenticated access attempt to admin route %s", request.path
            )
            return jsonify({'error': 'Unauthorized'}), 401
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            logger.warning(
                "Forbidden: user_id=%s attempted admin action on %s",
                user_id, request.path
            )
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    return decorated


# --- Auth Routes ---
@app.route('/api/register', methods=['POST'])
def register():
    data     = request.json or {}
    email    = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    # OWASP A03: Reject inputs containing SQL injection patterns.
    if _contains_sql_injection(email):
        logger.warning("SQL injection pattern detected in registration email")
        return jsonify({'error': 'Invalid input'}), 400

    # Validate email format.
    if not _EMAIL_RE.match(email):
        logger.warning("Invalid email format in registration attempt: %s", request.path)
        return jsonify({'error': 'Invalid email format'}), 422

    # Field length limits prevent excessively large inputs.
    if len(email) > 120:
        return jsonify({'error': 'Email must be at most 120 characters'}), 422
    if len(password) > 128:
        return jsonify({'error': 'Password must be at most 128 characters'}), 422

    # OWASP A07: Validate password strength on the server — the frontend check
    # can be bypassed, so server-side enforcement is the authoritative gate.
    if not _is_strong_password(password):
        return jsonify({
            'error': 'Password must be at least 8 characters and include '
                     'uppercase, lowercase, number, and special character.'
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    hashed = generate_password_hash(password)
    # OWASP A01: All self-registered users are always assigned 'user' role.
    # Admin roles must be granted by an existing admin through a separate,
    # protected administrative workflow — never via the public register form.
    user = User(email=email, role='user')
    user.password = hashed
    db.session.add(user)
    db.session.commit()
    logger.info("New user registered: %s", email)
    return jsonify({'message': 'Registration successful'}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data     = request.json or {}
    email    = (data.get('email') or '').strip()
    password = data.get('password') or ''

    now = time.time()

    with _failed_logins_lock:
        record = _failed_logins[email]

        # OWASP A07: Enforce lockout before doing any credential check.
        if record['locked_until'] > now:
            remaining = int(record['locked_until'] - now)
            logger.warning("Locked account login attempt for: %s", email)
            return jsonify({
                'error': f'Account temporarily locked. Try again in {remaining} seconds.'
            }), 429

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            record['count'] += 1
            if record['count'] >= MAX_LOGIN_ATTEMPTS:
                record['locked_until'] = now + LOCKOUT_SECONDS
                record['count'] = 0
                logger.warning("Account locked after repeated failures: %s", email)
                return jsonify({
                    'error': (
                        f'Too many failed attempts. '
                        f'Account locked for {LOCKOUT_SECONDS // 60} minutes.'
                    )
                }), 429
            logger.warning(
                "Failed login attempt %d/%d for: %s",
                record['count'], MAX_LOGIN_ATTEMPTS, email
            )
            return jsonify({'error': 'Invalid credentials'}), 401

        # Successful login: reset the failure counter.
        record['count'] = 0
        record['locked_until'] = 0.0

    session['user_id'] = user.id
    logger.info("Successful login: %s", email)
    return jsonify({'message': 'Login successful'}), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200


# --- Current User Endpoint ---
@app.route('/api/me', methods=['GET'])
def me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(user_id)
    if not user:
        session.clear()
        return jsonify({'error': 'Unauthorized'}), 401

    return jsonify({
        'user': {
            'email': user.email,
            'role': user.role
        }
    }), 200


# --- Protected Test Route ---
@app.route('/api/message', methods=['GET'])
@login_required
def message():
    return jsonify({'message': 'Hello from Flask, authenticated user!'}), 200


# --- Customer Endpoints ---
@app.route('/api/customers', methods=['GET'])
@login_required
def list_customers():
    customers = Customer.query.all()
    return jsonify([
        {'id': c.id, 'name': c.name, 'email': c.email, 'phone': c.phone}
        for c in customers
    ]), 200


@app.route('/api/customers', methods=['POST'])
@login_required
def add_customer():
    data  = request.json or {}
    name  = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip() or None

    if not name or not email:
        return jsonify({'error': 'Name and email required'}), 400

    # OWASP A03: Block SQL injection patterns in customer fields.
    if _contains_sql_injection(name) or _contains_sql_injection(email):
        logger.warning(
            "SQL injection pattern in customer input from user_id=%s",
            session.get('user_id')
        )
        return jsonify({'error': 'Invalid input'}), 400

    # Validate email format.
    if not _EMAIL_RE.match(email):
        logger.warning(
            "Invalid customer email format from user_id=%s", session.get('user_id')
        )
        return jsonify({'error': 'Invalid email format'}), 422

    # Field length limits.
    if len(name) > 120:
        return jsonify({'error': 'Name must be at most 120 characters'}), 422
    if len(email) > 120:
        return jsonify({'error': 'Email must be at most 120 characters'}), 422

    # Validate phone format when provided.
    if phone and not _PHONE_RE.match(phone):
        logger.warning(
            "Invalid phone format in customer input from user_id=%s",
            session.get('user_id')
        )
        return jsonify({'error': 'Invalid phone format (digits, spaces, + - ( ) only)'}), 422

    if Customer.query.filter_by(email=email).first():
        return jsonify({'error': 'Customer email already in use'}), 400

    customer = Customer(name=name, email=email, phone=phone)
    db.session.add(customer)
    db.session.commit()
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone
    }), 201


# OWASP A01: Only admins may delete customers.
@app.route('/api/customers/<int:id>', methods=['DELETE'])
@admin_required
def delete_customer(id):
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({'error': 'Not found'}), 404

    db.session.delete(customer)
    db.session.commit()
    logger.info("Admin (user_id=%s) deleted customer id=%d", session.get('user_id'), id)
    return jsonify({'message': 'Customer deleted'}), 200


# --- CryptoWallet Endpoints ---
@app.route('/api/customers/<int:cust_id>/wallets', methods=['GET'])
@login_required
def list_wallets(cust_id):
    wallets = CryptoWallet.query.filter_by(customer_id=cust_id).all()
    return jsonify([
        {
            'id': w.id,
            'wallet_name': w.wallet_name,
            'balance': w.balance,
            'customer_id': w.customer_id
        } for w in wallets
    ]), 200


@app.route('/api/wallets', methods=['POST'])
@login_required
def add_wallet():
    data        = request.json or {}
    cust_id     = data.get('customer_id')
    wallet_name = (data.get('wallet_name') or '').strip()

    if not cust_id or not wallet_name:
        return jsonify({'error': 'Customer ID and wallet name required'}), 400

    # OWASP A03: Reject injection patterns in wallet name.
    if _contains_sql_injection(wallet_name):
        logger.warning(
            "SQL injection pattern in wallet name from user_id=%s",
            session.get('user_id')
        )
        return jsonify({'error': 'Invalid input'}), 400

    # Length limit for wallet name.
    if len(wallet_name) > 100:
        return jsonify({'error': 'Wallet name must be at most 100 characters'}), 422

    cust = Customer.query.get(cust_id)
    if not cust:
        return jsonify({'error': 'Customer not found'}), 404

    balance, err = _validate_balance(data.get('balance'), fallback=0.0)
    if err:
        return jsonify({'error': err}), 400

    wallet = CryptoWallet(wallet_name=wallet_name, balance=balance, customer_id=cust_id)
    db.session.add(wallet)
    db.session.commit()
    return jsonify({
        'id': wallet.id,
        'wallet_name': wallet.wallet_name,
        'balance': wallet.balance,
        'customer_id': wallet.customer_id
    }), 201


@app.route('/api/wallets/<int:id>', methods=['PUT'])
@login_required
def update_wallet(id):
    data   = request.json or {}
    wallet = CryptoWallet.query.get(id)
    if not wallet:
        return jsonify({'error': 'Wallet not found'}), 404

    new_name = (data.get('wallet_name') or wallet.wallet_name).strip()

    # OWASP A03: Reject injection patterns in updated wallet name.
    if _contains_sql_injection(new_name):
        logger.warning(
            "SQL injection pattern in wallet update from user_id=%s",
            session.get('user_id')
        )
        return jsonify({'error': 'Invalid input'}), 400

    # Length limit for wallet name.
    if len(new_name) > 100:
        return jsonify({'error': 'Wallet name must be at most 100 characters'}), 422

    new_balance, err = _validate_balance(data.get('balance'), fallback=wallet.balance)
    if err:
        return jsonify({'error': err}), 400

    wallet.wallet_name = new_name
    wallet.balance     = new_balance
    db.session.commit()
    return jsonify({
        'id': wallet.id,
        'wallet_name': wallet.wallet_name,
        'balance': wallet.balance,
        'customer_id': wallet.customer_id
    }), 200


# OWASP A01: Only admins may delete wallets.
@app.route('/api/wallets/<int:id>', methods=['DELETE'])
@admin_required
def delete_wallet(id):
    wallet = CryptoWallet.query.get(id)
    if not wallet:
        return jsonify({'error': 'Not found'}), 404

    db.session.delete(wallet)
    db.session.commit()
    logger.info("Admin (user_id=%s) deleted wallet id=%d", session.get('user_id'), id)
    return jsonify({'message': 'Wallet deleted'}), 200


# ---------------------------------------------------------------------------
# Global error handlers — OWASP A07: return safe JSON error messages with no
# stack traces or internal details that could aid an attacker.
# ---------------------------------------------------------------------------
@app.errorhandler(400)
def handle_400(e):
    logger.warning("400 Bad Request at %s: %s", request.path, str(e))
    return jsonify({'error': 'Bad request'}), 400


@app.errorhandler(401)
def handle_401(e):
    logger.warning("401 Unauthorized at %s", request.path)
    return jsonify({'error': 'Unauthorized'}), 401


@app.errorhandler(403)
def handle_403(e):
    logger.warning("403 Forbidden at %s", request.path)
    return jsonify({'error': 'Forbidden'}), 403


@app.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def handle_500(e):
    logger.error("500 Internal Server Error at %s: %s", request.path, str(e))
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    if debug_mode:
        logger.warning(
            "Flask is running in DEBUG mode. Never enable this in production — "
            "the interactive debugger exposes sensitive server internals."
        )
    # Also warn if the dev-only fallback secret key is still in use.
    if app.config['SECRET_KEY'] == 'dev-only-replace-with-strong-env-var-in-production':
        logger.warning(
            "Using the default development SECRET_KEY. "
            "Set the SECRET_KEY environment variable before deploying."
        )
    app.run(debug=debug_mode)
