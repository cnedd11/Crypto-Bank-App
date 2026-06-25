"""Entry point for running the Flask development server."""
import logging
import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    if debug_mode:
        logger.warning(
            "Flask is running in DEBUG mode. Never enable this in production — "
            "the interactive debugger exposes sensitive server internals."
        )
    if app.config['SECRET_KEY'] == 'dev-only-replace-with-strong-env-var-in-production':
        logger.warning(
            "Using the default development SECRET_KEY. "
            "Set the SECRET_KEY environment variable before deploying."
        )
    app.run(debug=debug_mode)
