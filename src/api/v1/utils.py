import yaml
import logging
import os
from typing import Dict, Any, Tuple, Optional

# Set up logging
logger = logging.getLogger(__name__)

def extract_agent_metadata(config_yaml: str) -> Dict[str, str]:
    """
    Extracts metadata (name, description, purpose) from the agent config.
    
    Args:
        config_yaml: The YAML configuration string
        
    Returns:
        dict: Dictionary with name, description, and purpose fields
    """
    try:
        config = yaml.safe_load(config_yaml)
        return {
            "name": config['persona'].get("name", "Unnamed Agent"),
            "description": config['persona'].get("description", ""),
            "purpose": config['persona'].get("purpose", "")
        }
    except Exception as e:
        logger.error(f"Error parsing agent config: {e}")
        return {
            "name": "Unnamed Agent",
            "description": "",
            "purpose": ""
        }

def get_session_key(user_id: str, agent_id: str) -> str:
    """Helper function to create a combined session key"""
    return f"{user_id}:{agent_id}"

def parse_session_key(session_key: str) -> Tuple[Optional[str], Optional[str]]:
    """Helper function to parse user_id and agent_id from a session key"""
    parts = session_key.split(':', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, None 