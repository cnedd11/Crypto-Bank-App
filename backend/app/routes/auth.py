import logging
import time
import threading
from collections import defaultdict
from functools import wraps

from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash

from ..models import User
from .. import db
from ..validators import contains_sql_injection, is_strong_password, is_valid_email

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

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
        user = db.session.get(User, user_id)
        if not user or user.role != 'admin':
            logger.warning(
                "Forbidden: user_id=%s attempted admin action on %s",
                user_id, request.path
            )
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    # OWASP A03: Reject inputs containing SQL injection patterns.
    if contains_sql_injection(email):
        logger.warning("SQL injection pattern detected in registration email")
        return jsonify({'error': 'Invalid input'}), 400

    # Validate email format.
    if not is_valid_email(email):
        logger.warning("Invalid email format in registration attempt: %s", request.path)
        return jsonify({'error': 'Invalid email format'}), 422

    # Field length limits prevent excessively large inputs.
    if len(email) > 120:
        return jsonify({'error': 'Email must be at most 120 characters'}), 422
    if len(password) > 128:
        return jsonify({'error': 'Password must be at most 128 characters'}), 422

    # OWASP A07: Validate password strength on the server.
    if not is_strong_password(password):
        return jsonify({
            'error': 'Password must be at least 8 characters and include '
                     'uppercase, lowercase, number, and special character.'
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    hashed = generate_password_hash(password)
    # OWASP A01: All self-registered users are always assigned 'user' role.
    user = User(email=email, role='user')
    user.password = hashed
    db.session.add(user)
    db.session.commit()
    logger.info("New user registered: %s", email)
    return jsonify({'message': 'Registration successful'}), 201


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    email = (data.get('email') or '').strip()
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


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200


@auth_bp.route('/api/me', methods=['GET'])
def me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        return jsonify({'error': 'Unauthorized'}), 401

    return jsonify({
        'user': {
            'email': user.email,
            'role': user.role
        }
    }), 200


@auth_bp.route('/api/message', methods=['GET'])
@login_required
def message():
    return jsonify({'message': 'Hello from Flask, authenticated user!'}), 200
