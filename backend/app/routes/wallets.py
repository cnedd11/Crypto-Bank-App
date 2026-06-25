import logging

from flask import Blueprint, jsonify, request, session

from ..models import Customer, CryptoWallet
from .. import db
from ..validators import contains_sql_injection, validate_balance
from .auth import login_required, admin_required

logger = logging.getLogger(__name__)

wallets_bp = Blueprint('wallets', __name__)


@wallets_bp.route('/api/customers/<int:cust_id>/wallets', methods=['GET'])
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


@wallets_bp.route('/api/wallets', methods=['POST'])
@login_required
def add_wallet():
    data = request.json or {}
    cust_id = data.get('customer_id')
    wallet_name = (data.get('wallet_name') or '').strip()

    if not cust_id or not wallet_name:
        return jsonify({'error': 'Customer ID and wallet name required'}), 400

    # OWASP A03: Reject injection patterns in wallet name.
    if contains_sql_injection(wallet_name):
        logger.warning(
            "SQL injection pattern in wallet name from user_id=%s",
            session.get('user_id')
        )
        return jsonify({'error': 'Invalid input'}), 400

    # Length limit for wallet name.
    if len(wallet_name) > 100:
        return jsonify({'error': 'Wallet name must be at most 100 characters'}), 422

    cust = db.session.get(Customer, cust_id)
    if not cust:
        return jsonify({'error': 'Customer not found'}), 404

    balance, err = validate_balance(data.get('balance'), fallback=0.0)
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


@wallets_bp.route('/api/wallets/<int:id>', methods=['PUT'])
@login_required
def update_wallet(id):
    data = request.json or {}
    wallet = db.session.get(CryptoWallet, id)
    if not wallet:
        return jsonify({'error': 'Wallet not found'}), 404

    new_name = (data.get('wallet_name') or wallet.wallet_name).strip()

    # OWASP A03: Reject injection patterns in updated wallet name.
    if contains_sql_injection(new_name):
        logger.warning(
            "SQL injection pattern in wallet update from user_id=%s",
            session.get('user_id')
        )
        return jsonify({'error': 'Invalid input'}), 400

    # Length limit for wallet name.
    if len(new_name) > 100:
        return jsonify({'error': 'Wallet name must be at most 100 characters'}), 422

    new_balance, err = validate_balance(data.get('balance'), fallback=wallet.balance)
    if err:
        return jsonify({'error': err}), 400

    wallet.wallet_name = new_name
    wallet.balance = new_balance
    db.session.commit()
    return jsonify({
        'id': wallet.id,
        'wallet_name': wallet.wallet_name,
        'balance': wallet.balance,
        'customer_id': wallet.customer_id
    }), 200


# OWASP A01: Only admins may delete wallets.
@wallets_bp.route('/api/wallets/<int:id>', methods=['DELETE'])
@admin_required
def delete_wallet(id):
    wallet = db.session.get(CryptoWallet, id)
    if not wallet:
        return jsonify({'error': 'Not found'}), 404

    db.session.delete(wallet)
    db.session.commit()
    logger.info("Admin (user_id=%s) deleted wallet id=%d", session.get('user_id'), id)
    return jsonify({'message': 'Wallet deleted'}), 200
