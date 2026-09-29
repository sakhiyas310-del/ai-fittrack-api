from flask import Blueprint, request
from werkzeug.security import check_password_hash

from app.db import get_connection
from app.routes.users import _row_to_dict
from app.utils.auth import make_token
from app.utils.responses import success_response, error_response
from app.utils.validation import ValidationError, require_fields, validate_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """
    Log in with email and password. Returns the user and a login token.

    Example request body:
    { "email": "alex@example.com", "password": "secret123" }
    """
    data = request.get_json(silent=True) or {}
    try:
        require_fields(data, ["email", "password"])
        email = validate_email(data["email"])
    except ValidationError as e:
        return error_response(e.message, 400)

    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()

    # Same message for "no such email" and "wrong password" so attackers learn nothing.
    if not row or not row["password_hash"] or not check_password_hash(row["password_hash"], str(data["password"])):
        return error_response("Incorrect email or password.", 401)

    return success_response({"user": _row_to_dict(row), "token": make_token(row["id"])})
