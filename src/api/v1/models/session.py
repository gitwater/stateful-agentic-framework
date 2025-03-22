from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class EngageAgentRequest(BaseModel):
    """Request model for engaging with an agent"""
    user_id: str
    agent_id: str
    username: Optional[str] = None
    config: Optional[str] = None

class SessionResponse(BaseModel):
    """Response model for session operations"""
    session_id: str

class MessageRequest(BaseModel):
    """Request model for sending a message to a session"""
    message: str

class Message(BaseModel):
    """Model for an individual message"""
    role: str
    response: str

class MessagesResponse(BaseModel):
    """Response model for retrieving messages"""
    messages: List[Message]

class StatusResponse(BaseModel):
    """Response model for status updates"""
    status: str 