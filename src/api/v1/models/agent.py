from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import uuid
import yaml

class AgentMetadata(BaseModel):
    """Agent metadata extracted from configuration"""
    name: str = "Unnamed Agent"
    description: str = ""
    purpose: str = ""

class CreateAgentRequest(BaseModel):
    """Request model for creating a new agent"""
    user_id: str
    config: str
    agent_id: Optional[str] = None
    
    @validator('agent_id', pre=True, always=True)
    def set_id(cls, v):
        """Set a UUID if agent_id is not provided"""
        return v or str(uuid.uuid4())
    
    @validator('config')
    def validate_yaml(cls, v):
        """Validate that the config is valid YAML and contains a name"""
        try:
            config = yaml.safe_load(v)
            if not config.get("name"):
                raise ValueError("Agent config must contain a name")
            return v
        except yaml.YAMLError:
            raise ValueError("Invalid YAML configuration")

class UpdateAgentRequest(BaseModel):
    """Request model for updating an existing agent"""
    user_id: str
    config: str
    
    @validator('config')
    def validate_yaml(cls, v):
        """Validate that the config is valid YAML and contains a name"""
        try:
            config = yaml.safe_load(v)
            if not config.get("name"):
                raise ValueError("Agent config must contain a name")
            return v
        except yaml.YAMLError:
            raise ValueError("Invalid YAML configuration")

class AgentResponse(BaseModel):
    """Response model for agent operations"""
    agent_id: str
    name: str
    description: Optional[str] = ""
    purpose: Optional[str] = ""

class AgentDetailResponse(AgentResponse):
    """Response model for detailed agent information"""
    user_id: str
    config: str

class AgentListResponse(BaseModel):
    """Response model for listing agents"""
    agents: List[AgentResponse] 