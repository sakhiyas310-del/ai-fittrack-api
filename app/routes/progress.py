from flask import Blueprint, request

from app.db import get_connection
from app.utils.responses import success_response, error_response
from app.utils.validation import ValidationError, require_fields, validate_positive_number, validate_date

progress_bp = Blueprint("progress", __name__)


def _log_to_dict(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "weight_kg": row["weight_kg"],
        "date": row["date"],
        "created_at": row["created_at"],
    }


def _user_exists(conn, user_id):
    return conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone() is not None


@progress_bp.route("/api/users/<int:user_id>/weight", methods=["POST"])
def log_weight(user_id):
    """
    Record a weight measurement for a user.

    Example request body:
    {
        "weight_kg": 71.8,
        "date": "2026-09-27"
    }

    This also updates the user's current profile weight to this latest value.
    """
    data = request.get_json(silent=True) or {}
    try:
        require_fields(data, ["weight_kg", "date"])
        weight_kg = validate_positive_number(data["weight_kg"], "weight_kg")
        log_date = validate_date(data["date"], "date")
    except ValidationError as e:
        return error_response(e.message, 400)

    conn = get_connection()
    try:
        if not _user_exists(conn, user_id):
            return error_response(f"User with id {user_id} not found.", 404)

        cursor = conn.execute(
            "INSERT INTO weight_logs (user_id, weight_kg, date) VALUES (?, ?, ?)",
            (user_id, weight_kg, log_date.isoformat()),
        )
        # Keep the profile's current weight in sync with the latest log.
        conn.execute("UPDATE users SET weight_kg = ? WHERE id = ?", (weight_kg, user_id))
        conn.commit()

        row = conn.execute("SELECT * FROM weight_logs WHERE id = ?", (cursor.lastrowid,)).fetchone()
    finally:
        conn.close()

    return success_response(_log_to_dict(row), status_code=201)


@progress_bp.route("/api/users/<int:user_id>/progress", methods=["GET"])
def get_progress(user_id):
    """
    Return a user's weight history over time plus a simple summary
    (starting weight, current weight, and total change).
    """
    conn = get_connection()
    try:
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user_row:
            return error_response(f"User with id {user_id} not found.", 404)

        logs = conn.execute(
            "SELECT * FROM weight_logs WHERE user_id = ? ORDER BY date ASC, id ASC", (user_id,)
        ).fetchall()
    finally:
        conn.close()

    if not logs:
        return success_response(
            {
                "history": [],
                "summary": {
                    "starting_weight_kg": None,
                    "current_weight_kg": user_row["weight_kg"],
                    "change_kg": 0,
                    "entries_logged": 0,
                },
            }
        )

    starting_weight = logs[0]["weight_kg"]
    current_weight = logs[-1]["weight_kg"]

    return success_response(
        {
            "history": [_log_to_dict(log) for log in logs],
            "summary": {
                "starting_weight_kg": starting_weight,
                "current_weight_kg": current_weight,
                "change_kg": round(current_weight - starting_weight, 2),
                "entries_logged": len(logs),
            },
        }
    )
