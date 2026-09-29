"""
AI FitTrack API
================
Application factory for the Flask app. This is where the app is created,
the database is initialized, and all the route groups (blueprints) are
registered.
"""

import os
import re

from flask import Flask, jsonify, request

from app.db import init_db
from app.utils.auth import read_token


def create_app():
    """
    Application factory.

    Using a factory function (instead of a global Flask app object) makes
    it easy to create fresh app instances -- handy for automated tests.
    """
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    # Make sure the database file and its tables exist before we handle any requests.
    init_db()

    if not os.environ.get("SECRET_KEY"):
        print("WARNING: SECRET_KEY is not set, so an insecure default is used. Set it before going online.")

    # ---- Register blueprints (route groups) ----
    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.workouts import workouts_bp
    from app.routes.meals import meals_bp
    from app.routes.progress import progress_bp
    from app.routes.workout_plan import workout_plan_bp
    from app.routes.water import water_bp
    from app.routes.meal_plan import meal_plan_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(workouts_bp)
    app.register_blueprint(meals_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(workout_plan_bp)
    app.register_blueprint(water_bp)
    app.register_blueprint(meal_plan_bp)

    # ---- Login check: every /api/users/<id>/... route needs the owner's token ----
    @app.before_request
    def require_login():
        match = re.match(r"^/api/users/(\d+)(/|$)", request.path)
        if not match:
            return None  # public: health, sign up, login, the web page
        header = request.headers.get("Authorization", "")
        token_user_id = read_token(header[7:]) if header.startswith("Bearer ") else None
        if token_user_id is None:
            return jsonify({"success": False, "error": "Login required. Send the header 'Authorization: Bearer <token>'."}), 401
        if token_user_id != int(match.group(1)):
            return jsonify({"success": False, "error": "You can only access your own data."}), 403

    # ---- Frontend: serve the web page at http://localhost:5000/ ----
    @app.route("/")
    def home():
        return app.send_static_file("index.html")

    # ---- Global error handlers (keep JSON responses consistent) ----
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Resource not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "error": "Method not allowed on this endpoint."}), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal server error."}), 500

    return app
