import os

from flask import jsonify, request

BRITE_API_KEY = os.environ.get("BRITE_API_KEY", "")

# Paths that don't require an API key
EXEMPT_PATHS = frozenset({"/", "/health"})


def require_api_key(app):
    """Register a before_request hook that checks for a valid API key."""

    @app.before_request
    def _check_api_key():
        if not BRITE_API_KEY:
            # No key configured — skip enforcement (dev mode)
            return None

        if request.path in EXEMPT_PATHS:
            return None

        provided = request.headers.get("X-API-Key", "")
        if provided == BRITE_API_KEY:
            return None

        return jsonify({"message": "Missing or invalid API key"}), 401
