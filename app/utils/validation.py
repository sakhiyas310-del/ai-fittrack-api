"""
Small, dependency-free validation helpers.

Each function either returns a cleaned-up value or raises a ValidationError.
Routes catch ValidationError and turn it into a consistent JSON error
response, so we never have to repeat that error-formatting logic.
"""

import re
from datetime import datetime

VALID_FITNESS_GOALS = {"lose_weight", "build_muscle", "endurance", "general_fitness"}
VALID_EXPERIENCE_LEVELS = {"beginner", "intermediate", "advanced"}


class ValidationError(Exception):
    """Raised when incoming request data fails validation."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def require_fields(data, fields):
    """Ensure every field in `fields` is present and not None in `data`."""
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    missing = [f for f in fields if data.get(f) is None]
    if missing:
        raise ValidationError(f"Missing required field(s): {', '.join(missing)}.")


def validate_string(value, field_name, max_length=None):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"'{field_name}' must be a non-empty string.")
    if max_length and len(value) > max_length:
        raise ValidationError(f"'{field_name}' must be {max_length} characters or fewer.")
    return value.strip()


def validate_positive_number(value, field_name, allow_float=True):
    if isinstance(value, bool):  # bool is a subclass of int in Python -- exclude it explicitly
        raise ValidationError(f"'{field_name}' must be a number.")
    if not isinstance(value, (int, float)):
        raise ValidationError(f"'{field_name}' must be a number.")
    if not allow_float and not isinstance(value, int):
        raise ValidationError(f"'{field_name}' must be an integer.")
    if value <= 0:
        raise ValidationError(f"'{field_name}' must be greater than zero.")
    return value


def validate_choice(value, field_name, choices):
    if value not in choices:
        raise ValidationError(
            f"'{field_name}' must be one of: {', '.join(sorted(choices))}."
        )
    return value


def validate_date(value, field_name):
    """Accepts an ISO date string (YYYY-MM-DD) and returns a date object."""
    if not isinstance(value, str):
        raise ValidationError(f"'{field_name}' must be a date string in YYYY-MM-DD format.")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(f"'{field_name}' must be a valid date in YYYY-MM-DD format.")


def validate_email(value, field_name="email"):
    value = validate_string(value, field_name, max_length=254).lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
        raise ValidationError(f"'{field_name}' must be a valid email address.")
    return value


def validate_password(value, field_name="password"):
    if not isinstance(value, str) or not 6 <= len(value) <= 128:
        raise ValidationError(f"'{field_name}' must be between 6 and 128 characters long.")
    return value
