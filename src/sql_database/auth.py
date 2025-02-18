import sqlite3
import os
import hashlib

class SQLDatabaseAuth:
    def __init__(self, conn):
        self.conn = conn

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def _hash_password(self, password, salt=None):
        """Hash a password with an optional salt. If salt is not provided, generate one."""
        if salt is None:
            salt = os.urandom(16).hex()
        hash_obj = hashlib.sha256()
        hash_obj.update((salt + password).encode('utf-8'))
        return hash_obj.hexdigest(), salt

    def register_user(self, username, password):
        """Register a new user. Returns True on success, False if the username already exists."""
        if self.get_user(username) is not None:
            return False  # User already exists.
        password_hash, salt = self._hash_password(password)
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, salt)
                VALUES (?, ?, ?)
            ''', (username, password_hash, salt))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user(self, username):
        """Retrieve a user row by username."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_row = cursor.fetchone()
        # Return user as a dictionary.
        if user_row:
            return {
                'id': user_row[0],
                'username': user_row[1],
                'password_hash': user_row[2],
                'salt': user_row[3],
                'created_at': user_row[4]
            }
        return None

    def verify_user(self, username, password):
        """
        Verify that the provided username and password are correct.
        Returns the user row if valid, otherwise None.
        """
        user = self.get_user(username)
        if user:
            stored_hash = user['password_hash']
            salt = user['salt']
            computed_hash, _ = self._hash_password(password, salt)
            if computed_hash == stored_hash:
                return user
        return None
