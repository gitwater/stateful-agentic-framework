"""
Long Term Memory (LTM) models for storing topic information.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel, UserAgentMixin

class Topic(BaseModel, UserAgentMixin):
    """
    Model for storing topic information in long-term memory.
    Each topic represents a conversation segment about a specific subject.
    """
    
    __tablename__ = 'ltm_topics'
    
    # User and Agent IDs
    user_id = Column(String(255), nullable=False)
    agent_id = Column(String(255), nullable=False)
    
    # Topic information
    topic = Column(String(255), nullable=False)
    topic_conversation_summary = Column(Text, nullable=False)
    start_utterance_id = Column(String(255), nullable=False)
    end_utterance_id = Column(String(255), nullable=False)
    
    def __repr__(self):
        return f"<Topic id={self.id} topic='{self.topic}' user_id='{self.user_id}' agent_id='{self.agent_id}'>" 