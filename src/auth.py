import datetime
import jwt
from sql_database.core import SQLDatabase
import os

# Configuration for JWT. Change these values as needed.
JWT_SECRET = os.environ.get("JWT_SECRET") or breakpoint()
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 3600  # Token validity: 1 hour

class Authentication:
    def __init__(self, persona_config):
        # Initialize the authentication database helper.
        self.sql = SQLDatabase("shared", "auth")

    def register(self, username, password):
        """
        Registers a new user.
        Returns True if registration succeeds, False if the user already exists.
        """
        return self.sql.db_auth.register_user(username, password)

    def login(self, username, password):
        """
        Verifies credentials. If successful, returns a JWT token.
        Otherwise, returns None.
        """
        user = self.sql.db_auth.verify_user(username, password)
        if user:
            payload = {
                "user_id": user["id"],
                "username": user["username"],
                "exp": datetime.datetime.now() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS)
            }
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
            # In some versions of PyJWT, token may be returned as bytes.
            if isinstance(token, bytes):
                token = token.decode("utf-8")
            return token
        return None

    def verify_token(self, token):
        """
        Verifies a JWT token.
        Returns the payload if valid, or None if the token is expired or invalid.
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    def get_next_client_id(self):
        """
        Returns a persistent next client ID.
        """
        # Assume SQLDatabase provides a SQLite-like connection.
        new_id = self.sql.db_auth.get_client_id()
        return new_id