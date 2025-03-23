from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from src.api.v1.models import (
    EngageAgentRequest,
    SessionResponse,
    MessageRequest,
    MessagesResponse,
    StatusResponse,
)
from src.api.v1.utils import get_session_key
from typing import Dict, Any, List, Optional
import logging
import os
import asyncio
from src.session import SessionState

# Set up logging
logger = logging.getLogger(__name__)

# Define router
router = APIRouter(
    prefix="/session",
    tags=["Sessions"],
)

# Global variable for session management
# In a production environment, this would be replaced with a database or Redis
agent_sessions: Dict[str, Dict[str, Any]] = {}
# This is called whenever the client is first engaging or wants to resume a session
# and needs the current state of the conversaion, hud, and any other information
@router.post("/engage", response_model=SessionResponse)
async def engage_agent(agent_data: EngageAgentRequest):
    """
    Engage with an agent based on the provided configuration.
    Creates a new SessionState or returns an existing one.
    """
    user_id = agent_data.user_id
    agent_id = agent_data.agent_id
    
    # Create the combined session key
    session_key = get_session_key(user_id, agent_id)
    
    logger.info(f"Engage request received for session {session_key}")
    
    # Check if this agent is already engaged by this user
    if session_key in agent_sessions:
        logger.info(f"Agent {agent_id} already engaged by user {user_id}, resuming session")
        
        # Check if the session state exists
        if "session_state" in agent_sessions[session_key]:
            # Send a refresh command to the agent
            try:
                session_state = agent_sessions[session_key]["session_state"]
                session_state.agent.get_conversation_history()
                logger.info(f"Refresh completed for session {session_key}")
            except Exception as e:
                logger.error(f"Error during refresh for session {session_key}: {str(e)}")
        
        return {"session_id": session_key}
    
    # If we get here, we need to create a new session
    logger.info(f"Creating new session for {session_key}")
    
    try:
        # If no config was provided, try to load it from the database
        if not agent_data.config:
            # Check if agent exists in our placeholder database
            from src.api.v1.routes.agents import agents_db
            agent_key = f"{user_id}:{agent_id}"
            agent = agents_db.get(agent_key)
            
            if not agent:
                raise HTTPException(
                    status_code=404,
                    detail="Agent not found or has no configuration"
                )
            
            config = agent.get("config")
        else:
            config = agent_data.config
        
        # Save config to a temporary file
        config_dir = os.path.join(os.getcwd(), 'tmp', 'configs')
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, f"{session_key}.yaml")
        
        with open(config_path, 'w') as f:
            f.write(config)
        
        # Create and initialize session state
        session_state = SessionState(session_key, config_path, False)
        session_state.init_session()
        
        # Set up session tracking
        agent_sessions[session_key] = {
            "status": "active",
            "session_state": session_state,
            "user_messages": [],
            "agent_dialog_messages": []
        }
        
        # Start or resume the conversation
        await session_state.agent.interaction_get_starting_conversation() 
    
    except Exception as e:
        logger.error(f"Error creating session {session_key}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )
    
    return {"session_id": session_key}

@router.get("/{session_key}/messages", response_model=MessagesResponse)
async def get_agent_messages(session_key: str):
    """
    Get active messages for a specific session.
    """
    session_data = agent_sessions.get(session_key)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="No active session found")
    
    session_state = session_data.get("session_state")
    if not session_state:
        raise HTTPException(status_code=500, detail="Session state not found")
    
    # Collect messages from the SessionState
    user_messages = session_state.pop_user_messages()
    agent_dialog_messages = session_state.pop_agent_dialog_messages()
    
    # Add the new messages to the session cache
    session_data["user_messages"].extend(user_messages)
    session_data["agent_dialog_messages"].extend(agent_dialog_messages)
    
    # Combine all messages for response
    all_messages = user_messages + agent_dialog_messages
    
    return {"messages": all_messages}

@router.post("/{session_key}/send", response_model=StatusResponse)
async def send_message(session_key: str, message_data: MessageRequest):
    """
    Send a message to a specific session and process it asynchronously.
    """
    session_data = agent_sessions.get(session_key)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="No active session found")
    
    session_state = session_data.get("session_state")
    if not session_state:
        raise HTTPException(status_code=500, detail="Session state not found")
    
    # Process the message in a background thread to avoid blocking
    try:
        await session_state.agent.process_user_input(message_data.message)        
    except Exception as e:
        logger.error(f"Error sending message to session {session_key}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}"
        )
    
    return {"status": "processed"}

@router.delete("/{session_key}", response_model=StatusResponse)
async def end_agent_session(session_key: str):
    """
    End a session and clean up resources.
    """
    session_data = agent_sessions.pop(session_key, None)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="No active session found")
    
    # Clean up the config file
    config_path = os.path.join(os.getcwd(), 'tmp', 'configs', f"{session_key}.yaml")
    if os.path.exists(config_path):
        os.remove(config_path)
    
    return {"status": "agent session ended"} 