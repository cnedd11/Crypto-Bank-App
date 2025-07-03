# server/app.py

from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace_with_strong_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crypto_bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app, supports_credentials=True)

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

# Create DB tables (run once)
with app.app_context():
    db.create_all()

# --- Auth Routes ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    hashed = generate_password_hash(data['password'])
    new_user = User(
        email=data['email'],
        password=hashed,
        role=data.get('role', 'user')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registration successful'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user_id'] = user.id
    return jsonify({'message': 'Login successful'}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200

# --- Protected Test Route ---
@app.route('/api/message', methods=['GET'])
def message():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'message': 'Hello from Flask, authenticated user!'}), 200

# --- Customer Endpoints ---
@app.route('/api/customers', methods=['GET'])
def list_customers():
    # Uncomment to require login:
    # if 'user_id' not in session:
    #     return jsonify({'error': 'Unauthorized'}), 401

    customers = Customer.query.all()
    output = [
        {'id': c.id, 'name': c.name, 'email': c.email, 'phone': c.phone}
        for c in customers
    ]
    return jsonify(output), 200

@app.route('/api/customers', methods=['POST'])
def add_customer():
    # Uncomment to require login:
    # if 'user_id' not in session:
    #     return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
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

# server/app.py (add below your POST /api/customers)

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

if __name__ == '__main__':
    app.run(debug=True)