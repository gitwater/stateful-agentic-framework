from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.v1.models import (
    CreateAgentRequest,
    UpdateAgentRequest,
    AgentResponse,
    AgentDetailResponse,
    AgentListResponse,
)
from src.api.v1.utils import extract_agent_metadata, get_session_key
from typing import List, Dict, Any, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Define router
router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)

# Global variables for agent management (to be replaced with database)
agents_db = {}  # Placeholder for database

@router.post("/", response_model=AgentResponse)
async def create_agent(agent_data: CreateAgentRequest):
    """
    Create a new agent for a user.
    """
    # Extract metadata to verify the config
    metadata = extract_agent_metadata(agent_data.config)
    
    # Create agent entry (placeholder for database operation)
    agent_entry = {
        "agent_id": agent_data.agent_id,
        "user_id": agent_data.user_id,
        "config": agent_data.config,
        "name": metadata["name"],
        "description": metadata["description"],
        "purpose": metadata["purpose"],
    }
    
    # Store in our placeholder database
    key = f"{agent_data.user_id}:{agent_data.agent_id}"
    agents_db[key] = agent_entry
    
    # Return the created agent
    return {
        "agent_id": agent_data.agent_id,
        "name": metadata["name"],
        "description": metadata["description"],
        "purpose": metadata["purpose"],
    }

@router.get("/", response_model=AgentListResponse)
async def list_agents(user_id: str = Query(..., description="ID of the user whose agents to list")):
    """
    List all agents owned by a user.
    """
    # Filter agents by user_id (placeholder for database query)
    user_agents = []
    
    for key, agent in agents_db.items():
        if agent["user_id"] == user_id:
            user_agents.append({
                "agent_id": agent["agent_id"],
                "name": agent["name"],
                "description": agent["description"],
                "purpose": agent["purpose"],
            })
    
    return {"agents": user_agents}

@router.get("/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(
    agent_id: str,
    user_id: str = Query(..., description="ID of the user who owns the agent")
):
    """
    Get details of a specific agent.
    """
    # Lookup agent by ID (placeholder for database query)
    key = f"{user_id}:{agent_id}"
    agent = agents_db.get(key)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent_id": agent["agent_id"],
        "user_id": agent["user_id"],
        "name": agent["name"],
        "description": agent["description"],
        "purpose": agent["purpose"],
        "config": agent["config"],
    }

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: UpdateAgentRequest,
):
    """
    Update an existing agent's configuration.
    """
    # Check if the agent exists
    key = f"{agent_data.user_id}:{agent_id}"
    if key not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Extract metadata to verify the config
    metadata = extract_agent_metadata(agent_data.config)
    
    # Update agent entry (placeholder for database operation)
    agent = agents_db[key]
    agent["config"] = agent_data.config
    agent["name"] = metadata["name"]
    agent["description"] = metadata["description"]
    agent["purpose"] = metadata["purpose"]
    
    # If the agent is currently active in a session, tell it to refresh
    # (This would be handled by the session management system)
    
    return {
        "agent_id": agent_id,
        "name": metadata["name"],
        "description": metadata["description"],
        "purpose": metadata["purpose"],
    }

@router.delete("/{agent_id}", response_model=dict)
async def delete_agent(
    agent_id: str,
    user_id: str = Query(..., description="ID of the user who owns the agent")
):
    """
    Delete an agent.
    """
    # Check if the agent exists
    key = f"{user_id}:{agent_id}"
    if key not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Delete the agent (placeholder for database operation)
    del agents_db[key]
    
    # If the agent is currently in a session, end the session
    # (This would be handled by the session management system)
    
    return {"status": "agent deleted"} 