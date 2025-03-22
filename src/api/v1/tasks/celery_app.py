from celery import Celery
import os
import logging
import json
import time
from typing import Dict, Any, List

# Set up logging
logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    'agentic_framework',
    # Using memory broker and file backend instead of Redis
    broker=os.environ.get('CELERY_BROKER_URL', 'memory://'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'file:///tmp/celery-results'),
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_concurrency=4,  # Adjust based on your machine's capabilities
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    task_acks_late=True,  # Acknowledge tasks after they are executed
)

# Ensure directories exist
def ensure_dirs():
    dirs = [
        os.path.join(os.getcwd(), 'tmp', 'configs'),
        os.path.join(os.getcwd(), 'tmp', 'messages'),
        os.path.join(os.getcwd(), 'tmp', 'commands'),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Message handling functions
def write_messages(session_key: str, messages: List[Dict[str, Any]]):
    """Write messages to a file for the API to pick up."""
    if not messages:
        return
    
    ensure_dirs()
    message_file = os.path.join(os.getcwd(), 'tmp', 'messages', f"{session_key}.json")
    
    try:
        # Read existing messages if file exists
        existing_messages = []
        if os.path.exists(message_file):
            with open(message_file, 'r') as f:
                try:
                    existing_messages = json.load(f)
                except json.JSONDecodeError:
                    existing_messages = []
        
        # Append new messages
        all_messages = existing_messages + messages
        
        # Write back to file
        with open(message_file, 'w') as f:
            json.dump(all_messages, f)
    except Exception as e:
        logger.error(f"Error writing messages for session {session_key}: {str(e)}")

def read_messages(session_key: str) -> List[Dict[str, Any]]:
    """Read and clear messages from file."""
    message_file = os.path.join(os.getcwd(), 'tmp', 'messages', f"{session_key}.json")
    
    if not os.path.exists(message_file):
        return []
    
    try:
        with open(message_file, 'r') as f:
            try:
                messages = json.load(f)
            except json.JSONDecodeError:
                messages = []
        
        # Clear the file
        with open(message_file, 'w') as f:
            json.dump([], f)
            
        return messages
    except Exception as e:
        logger.error(f"Error reading messages for session {session_key}: {str(e)}")
        return []

# Command handling functions
def write_command(session_key: str, command: str):
    """Write a command to a file for the worker to pick up."""
    ensure_dirs()
    command_file = os.path.join(os.getcwd(), 'tmp', 'commands', f"{session_key}.txt")
    
    try:
        with open(command_file, 'w') as f:
            f.write(command)
    except Exception as e:
        logger.error(f"Error writing command for session {session_key}: {str(e)}")

def read_command(session_key: str) -> str:
    """Read and clear command from file."""
    command_file = os.path.join(os.getcwd(), 'tmp', 'commands', f"{session_key}.txt")
    
    if not os.path.exists(command_file):
        return None
    
    try:
        with open(command_file, 'r') as f:
            command = f.read().strip()
        
        # Clear the file
        os.remove(command_file)
            
        return command
    except Exception as e:
        logger.error(f"Error reading command for session {session_key}: {str(e)}")
        return None

def write_input(session_key: str, user_input: str):
    """Write user input to a file for the worker to pick up."""
    ensure_dirs()
    input_file = os.path.join(os.getcwd(), 'tmp', 'commands', f"{session_key}_input.txt")
    
    try:
        with open(input_file, 'w') as f:
            f.write(user_input)
    except Exception as e:
        logger.error(f"Error writing user input for session {session_key}: {str(e)}")

def read_input(session_key: str) -> str:
    """Read and clear user input from file."""
    input_file = os.path.join(os.getcwd(), 'tmp', 'commands', f"{session_key}_input.txt")
    
    if not os.path.exists(input_file):
        return None
    
    try:
        with open(input_file, 'r') as f:
            user_input = f.read().strip()
        
        # Clear the file
        os.remove(input_file)
            
        return user_input
    except Exception as e:
        logger.error(f"Error reading user input for session {session_key}: {str(e)}")
        return None

# Define tasks here
@celery_app.task(bind=True, name='process_session')
def process_session(self, session_key, config_str=None, username=None):
    """
    Background task for processing an agent session.
    
    Args:
        session_key: The combined session key (user_id:agent_id)
        config_str: Optional agent configuration string
        username: Optional username
    """
    from session import SessionState
    import os
    
    logger.info(f"Starting background processing for session {session_key}")
    
    # Create session state
    if config_str:
        # Save config to a temporary file
        ensure_dirs()
        config_dir = os.path.join(os.getcwd(), 'tmp', 'configs')
        config_path = os.path.join(config_dir, f"{session_key}.yaml")
        
        with open(config_path, 'w') as f:
            f.write(config_str)
        
        session_state = SessionState(session_key, config_path, username, False)
    else:
        # Load config from existing file
        config_path = os.path.join(os.getcwd(), 'tmp', 'configs', f"{session_key}.yaml")
        session_state = SessionState(session_key, config_path, username, False)
    
    # Initialize session
    session_state.init_session()
    logger.info(f"Initialized session for agent {session_state.client_id}")
    
    # Main processing loop
    while True:
        # Check for user input from file
        user_input = read_input(session_key)
            
        # Process user input
        if user_input is not None:
            logger.info(f"Processing input for session {session_key}: {user_input}")
            success = session_state.agent.interactions(user_input)
            if not success:
                logger.error(f"Error processing input for agent {session_state.client_id}")
        
        # Check for commands from file
        command = read_command(session_key)
        
        # Process commands
        if command is not None:
            logger.info(f"Processing command for session {session_key}: {command}")
            if command == "refresh":
                session_state.agent.refresh()
            elif command == "terminate":
                logger.info(f"Terminating session {session_key}")
                break
        
        # Write messages to files for the API to pick up
        user_messages = session_state.pop_user_messages()
        agent_dialog_messages = session_state.pop_agent_dialog_messages()
        
        if user_messages:
            write_messages(session_key, user_messages)
        if agent_dialog_messages:
            write_messages(session_key, agent_dialog_messages)
        
        # Sleep to avoid maxing CPU
        time.sleep(0.1)
    
    logger.info(f"Process ended for session {session_key}")
    return {"status": "completed"}

@celery_app.task(name='send_command')
def send_command(session_key, command):
    """Send a command to a running session."""
    write_command(session_key, command)
    return {"status": "command_sent"}

@celery_app.task(name='send_input')
def send_input(session_key, user_input):
    """Send user input to a running session."""
    write_input(session_key, user_input)
    return {"status": "input_sent"} 