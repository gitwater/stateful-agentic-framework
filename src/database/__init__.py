"""
Database layer module using SQLAlchemy ORM and Alembic for migrations.
This module replaces the older SQL database implementation with a more robust,
scalable approach using a shared table design.
"""

from .core import Database 