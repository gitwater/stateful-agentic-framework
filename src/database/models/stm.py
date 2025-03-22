"""
Short Term Memory (STM) model for storing conversation history.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from .base import BaseModel, UserAgentMixin
import datetime

class Utterance(BaseModel, UserAgentMixin):
    """
    Model for storing conversation utterances.
    This matches the structure of the original 'utterances' table with added user_id and agent_id.
    """
    
    __tablename__ = 'stm_utterances'
    
    # User and Agent IDs
    user_id = Column(String(255), nullable=False)
    agent_id = Column(String(255), nullable=False)
    
    # Utterance content
    speaker = Column(String(50), nullable=False)  # Who spoke - user, assistant, system, etc.
    utterance = Column(Text, nullable=False)  # The content of the utterance
    created_at = Column(DateTime, default=datetime.datetime.now)
    
    def __repr__(self):
        return f"<Utterance id={self.id} speaker='{self.speaker}' user_id='{self.user_id}' agent_id='{self.agent_id}' created_at='{self.created_at}'>" 