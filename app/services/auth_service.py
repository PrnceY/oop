"""Registration and login logic (kept out of the web routes)."""
from werkzeug.security import check_password_hash, generate_password_hash

from app.exceptions import AuthError
from app.models.user import User

# Checked when the username doesn't exist, so login takes similar time either way.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


class AuthService:
    def __init__(self, users):
        self._users = users

    def register(self, username, password) -> User:
        user = User.register(username, password)
        return self._users.add(user)

    def login(self, username, password) -> User:
        user = self._users.get_by_username((username or "").strip())
        if user is None:
            check_password_hash(_DUMMY_HASH, password or "")
            raise AuthError("Invalid username or password.")
        if not user.check_password(password):
            raise AuthError("Invalid username or password.")
        return user
