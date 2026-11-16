"""User model.

Encapsulation: the password hash is private and only reachable through
check_password() / export_hash(); the plain password is never stored.
"""
import re

from werkzeug.security import check_password_hash, generate_password_hash

from app.exceptions import ValidationError

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")
MIN_PASSWORD_LENGTH = 8


class User:
    def __init__(self, username, password_hash, monthly_budget=0.0, user_id=None):
        self._id = user_id
        self._username = username
        self._password_hash = password_hash
        self._monthly_budget = 0.0
        self.monthly_budget = monthly_budget

    @classmethod
    def register(cls, username, password) -> "User":
        """Validate raw credentials and build a new user with a hashed password."""
        username = (username or "").strip()
        if not USERNAME_PATTERN.match(username):
            raise ValidationError("Username must be 3-30 characters: letters, numbers, underscore.")
        if not password or len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        return cls(username, generate_password_hash(password))

    @property
    def id(self):
        return self._id

    @property
    def username(self) -> str:
        return self._username

    @property
    def monthly_budget(self) -> float:
        return self._monthly_budget

    @monthly_budget.setter
    def monthly_budget(self, value):
        try:
            number = round(float(value), 2)
        except (TypeError, ValueError):
            raise ValidationError("Budget must be a number.")
        if number < 0 or number > 10_000_000:
            raise ValidationError("Budget must be between 0 and 10,000,000.")
        self._monthly_budget = number

    def check_password(self, password) -> bool:
        return check_password_hash(self._password_hash, password or "")

    def export_hash(self) -> str:
        """Only used by the repository when saving the user."""
        return self._password_hash
