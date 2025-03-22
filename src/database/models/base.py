"""
Base models and mixins for all database models.
"""

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from ..core import Base
import datetime

# List to track all models
all_models = []

class UserAgentMixin:
    """
    Mixin that adds user_id and agent_id columns to a model.
    This ensures that all data is properly partitioned by user and agent.
    """
    
    @declared_attr
    def user_id(cls):
        return Column(String(255), nullable=False)
    
    @declared_attr
    def agent_id(cls):
        return Column(String(255), nullable=False)
    
    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Register the model in the all_models list when it's created."""
        super().__init_subclass__(**kwargs)
        all_models.append(cls)

class TimestampMixin:
    """Mixin that adds created_at and updated_at columns to a model."""
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class BaseModel(Base, TimestampMixin):
    """Base model class with common functionality."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    
    @classmethod
    def create(cls, session, **kwargs):
        """Create a new instance of the model."""
        instance = cls(**kwargs)
        session.add(instance)
        session.flush()
        return instance
    
    @classmethod
    def get(cls, session, id):
        """Get a model instance by ID."""
        return session.query(cls).get(id)
    
    @classmethod
    def get_all(cls, session, **kwargs):
        """Get all instances of the model that match the given kwargs."""
        return session.query(cls).filter_by(**kwargs).all()
    
    @classmethod
    def get_first(cls, session, **kwargs):
        """Get the first instance of the model that matches the given kwargs."""
        return session.query(cls).filter_by(**kwargs).first()
    
    def update(self, session, **kwargs):
        """Update the model instance with the given kwargs."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        session.flush()
        return self
    
    def delete(self, session):
        """Delete the model instance."""
        session.delete(self)
        session.flush() 