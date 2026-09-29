from flask import Blueprint
from app.utils.responses import success_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """Simple endpoint to confirm the API is running."""
    return success_response({"status": "ok", "service": "AI FitTrack API"})
