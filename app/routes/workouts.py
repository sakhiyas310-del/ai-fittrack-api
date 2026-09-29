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

workouts_bp = Blueprint("workouts", __name__)


def _row_to_dict(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "exercise_name": row["exercise_name"],
        "duration_minutes": row["duration_minutes"],
        "date": row["date"],
        "notes": row["notes"],
        "created_at": row["created_at"],
    }


def _user_exists(conn, user_id):
    return conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone() is not None


@workouts_bp.route("/api/users/<int:user_id>/workouts", methods=["POST"])
def add_workout(user_id):
    """
    Log a new workout for a user.

    Example request body:
    {
        "exercise_name": "Running",
        "duration_minutes": 30,
        "date": "2026-09-27",
        "notes": "Felt strong, ran a new personal best pace."
    }
    """
    data = request.get_json(silent=True) or {}
    try:
        require_fields(data, ["exercise_name", "duration_minutes", "date"])
        exercise_name = validate_string(data["exercise_name"], "exercise_name", max_length=150)
        duration_minutes = validate_positive_number(data["duration_minutes"], "duration_minutes", allow_float=False)
        workout_date = validate_date(data["date"], "date")
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
            """
            INSERT INTO workouts (user_id, exercise_name, duration_minutes, date, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, exercise_name, duration_minutes, workout_date.isoformat(), notes),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM workouts WHERE id = ?", (cursor.lastrowid,)).fetchone()
    finally:
        conn.close()

    return success_response(_row_to_dict(row), status_code=201)


@workouts_bp.route("/api/users/<int:user_id>/workouts", methods=["GET"])
def get_workouts(user_id):
    """Fetch a user's full workout history, most recent first."""
    conn = get_connection()
    try:
        if not _user_exists(conn, user_id):
            return error_response(f"User with id {user_id} not found.", 404)

        rows = conn.execute(
            "SELECT * FROM workouts WHERE user_id = ? ORDER BY date DESC, id DESC", (user_id,)
        ).fetchall()
    finally:
        conn.close()

    return success_response([_row_to_dict(r) for r in rows])


@workouts_bp.route("/api/users/<int:user_id>/workouts/<int:item_id>", methods=["DELETE"])
def delete_workout(user_id, item_id):
    """Delete one workout entry that belongs to this user."""
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM workouts WHERE id = ? AND user_id = ?", (item_id, user_id))
        conn.commit()
        if cursor.rowcount == 0:
            return error_response(f"Workout {item_id} not found for user {user_id}.", 404)
    finally:
        conn.close()
    return success_response({"deleted_id": item_id})
