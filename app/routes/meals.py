from flask import Blueprint, request

from app.db import get_connection
from app.utils.responses import success_response, error_response
from app.utils.validation import (
    ValidationError,
    require_fields,
    validate_string,
    validate_positive_number,
    validate_date,
)

meals_bp = Blueprint("meals", __name__)


def _row_to_dict(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "food_name": row["food_name"],
        "calories": row["calories"],
        "date": row["date"],
        "notes": row["notes"],
        "created_at": row["created_at"],
    }


def _user_exists(conn, user_id):
    return conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone() is not None


@meals_bp.route("/api/users/<int:user_id>/meals", methods=["POST"])
def add_meal(user_id):
    """
    Log a new meal for a user.

    Example request body:
    {
        "food_name": "Grilled chicken salad",
        "calories": 450,
        "date": "2026-09-27",
        "notes": "Lunch after workout"
    }
    """
    data = request.get_json(silent=True) or {}
    try:
        require_fields(data, ["food_name", "calories", "date"])
        food_name = validate_string(data["food_name"], "food_name", max_length=150)
        calories = validate_positive_number(data["calories"], "calories", allow_float=False)
        meal_date = validate_date(data["date"], "date")
        notes = data.get("notes")
        if notes is not None:
            notes = validate_string(notes, "notes", max_length=1000)
    except ValidationError as e:
        return error_response(e.message, 400)

    conn = get_connection()
    try:
        if not _user_exists(conn, user_id):
            return error_response(f"User with id {user_id} not found.", 404)

        cursor = conn.execute(
            "INSERT INTO meals (user_id, food_name, calories, date, notes) VALUES (?, ?, ?, ?, ?)",
            (user_id, food_name, calories, meal_date.isoformat(), notes),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM meals WHERE id = ?", (cursor.lastrowid,)).fetchone()
    finally:
        conn.close()

    return success_response(_row_to_dict(row), status_code=201)


@meals_bp.route("/api/users/<int:user_id>/meals", methods=["GET"])
def get_meals(user_id):
    """Fetch a user's full meal history, most recent first."""
    conn = get_connection()
    try:
        if not _user_exists(conn, user_id):
            return error_response(f"User with id {user_id} not found.", 404)

        rows = conn.execute(
            "SELECT * FROM meals WHERE user_id = ? ORDER BY date DESC, id DESC", (user_id,)
        ).fetchall()
    finally:
        conn.close()

    return success_response([_row_to_dict(r) for r in rows])


@meals_bp.route("/api/users/<int:user_id>/meals/<int:item_id>", methods=["DELETE"])
def delete_meal(user_id, item_id):
    """Delete one meal entry that belongs to this user."""
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM meals WHERE id = ? AND user_id = ?", (item_id, user_id))
        conn.commit()
        if cursor.rowcount == 0:
            return error_response(f"Meal {item_id} not found for user {user_id}.", 404)
    finally:
        conn.close()
    return success_response({"deleted_id": item_id})
