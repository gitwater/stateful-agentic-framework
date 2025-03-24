from typing import Dict, Any
import logging
from src.session import SessionState
import os

# Set up logging
logger = logging.getLogger(__name__)

# Global variable for session management
# In a production environment, this would be replaced with a database or Redis
agent_sessions: Dict[str, Dict[str, Any]] = {}

def gen_session_key(user_id: str, agent_id: str) -> str:
    """Generate a session key for a specific user/agent combo"""
    return f"{user_id}:{agent_id}"

def get_session(session_key: str) -> Dict[str, Any]:
    """Get session data for a specific session key"""
    return agent_sessions.get(session_key)

def add_session(session_key: str, session_data: Dict[str, Any]) -> None:
    """Add a new session to the sessions dictionary"""
    agent_sessions[session_key] = session_data

def remove_session(session_key: str) -> Dict[str, Any]:
    """Remove a session from the sessions dictionary"""
    return agent_sessions.pop(session_key, None)

def restart_sessions_for_agent(user_id: str, agent_id: str) -> None:
    """
    Restart all sessions for a specific agent by removing them from agent_sessions.
    The next time the client calls engage, a new session will be created.
    """
    keys_to_remove = []
    
    # Find all sessions for this user/agent combo
    for session_key in agent_sessions:
        if session_key.startswith(f"{user_id}:{agent_id}:"):
            keys_to_remove.append(session_key)
    
    # Remove the sessions
    for key in keys_to_remove:
        session_data = remove_session(key)
        logger.info(f"Removed session {key} due to agent config update")
        
        # Clean up the config file if it exists
        config_path = os.path.join(os.getcwd(), 'tmp', 'configs', f"{key}.yaml")
        if os.path.exists(config_path):
            os.remove(config_path)
            logger.info(f"Removed config file for session {key}") 