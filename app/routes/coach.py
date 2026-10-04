from flask import Blueprint, request

from app.db import get_connection
from app.utils.coach import get_coach_reply
from app.utils.responses import error_response, success_response
from app.utils.validation import ValidationError, require_fields, validate_string

coach_bp = Blueprint("coach", __name__)


@coach_bp.route("/api/users/<int:user_id>/coach", methods=["POST"])
def ask_coach(user_id):
    data = request.get_json(silent=True) or {}
    try:
        require_fields(data, ["message"])
        message = validate_string(data["message"], "message", max_length=500)
    except ValidationError as error:
        return error_response(error.message, 400)

    raw_history = data.get("history", [])
    if not isinstance(raw_history, list):
        return error_response("Conversation history must be a list.", 400)
    history = []
    for entry in raw_history[-8:]:
        if not isinstance(entry, dict) or entry.get("role") not in ("user", "assistant"):
            continue
        content = entry.get("content")
        if isinstance(content, str) and content.strip():
            content = content.strip()[:500]
            if history and history[-1]["role"] == entry["role"]:
                history[-1]["content"] += "\n" + content
            else:
                history.append({"role": entry["role"], "content": content})
    if history and history[0]["role"] == "assistant":
        history = history[1:]
    if history and history[-1]["role"] == "user":
        history = history[:-1]

    conn = get_connection()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()
    if user is None:
        return error_response(f"User with id {user_id} not found.", 404)

    language = "ta" if data.get("language") == "ta" else "en"
    reply, source = get_coach_reply(user, message, history, language)
    return success_response({"reply": reply, "source": source})
