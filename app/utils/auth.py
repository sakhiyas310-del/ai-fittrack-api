"""
Login tokens.

After signing up or logging in, the API gives the user a signed token.
The user sends it back on every request as:  Authorization: Bearer <token>
The token is signed with SECRET_KEY, so nobody can fake one without the key.
"""

import os

from itsdangerous import BadSignature, URLSafeTimedSerializer

TOKEN_MAX_AGE = 60 * 60 * 24 * 7  # tokens stop working after 7 days


def _serializer():
    return URLSafeTimedSerializer(os.environ.get("SECRET_KEY", "dev-secret-change-me"))


def make_token(user_id):
    return _serializer().dumps({"uid": user_id})


def read_token(token):
    """Return the user id inside a valid token, or None if it is fake or expired."""
    try:
        return _serializer().loads(token, max_age=TOKEN_MAX_AGE)["uid"]
    except BadSignature:  # also covers expired tokens
        return None
