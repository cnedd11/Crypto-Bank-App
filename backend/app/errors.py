import logging

from flask import jsonify, request

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register global JSON error handlers on the Flask app."""

    # OWASP A07: Return safe JSON error messages with no stack traces or
    # internal details that could aid an attacker.
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
