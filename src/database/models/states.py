"""
State models for storing persona state information.
"""

from sqlalchemy import Column, Integer, String, Text, JSON
from .base import BaseModel, UserAgentMixin

class PersonaState(BaseModel, UserAgentMixin):
    """
    Model for storing persona state information.
    Each persona state is associated with a specific user and agent.
    """
    
    __tablename__ = 'persona_states'
    
    name = Column(String(255), nullable=False)
    state_data = Column(Text, nullable=False)  # JSON serialized data
    
    def __repr__(self):
        return f"<PersonaState id={self.id} name='{self.name}' user_id='{self.user_id}' agent_id='{self.agent_id}'>" 