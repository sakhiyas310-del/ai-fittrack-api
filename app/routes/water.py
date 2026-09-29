"""Water-intake logging endpoints."""

from flask import Blueprint, request

from app.db import get_connection
from app.utils.responses import success_response, error_response
from app.utils.validation import (
    ValidationError,
    require_fields,
    validate_positive_number,
    validate_date,
    validate_string,
)

water_bp = Blueprint("water", __name__)


def _row_to_dict(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "amount_ml": row["amount_ml"],
        "date": row["date"],
        "notes": row["notes"],
        "created_at": row["created_at"],
    }


@water_bp.route("/api/users/<int:user_id>/water", methods=["POST"])
def add_water(user_id):
    """Record one water serving in millilitres."""
    data = request.get_json(silent=True) or {}
    try:
        require_fields(data, ["amount_ml", "date"])
        amount_ml = validate_positive_number(data["amount_ml"], "amount_ml", allow_float=False)
        log_date = validate_date(data["date"], "date")
        notes = data.get("notes")
        if notes is not None:
            notes = validate_string(notes, "notes", max_length=500)
    except ValidationError as e:
        return error_response(e.message, 400)

    conn = get_connection()
    try:
        user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            return error_response(f"User with id {user_id} not found.", 404)

        cursor = conn.execute(
            "INSERT INTO water_logs (user_id, amount_ml, date, notes) VALUES (?, ?, ?, ?)",
            (user_id, amount_ml, log_date.isoformat(), notes),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM water_logs WHERE id = ?", (cursor.lastrowid,)).fetchone()
    finally:
        conn.close()

    return success_response(_row_to_dict(row), status_code=201)


@water_bp.route("/api/users/<int:user_id>/water", methods=["GET"])
def get_water(user_id):
    """Return a user's water logs, newest first."""
    conn = get_connection()
    try:
        user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            return error_response(f"User with id {user_id} not found.", 404)
        rows = conn.execute(
            "SELECT * FROM water_logs WHERE user_id = ? ORDER BY date DESC, id DESC",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    return success_response([_row_to_dict(row) for row in rows])


@water_bp.route("/api/users/<int:user_id>/water/<int:item_id>", methods=["DELETE"])
def delete_water(user_id, item_id):
    """Delete one water log belonging to the signed-in user."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM water_logs WHERE id = ? AND user_id = ?", (item_id, user_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return error_response(f"Water entry {item_id} not found for user {user_id}.", 404)
    finally:
        conn.close()

    return success_response({"deleted_id": item_id})
