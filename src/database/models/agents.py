"""
Agent database model for storing agent configurations.
"""

from sqlalchemy import Column, String, Text
from .base import BaseModel, UserAgentMixin

class Agent(BaseModel):
    """
    Agent model for storing agent configurations and metadata.
    Each agent belongs to a user and has a unique id within that user's scope.
    """
    __tablename__ = 'agents'
    
    # UserAgentMixin provides user_id and agent_id fields
    user_id = Column(String(255), nullable=False, index=True)
    agent_id = Column(String(255), nullable=False, index=True)
    
    # Store the configuration as YAML
    config = Column(Text, nullable=False)
    
    __table_args__ = (
        # Ensure agent_id is unique within a user's scope
        {'sqlite_autoincrement': True},
    ) 