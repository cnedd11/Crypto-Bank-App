from flask import Blueprint  # noqa: F401 - makes the package importable

from .auth import auth_bp
from .customers import customers_bp
from .wallets import wallets_bp

__all__ = ['auth_bp', 'customers_bp', 'wallets_bp']
