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
from src.database import Database
import uuid
from src.session_manager import restart_sessions_for_agent, remove_session, gen_session_key

# Set up logging
logger = logging.getLogger(__name__)
# Set logging level
logging.basicConfig(level=logging.INFO)

# Define router
router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)

# Get database instance
db = Database()

@router.post("/", response_model=AgentResponse)
async def create_agent(agent_data: CreateAgentRequest):
    """
    Create a new agent for a user.
    """
    # Log the request payload for debugging
    logger.info(f"Received create_agent request with payload: {agent_data.json()}")
    
    try:
        # Extract metadata to verify the config
        metadata = extract_agent_metadata(agent_data.config)

        # Generate a new UUID for the agent_id
        agent_id = str(uuid.uuid4())
        
        # Create agent in the database
        agent = db.agents.create_agent(
            user_id=agent_data.user_id,
            agent_id=agent_id,
            config=agent_data.config
        )
        
        # Return the created agent using the captured metadata and agent_id
        # This avoids accessing the agent object after the session might be closed
        return {
            "agent_id": agent_id,
            "name": metadata["name"],
            "description": metadata["description"],
            "purpose": metadata["purpose"],
        }
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Error creating agent: {str(e)}")

@router.get("/", response_model=AgentListResponse)
async def list_agents(user_id: str = Query(..., description="ID of the user whose agents to list")):
    """
    List all agents owned by a user.
    """
    try:
        # Get agents from database (now returns dictionaries, not Agent objects)
        agents_data = db.agents.list_agents(user_id)
        
        # Format response
        user_agents = []
        for agent_data in agents_data:
            # Get metadata from config
            metadata = extract_agent_metadata(agent_data["config"])
            
            user_agents.append({
                "agent_id": agent_data["agent_id"],
                "name": metadata["name"],
                "description": metadata["description"],
                "purpose": metadata["purpose"],
            })
        
        return {"agents": user_agents}
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing agents: {str(e)}")

@router.get("/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(
    agent_id: str,
    user_id: str = Query(..., description="ID of the user who owns the agent")
):
    """
    Get details of a specific agent.
    """
    try:
        # Get agent from database (now returns a dictionary, not an Agent object)
        agent_data = db.agents.get_agent(user_id, agent_id)
        
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Extract metadata from config
        metadata = extract_agent_metadata(agent_data["config"])
        
        return {
            "agent_id": agent_data["agent_id"],
            "user_id": agent_data["user_id"],
            "name": metadata["name"],
            "description": metadata["description"],
            "purpose": metadata["purpose"],
            "config": agent_data["config"],
        }
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Agent not found")
        # Log the error for debugging
        logger.error(f"Error retrieving agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving agent: {str(e)}")

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: UpdateAgentRequest,
):
    """
    Update an existing agent's configuration.
    """
    try:
        # Extract metadata to verify the config
        metadata = extract_agent_metadata(agent_data.config)
        
        # Update agent in database (now returns a dictionary, not an Agent object)
        updated_agent = db.agents.update_agent(
            user_id=agent_data.user_id,
            agent_id=agent_id,
            config=agent_data.config
        )
        
        if not updated_agent:
            raise HTTPException(status_code=404, detail="Agent not found")        
        
        # Restart all sessions for this agent
        restart_sessions_for_agent(agent_data.user_id, agent_id)
        logger.info(f"Restarted sessions for agent {agent_id} due to config update")
        
        return {
            "agent_id": agent_id,
            "name": metadata["name"],
            "description": metadata["description"],
            "purpose": metadata["purpose"],
        }
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Agent not found")
        # Log the error for debugging
        logger.error(f"Error updating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating agent: {str(e)}")

@router.delete("/{agent_id}", response_model=dict)
async def delete_agent(
    agent_id: str,
    user_id: str = Query(..., description="ID of the user who owns the agent")
):
    """
    Delete an agent.
    """
    # Delete agent from database
    success = db.agents.delete_agent(user_id, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent not found: {user_id}:{agent_id}")
    
    # Delete all user:agent id data from the databases
    success = db.stm.delete_utterances(user_id, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Failed to delete utterances: {user_id}:{agent_id}")

    success = db.states.delete_persona_states(user_id, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Failed to delete persona states: {user_id}:{agent_id}")

    success = db.ltm.delete_topics(user_id, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Failed to delete topics: {user_id}:{agent_id}")
    
    # Restart (effectively delete) all sessions for this agent
    session_key = gen_session_key(user_id, agent_id)
    remove_session(session_key)
    
    return {"status": "agent deleted"} 