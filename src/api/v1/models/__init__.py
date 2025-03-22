from src.api.v1.models.agent import (
    AgentMetadata,
    CreateAgentRequest,
    UpdateAgentRequest,
    AgentResponse,
    AgentDetailResponse,
    AgentListResponse,
)

from src.api.v1.models.session import (
    EngageAgentRequest,
    SessionResponse,
    MessageRequest,
    Message,
    MessagesResponse,
    StatusResponse,
)

# Common models for responses
from pydantic import BaseModel
from typing import Optional, Any

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    detail: Optional[str] = None 