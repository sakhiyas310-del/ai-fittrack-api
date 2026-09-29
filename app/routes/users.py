import sqlite3

from flask import Blueprint, request
from werkzeug.security import generate_password_hash

from app.db import get_connection
from app.utils.auth import make_token
from app.utils.responses import success_response, error_response
from app.utils.validation import (
    ValidationError,
    require_fields,
    validate_string,
    validate_positive_number,
    validate_choice,
    validate_email,
    validate_password,
    VALID_FITNESS_GOALS,
    VALID_EXPERIENCE_LEVELS,
)

users_bp = Blueprint("users", __name__)


def _row_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "age": row["age"],
        "height_cm": row["height_cm"],
        "weight_kg": row["weight_kg"],
        "fitness_goal": row["fitness_goal"],
        "experience_level": row["experience_level"],
        "workout_days_per_week": row["workout_days_per_week"],
        "created_at": row["created_at"],
    }


@users_bp.route("/api/users", methods=["POST"])
def create_user():
    """
    Sign up: create a new account and profile. Returns the user and a login token.

    Example request body:
    {
        "name": "Alex Rivera",
        "email": "alex@example.com",
        "password": "secret123",
        "age": 28,
        "height_cm": 175,
        "weight_kg": 72.5,
        "fitness_goal": "build_muscle",
        "experience_level": "beginner",
        "workout_days_per_week": 4
    }

    fitness_goal must be one of: lose_weight, build_muscle, endurance, general_fitness
    experience_level must be one of: beginner, intermediate, advanced
    """
    data = request.get_json(silent=True) or {}
    try:
        require_fields(
            data,
            ["name", "email", "password", "age", "height_cm", "weight_kg", "fitness_goal", "experience_level", "workout_days_per_week"],
        )
        name = validate_string(data["name"], "name", max_length=100)
        email = validate_email(data["email"])
        password = validate_password(data["password"])
        age = validate_positive_number(data["age"], "age", allow_float=False)
        height_cm = validate_positive_number(data["height_cm"], "height_cm")
        weight_kg = validate_positive_number(data["weight_kg"], "weight_kg")
        fitness_goal = validate_choice(data["fitness_goal"], "fitness_goal", VALID_FITNESS_GOALS)
        experience_level = validate_choice(data["experience_level"], "experience_level", VALID_EXPERIENCE_LEVELS)
        workout_days_per_week = validate_positive_number(
            data["workout_days_per_week"], "workout_days_per_week", allow_float=False
        )
        if workout_days_per_week > 7:
            raise ValidationError("'workout_days_per_week' cannot be greater than 7.")
    except ValidationError as e:
        return error_response(e.message, 400)

    conn = get_connection()
    try:
        try:
            cursor = conn.execute(
                """
                INSERT INTO users (name, email, password_hash, age, height_cm, weight_kg,
                                   fitness_goal, experience_level, workout_days_per_week)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, email, generate_password_hash(password), age, height_cm, weight_kg,
                 fitness_goal, experience_level, workout_days_per_week),
            )
        except sqlite3.IntegrityError:
            return error_response("An account with this email already exists.", 409)
        conn.commit()
        new_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM users WHERE id = ?", (new_id,)).fetchone()
    finally:
        conn.close()

    return success_response({"user": _row_to_dict(row), "token": make_token(new_id)}, status_code=201)


@users_bp.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """Fetch a single user's profile by ID."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()

    if not row:
        return error_response(f"User with id {user_id} not found.", 404)
    return success_response(_row_to_dict(row))
