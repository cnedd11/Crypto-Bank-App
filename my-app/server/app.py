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

# Create DB tables (run once)
with app.app_context():
    db.create_all()

# --- Routes ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    hashed = generate_password_hash(data['password'])
    user = User(email=data['email'], password=hashed)
    db.session.add(user)
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

# Example protected route
@app.route('/api/message')
def message():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'message': 'Hello from Flask, authenticated user!'})

if __name__ == '__main__':
    app.run(debug=True)