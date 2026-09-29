from flask import Blueprint, request

from app.db import get_connection
from app.utils.responses import success_response, error_response
from app.utils.validation import ValidationError, require_fields, validate_string
from app.utils.meal_planner import generate_meal_plan

meal_plan_bp = Blueprint("meal_plan", __name__)


@meal_plan_bp.route("/api/users/<int:user_id>/meal-plan", methods=["POST"])
def create_meal_plan(user_id):
    data = request.get_json(silent=True) or {}
    try:
        require_fields(data, ["instructions"])
        instructions = validate_string(data["instructions"], "instructions", max_length=1000)
    except ValidationError as e:
        return error_response(e.message, 400)

    conn = get_connection()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()
    if user is None:
        return error_response(f"User with id {user_id} not found.", 404)

    plan, source = generate_meal_plan(user, instructions)
    return success_response({
        "user_id": user_id,
        "source": source,
        "is_ai_generated": source == "ai",
        "plan": plan,
    })
