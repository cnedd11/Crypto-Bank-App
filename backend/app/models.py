from . import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=True)


class CryptoWallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet_name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customer.id', ondelete='CASCADE'),
        nullable=False
    )
