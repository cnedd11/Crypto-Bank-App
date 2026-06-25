import logging

from flask import Blueprint, jsonify, request, session

from ..models import Customer
from .. import db
from ..validators import contains_sql_injection, is_valid_email, is_valid_phone
from .auth import login_required, admin_required

logger = logging.getLogger(__name__)

customers_bp = Blueprint('customers', __name__)


@customers_bp.route('/api/customers', methods=['GET'])
@login_required
def list_customers():
    customers = Customer.query.all()
    return jsonify([
        {'id': c.id, 'name': c.name, 'email': c.email, 'phone': c.phone}
        for c in customers
    ]), 200


@customers_bp.route('/api/customers', methods=['POST'])
@login_required
def add_customer():
    data = request.json or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip() or None

    if not name or not email:
        return jsonify({'error': 'Name and email required'}), 400

    # OWASP A03: Block SQL injection patterns in customer fields.
    if contains_sql_injection(name) or contains_sql_injection(email):
        logger.warning(
            "SQL injection pattern in customer input from user_id=%s",
            session.get('user_id')
        )
        return jsonify({'error': 'Invalid input'}), 400

    # Validate email format.
    if not is_valid_email(email):
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
    if phone and not is_valid_phone(phone):
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
@customers_bp.route('/api/customers/<int:id>', methods=['DELETE'])
@admin_required
def delete_customer(id):
    customer = db.session.get(Customer, id)
    if not customer:
        return jsonify({'error': 'Not found'}), 404

    db.session.delete(customer)
    db.session.commit()
    logger.info("Admin (user_id=%s) deleted customer id=%d", session.get('user_id'), id)
    return jsonify({'message': 'Customer deleted'}), 200
