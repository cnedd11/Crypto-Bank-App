# server/app.py

from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy.engine import Engine

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace_with_strong_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crypto_bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

# --- Auth Routes ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    hashed = generate_password_hash(data['password'])
    user = User(
        email=data['email'],
        password=hashed,
        role=data.get('role', 'user')
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Registration successful'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or not check_password_hash(user.password, data.get('password','')):
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user_id'] = user.id
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
def message():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'message': 'Hello from Flask, authenticated user!'}), 200

# --- Customer Endpoints ---
@app.route('/api/customers', methods=['GET'])
def list_customers():
    customers = Customer.query.all()
    return jsonify([
        {'id': c.id, 'name': c.name, 'email': c.email, 'phone': c.phone}
        for c in customers
    ]), 200

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json or {}
    if not data.get('name') or not data.get('email'):
        return jsonify({'error': 'Name and email required'}), 400

    if Customer.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Customer email already in use'}), 400

    customer = Customer(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone')
    )
    db.session.add(customer)
    db.session.commit()
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone
    }), 201

@app.route('/api/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403

    customer = Customer.query.get(id)
    if not customer:
        return jsonify({'error': 'Not found'}), 404

    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Customer deleted'}), 200

# --- CryptoWallet Endpoints ---
@app.route('/api/customers/<int:cust_id>/wallets', methods=['GET'])
def list_wallets(cust_id):
    # Optional auth check here
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
def add_wallet():
    data = request.json or {}
    cust_id = data.get('customer_id')
    if not cust_id or not data.get('wallet_name'):
        return jsonify({'error': 'Customer ID and wallet name required'}), 400

    cust = Customer.query.get(cust_id)
    if not cust:
        return jsonify({'error': 'Customer not found'}), 404

    wallet = CryptoWallet(
        wallet_name=data['wallet_name'],
        balance=float(data.get('balance', 0.0)),
        customer_id=cust_id
    )
    db.session.add(wallet)
    db.session.commit()
    return jsonify({
        'id': wallet.id,
        'wallet_name': wallet.wallet_name,
        'balance': wallet.balance,
        'customer_id': wallet.customer_id
    }), 201

@app.route('/api/wallets/<int:id>', methods=['PUT'])
def update_wallet(id):
    data = request.json or {}
    wallet = CryptoWallet.query.get(id)
    if not wallet:
        return jsonify({'error': 'Wallet not found'}), 404

    # update fields if provided
    wallet.wallet_name = data.get('wallet_name', wallet.wallet_name)
    wallet.balance     = float(data.get('balance', wallet.balance))

    db.session.commit()
    return jsonify({
        'id': wallet.id,
        'wallet_name': wallet.wallet_name,
        'balance': wallet.balance,
        'customer_id': wallet.customer_id
    }), 200

@app.route('/api/wallets/<int:id>', methods=['DELETE'])
def delete_wallet(id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403

    wallet = CryptoWallet.query.get(id)
    if not wallet:
        return jsonify({'error': 'Not found'}), 404

    db.session.delete(wallet)
    db.session.commit()
    return jsonify({'message': 'Wallet deleted'}), 200

if __name__ == '__main__':
    app.run(debug=True)