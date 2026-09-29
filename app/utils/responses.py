"""
Helpers that make sure every API response has the same shape:

Success:  {"success": true,  "data": ...}
Error:    {"success": false, "error": "..."}

Keeping this consistent across the whole API makes the frontend/client
code that consumes it much simpler and more predictable.
"""

from flask import jsonify


def success_response(data=None, status_code=200):
    body = {"success": True}
    if data is not None:
        body["data"] = data
    return jsonify(body), status_code


def error_response(message, status_code=400):
    return jsonify({"success": False, "error": message}), status_code
