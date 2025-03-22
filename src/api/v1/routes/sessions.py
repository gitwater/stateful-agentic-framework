from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from src.api.v1.models import (
    EngageAgentRequest,
    SessionResponse,
    MessageRequest,
    MessagesResponse,
    StatusResponse,
)
from src.api.v1.utils import get_session_key
from typing import Dict, Any, List
import logging
import queue
import os
import asyncio
import threading

# Set up logging
logger = logging.getLogger(__name__)

# Define router
router = APIRouter(
    prefix="/session",
    tags=["Sessions"],
)

# Global variables for session management
# In a production environment, this would be replaced with Redis
agent_sessions = {}  # Maps "{user_id}:{agent_id}" to SessionState objects

# Flag to determine if we're using Celery or local tasks
USE_CELERY = os.environ.get("USE_CELERY", "false").lower() == "true"

@router.post("/engage", response_model=SessionResponse)
async def engage_agent(
    agent_data: EngageAgentRequest,
    background_tasks: BackgroundTasks
):
    """
    Engage with an agent based on the provided configuration.
    """
    user_id = agent_data.user_id
    agent_id = agent_data.agent_id
    
    # Create the combined session key
    session_key = get_session_key(user_id, agent_id)
    
    # Check if this agent is already engaged by this user
    if session_key in agent_sessions:
        # Agent already engaged by this user, return the existing session key
        logger.info(f"Agent {agent_id} already engaged by user {user_id}, resuming session")
        # Send a refresh command to the session
        if USE_CELERY:
            from src.api.v1.tasks.celery_app import send_command
            send_command.delay(session_key, "refresh")
        else:
            agent_sessions[session_key]["command_queue"].put("refresh")
        return {"session_id": session_key}
    
    # If no config was provided, try to load it from the database
    # This is a placeholder - in a real implementation, we'd query the database
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
    
    # Set up session tracking
    agent_sessions[session_key] = {
        "status": "active",
    }
    
    # Start processing - either with Celery or locally
    if USE_CELERY:
        # Start a Celery task for this agent session
        from src.api.v1.tasks.celery_app import process_session
        task = process_session.delay(session_key, config, agent_data.username)
        agent_sessions[session_key]["task_id"] = task.id
    else:
        # For local development without Celery, use in-memory queues and a background thread
        agent_sessions[session_key].update({
            "user_messages": [],
            "agent_dialog_messages": [],
            "user_input_queue": queue.Queue(),
            "command_queue": queue.Queue(),
        })
        
        background_thread = threading.Thread(
            target=process_session_locally,
            args=(session_key, config, agent_data.username),
            daemon=True  # Allow the thread to be terminated when the main program exits
        )
        background_thread.start()
        agent_sessions[session_key]["thread"] = background_thread
    
    return {"session_id": session_key}

@router.get("/{session_key}/messages", response_model=MessagesResponse)
async def get_agent_messages(session_key: str):
    """
    Get active messages for a specific session.
    """
    session_state = agent_sessions.get(session_key)
    
    if not session_state:
        raise HTTPException(status_code=404, detail="No active session found")
    
    # Collect messages
    if USE_CELERY:
        # When using Celery, read messages from files
        from src.api.v1.tasks.celery_app import read_messages
        all_messages = read_messages(session_key)
    else:
        # When using local threads, get messages from in-memory dictionary
        # The user_messages and agent_dialog_messages are lists in the agent_sessions dict
        # that are populated by process_session_locally
        user_messages = session_state.get("user_messages", [])
        agent_dialog_messages = session_state.get("agent_dialog_messages", [])
        
        # Make a copy of the messages before clearing
        all_messages = user_messages.copy() + agent_dialog_messages.copy()
        
        # Clear the messages (they've been delivered)
        session_state["user_messages"] = []
        session_state["agent_dialog_messages"] = []
    
    return {"messages": all_messages}

@router.post("/{session_key}/send", response_model=StatusResponse)
async def send_message(session_key: str, message_data: MessageRequest):
    """
    Send a message to a specific session.
    """
    session_state = agent_sessions.get(session_key)
    
    if not session_state:
        raise HTTPException(status_code=404, detail="No active session found")
    
    # Queue the message for processing
    if USE_CELERY:
        # When using Celery, write message to file
        from src.api.v1.tasks.celery_app import send_input
        send_input.delay(session_key, message_data.message)
    else:
        # When using local threads, use in-memory queue
        session_state["user_input_queue"].put(message_data.message)
    
    return {"status": "queued"}

@router.delete("/{session_key}", response_model=StatusResponse)
async def end_agent_session(session_key: str):
    """
    End a session.
    """
    session_state = agent_sessions.pop(session_key, None)
    
    if not session_state:
        raise HTTPException(status_code=404, detail="No active session found")
    
    # Send termination command to the session
    if USE_CELERY:
        # When using Celery, write termination command to file
        from src.api.v1.tasks.celery_app import send_command
        send_command.delay(session_key, "terminate")
    else:
        # When using local threads, use in-memory queue
        session_state["command_queue"].put("terminate")
    
    # Clean up the config file
    config_path = os.path.join(os.getcwd(), 'tmp', 'configs', f"{session_key}.yaml")
    if os.path.exists(config_path):
        os.remove(config_path)
    
    return {"status": "agent session ended"}

# Helper function for background task processing in development
def process_session_locally(session_key, config, username):
    """
    Background task for development without Celery.
    """
    # Import session module
    try:
        from session import SessionState
        import time
        
        # Save config to a temporary file
        config_dir = os.path.join(os.getcwd(), 'tmp', 'configs')
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, f"{session_key}.yaml")
        
        with open(config_path, 'w') as f:
            f.write(config)
        
        # Create session state
        session_state = SessionState(session_key, config_path, False)
        session_state.init_session()
        
        logger.info(f"Local processing thread started for session {session_key}")
        
        # Process session in a loop
        # This is just for development testing - in production we'd use Celery
        while True:
            # Check for user input
            try:
                if session_key in agent_sessions:
                    user_input = agent_sessions[session_key]["user_input_queue"].get(block=False)
                else:
                    # Session has been deleted
                    break
            except queue.Empty:
                user_input = None
                
            # Process user input
            if user_input is not None:
                success = session_state.agent.interactions(user_input)
                if not success:
                    logger.error(f"Error processing input for agent {session_key}")
                agent_sessions[session_key]["user_input_queue"].task_done()
            
            # Check for commands
            try:
                if session_key in agent_sessions:
                    command = agent_sessions[session_key]["command_queue"].get(block=False)
                else:
                    # Session has been deleted
                    break
            except queue.Empty:
                command = None
                
            # Process commands
            if command is not None:
                if command == "refresh":
                    session_state.agent.refresh()
                elif command == "terminate":
                    logger.info(f"Terminating session {session_key}")
                    break
                agent_sessions[session_key]["command_queue"].task_done()
            
            # Sync messages
            if session_key in agent_sessions:
                # Retrieve messages from the SessionState object and store them in our shared dictionary
                new_user_messages = session_state.pop_user_messages()
                new_agent_dialog_messages = session_state.pop_agent_dialog_messages()
                
                # Append to existing messages rather than replacing
                if new_user_messages:
                    agent_sessions[session_key]["user_messages"].extend(new_user_messages)
                if new_agent_dialog_messages:
                    agent_sessions[session_key]["agent_dialog_messages"].extend(new_agent_dialog_messages)
                
                # Log if we found messages for debugging
                if new_user_messages or new_agent_dialog_messages:
                    logger.debug(f"Session {session_key}: Synced {len(new_user_messages)} user messages and {len(new_agent_dialog_messages)} dialog messages")
            
            # Don't max out CPU
            time.sleep(0.1)
            
        logger.info(f"Local processing thread ended for session {session_key}")
    except Exception as e:
        logger.error(f"Error in local processing thread for session {session_key}: {str(e)}") 